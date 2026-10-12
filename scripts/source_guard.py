"""Detect source replacement/mutation across reads; this is not an atomic snapshot."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO
import os


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
        self.baseline = self._identity(self.path.stat())
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
        try:
            handle = self.path.open('r', encoding='utf-8', errors='replace')
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
            return handle.read()

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
            for line in handle:
                yield line
