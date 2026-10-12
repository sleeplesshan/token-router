import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('source_guard', Path(__file__).resolve().parents[1] / 'scripts/source_guard.py')
g = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g)


class SourceGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'source.txt'
        self.path.write_text('alpha\nbeta\n')

    def test_read_probe_lines(self):
        guard = g.SourceGuard(self.path)
        self.assertEqual(guard.read(), 'alpha\nbeta\n')
        self.assertEqual(guard.probe(3), 'alp')
        self.assertEqual(list(guard.lines()), ['alpha\n', 'beta\n'])
        with self.assertRaises(ValueError):
            guard.probe(-1)

    def test_same_size_mutation_even_restored_mtime(self):
        guard = g.SourceGuard(self.path)
        initial = self.path.stat()
        self.path.write_text('ALPHA\nBETA\n')
        os.utime(self.path, ns=(initial.st_atime_ns, initial.st_mtime_ns))
        with self.assertRaises(g.SourceChangedError):
            guard.read()

    def test_replacement_same_size(self):
        guard = g.SourceGuard(self.path)
        other = self.path.with_name('other')
        other.write_text(self.path.read_text())
        os.replace(other, self.path)
        with self.assertRaises(g.SourceChangedError):
            guard.probe(1)

    def test_open_descriptor_mutation_detected_after_read(self):
        guard = g.SourceGuard(self.path)
        with self.assertRaises(g.SourceChangedError):
            with guard.open() as handle:
                self.assertEqual(handle.readline(), 'alpha\n')
                self.path.write_text('alpha\nBETA\n')

    def test_rotation_while_descriptor_still_open(self):
        guard = g.SourceGuard(self.path)
        if os.name == 'nt':
            with guard.open():
                with self.assertRaises(PermissionError):
                    self.path.rename(self.path.with_name('old'))
            self.path.rename(self.path.with_name('old'))
            self.path.write_text('alpha\nbeta\n')
            with self.assertRaises(g.SourceChangedError):
                guard.read()
            return
        with self.assertRaises(g.SourceChangedError):
            with guard.open():
                self.path.rename(self.path.with_name('old'))
                self.path.write_text('alpha\nbeta\n')

    def test_symlink_retarget_detected(self):
        link = self.path.with_name('link')
        link.symlink_to(self.path)
        guard = g.SourceGuard(link)
        other = self.path.with_name('other')
        other.write_text('alpha\nbeta\n')
        link.unlink()
        link.symlink_to(other)
        with self.assertRaises(g.SourceChangedError):
            guard.read()

    def test_removed_source_and_closed_early_iterator(self):
        guard = g.SourceGuard(self.path)
        iterator = guard.lines()
        self.assertEqual(next(iterator), 'alpha\n')
        if os.name == 'nt':
            with self.assertRaises(PermissionError):
                self.path.unlink()
            iterator.close()
            self.path.unlink()
            with self.assertRaises(g.SourceChangedError):
                guard.read()
        else:
            self.path.unlink()
            with self.assertRaises(g.SourceChangedError):
                iterator.close()

    def test_decode_replacement_and_empty_file(self):
        self.path.write_bytes(b'\xff\n')
        self.assertEqual(g.SourceGuard(self.path).read(), '\ufffd\n')
        self.path.write_bytes(b'')
        self.assertEqual(g.SourceGuard(self.path).read(), '')


if __name__ == '__main__':
    unittest.main()
