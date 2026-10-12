"""Detect source replacement/mutation across reads; this is not an atomic snapshot."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO
import os
import stat

MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_SOURCE_LINES = 250_000
MAX_LINE_CHARS = 1_000_000


class SourceLimitError(ValueError):
    """Input exceeds bounded local processing limits; nothing was fully scanned."""



class SourceChanged(OSError):
    """The source no longer matches the metadata captured for this operation."""


SourceChangedError = SourceChanged


class SourceGuard:
    """Guard repeated UTF-8 reads using path and open-descriptor identities.

    Metadata checks detect ordinary mutations and rotations, including same-size
    writes. They do not prevent concurrent writes or adversarial metadata changes.
    Symlink identity is also checked so retargeting a link is detected.
    """

    def __init__(self, path: str | Path):
        # Keep the lexical path: resolving it would hide later symlink rotation.
        self.path = Path(path).absolute()
        info = self.path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Source must be a regular file (FIFO/devices unsupported)")
        self.baseline = self._identity(info)
        self.stamp = self.baseline
        self.open_count = 0
        self.link_baseline = self._identity(self.path.lstat())
        self.check()

    @staticmethod
    def _identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns

    def check(self) -> None:
        try:
            matches = (self._identity(self.path.stat()) == self.baseline
                       and self._identity(self.path.lstat()) == self.link_baseline)
        except OSError as exc:
            raise SourceChangedError('source_changed: source unavailable during guarded read') from exc
        if not matches:
            raise SourceChangedError('source_changed: source metadata changed during guarded read')

    @contextmanager
    def open(self) -> Iterator[TextIO]:
        """Check the path and descriptor before use and again before completion."""
        self.check()
        if self.baseline[2] > MAX_SOURCE_BYTES:
            raise SourceLimitError('source exceeds 64 MiB; split it into bounded regular files')
        try:
            fd = os.open(self.path, os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0))
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise SourceChangedError('source_changed: descriptor is not a regular file')
                handle = os.fdopen(fd, 'r', encoding='utf-8', errors='replace')
            except BaseException:
                os.close(fd)
                raise
            self.open_count += 1
        except OSError as exc:
            raise SourceChangedError('source_changed: source could not be reopened') from exc
        try:
            if self._identity(os.fstat(handle.fileno())) != self.baseline:
                raise SourceChangedError('source_changed: opened descriptor differs from source')
            self.check()
            try:
                yield handle
            finally:
                if self._identity(os.fstat(handle.fileno())) != self.baseline:
                    raise SourceChangedError('source_changed: opened source changed during read')
                self.check()
        finally:
            handle.close()

    def read_text(self) -> str:
        with self.open() as handle:
            text = handle.read(MAX_SOURCE_BYTES + 1)
            if len(text) > MAX_SOURCE_BYTES:
                raise SourceLimitError('decoded source exceeds read limit')
            return text

    def read(self) -> str:
        return self.read_text()

    def probe(self, max_chars: int) -> str:
        """Read at most max_chars characters, checking even truncated probes."""
        if max_chars < 0:
            raise ValueError('max_chars must be nonnegative')
        with self.open() as handle:
            return handle.read(max_chars)

    def lines(self) -> Iterator[str]:
        """Yield lines; callers stopping early must close the iterator."""
        with self.open() as handle:
            for count in range(MAX_SOURCE_LINES + 1):
                line = handle.readline(MAX_LINE_CHARS + 1)
                if not line:
                    return
                if count == MAX_SOURCE_LINES or len(line) > MAX_LINE_CHARS:
                    raise SourceLimitError('source exceeds 250000 lines or 1000000 decoded characters per line')
                yield line
