"""Durable, bounded benchmark process capture; never part of the skill payload."""
from __future__ import annotations
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import threading
import time

from run_workflow_bench import usage_from_events

try:
    import resource
except ImportError:  # Local CPU is unavailable on Windows.
    resource = None


def _cpu():
    if resource is None:
        return None
    u = resource.getrusage(resource.RUSAGE_CHILDREN)
    return u.ru_utime + u.ru_stime


def capture(cmd, directory, *, prompt='', cwd=None, env=None,
            idle_timeout=240, absolute_timeout=360, grace=20,
            max_bytes=2_000_000):
    """Stream immediately; silence and absolute deadlines are distinct.

    Final usage is authoritative only after the latest started turn completes.
    Incomplete cumulative counters are lower bounds, never a zero-cost failure.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    before = _cpu()
    options = {'start_new_session': True} if os.name == 'posix' else {
        'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, **options)
    events = queue.Queue()
    def drain(name, pipe):
        try:
            while True:
                chunk = pipe.read1(65536)
                if not chunk:
                    break
                events.put((name, chunk))
        finally:
            events.put((name, None))
            pipe.close()
    workers = [threading.Thread(target=drain, args=(name, pipe), daemon=True)
               for name, pipe in [('stdout', p.stdout), ('stderr', p.stderr)]]
    for worker in workers:
        worker.start()
    def send_input():
        try:
            p.stdin.write(prompt.encode('utf-8'))
        except (BrokenPipeError, OSError):
            pass  # Exit status/events determine whether input was processed.
        finally:
            try:
                p.stdin.close()
            except OSError:
                pass
    sender=threading.Thread(target=send_input,daemon=True)
    sender.start()
    activity = start
    interrupted = None
    reason = None
    forced = False
    truncated = False
    closed = set()
    chunks = {'stdout': bytearray(), 'stderr': bytearray()}
    paths = {'stdout': directory/'events.jsonl', 'stderr': directory/'stderr.txt'}
    streams = {name: path.open('wb') for name, path in paths.items()}
    def terminate(force=False):
        if os.name == 'posix':
            try:
                os.killpg(p.pid, signal.SIGKILL if force else signal.SIGINT)
            except ProcessLookupError:
                pass
        elif force:
            p.kill()
        else:
            try:
                p.send_signal(signal.CTRL_BREAK_EVENT)
            except OSError:
                p.terminate()
    try:
        while len(closed) < 2 or p.poll() is None:
            now = time.monotonic()
            if reason is None:
                if now-start >= absolute_timeout:
                    reason = 'absolute_timeout'
                elif now-activity >= idle_timeout:
                    reason = 'idle_timeout'
                if reason is not None:
                    interrupted = now
                    terminate()
            elif not forced and now-interrupted >= grace:
                terminate(force=True)
                forced = True
            try:
                name, chunk = events.get(timeout=.05)
            except queue.Empty:
                continue
            if chunk is None:
                closed.add(name)
                continue
            if name == 'stdout':
                activity = time.monotonic()
            if sum(map(len, chunks.values()))+len(chunk) > max_bytes:
                truncated=True
                if reason is None:
                    reason = 'capture_limit'
                    interrupted = time.monotonic()
                    terminate()
            # Bound capture during shutdown too; an incomplete log blocks release.
            room=max(0,max_bytes-sum(map(len,chunks.values())))
            kept=chunk[:room]
            chunks[name].extend(kept)
            streams[name].write(kept)
            streams[name].flush()
        p.wait()
    finally:
        if p.poll() is None:
            terminate(force=True)
            p.wait()
        for stream in streams.values():
            stream.close()
        for worker in workers:
            worker.join(timeout=1)
        sender.join(timeout=1)
    elapsed = time.monotonic()-start
    after = _cpu()
    stdout = chunks['stdout'].decode('utf-8', errors='replace')
    try:
        known = usage_from_events(stdout, allow_tools=True)
    except ValueError:
        known = None
    parsed = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                parsed.append(event)
        except ValueError:
            pass
    last_start = max((i for i,e in enumerate(parsed) if e.get('type')=='turn.started'), default=-1)
    complete = not truncated and known is not None and any(e.get('type')=='turn.completed' for e in parsed[last_start+1:])
    cpu = None if before is None else after-before
    return dict(returncode=p.returncode, termination_reason=reason,
        forced_kill=forced, capture_truncated=truncated, wall=elapsed, cpu=cpu,
        remote_wait_proxy=None if cpu is None else max(0, elapsed-cpu),
        usage=known if complete else None, known_usage_lower_bound=known,
        usage_complete=complete, events=parsed,
        timeout=reason in ('idle_timeout','absolute_timeout'))


def retry_admissible(attempts, max_attempts=2):
    """No retry after an unbilled failure or a completed successful process."""
    if not attempts or len(attempts) >= max_attempts:
        return False
    last = attempts[-1]
    return last['usage_complete'] and (last['returncode'] != 0 or last['termination_reason'] is not None)


def aggregate(attempts):
    complete = bool(attempts) and all(a['usage_complete'] for a in attempts)
    known = {key: sum((a.get('known_usage_lower_bound') or {}).get(key,0) for a in attempts)
             for key in ('input_tokens','output_tokens','cached_input_tokens','reasoning_output_tokens')}
    return dict(usage_complete=complete,
        total_tokens=known['input_tokens']+known['output_tokens'] if complete else None,
        known_lower_bound=known['input_tokens']+known['output_tokens'], usage=known,
        wall=sum(a['wall'] for a in attempts), attempts=len(attempts))
