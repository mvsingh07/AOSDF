"""Channel rotation (C17): verbatim move of old rounds, newest kept, pointer added once, race guard."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import channel_rotate as cr  # noqa: E402


def rnd(n, status='ALIGNED'):
    return f'<!-- round:{n} checkpoint:assignment status:{status} opened:2026-11-26T00:00:00+00:00 wave:W scope:s -->\n\n## Round {n}\n\nbody {n}\n<!-- consumed:x round:{n} status:GREEN -->\n\n'


class RotateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = [patch.object(cr, 'CHANNEL_DIR', self.tmp),
                  patch.object(cr, '_create_history', self.fake_create)]
        for x in self.p:
            x.start()
        self.pre = '# Thread 1 ⇄ Architect\n\nintro\n\n'
        self.text = self.pre + ''.join(rnd(i) for i in range(1, 9))
        (self.tmp / 'thread1.md').write_text(self.text)

    def fake_create(self, thread, moved):
        (self.tmp / 'history').mkdir(exist_ok=True)
        (self.tmp / 'history' / f'thread{thread}.md').write_text('---\nid: x\n---\n# history\n\n' + moved)

    def tearDown(self):
        for x in reversed(self.p):
            x.stop()

    def test_moves_old_rounds_verbatim_and_keeps_newest(self):
        r = cr.rotate(1, keep=3, min_bytes=0, quiet=0, now=10**12)
        self.assertEqual((r['state'], r['moved_rounds'], r['kept_rounds']), ('rotated', 5, 3))
        chan = (self.tmp / 'thread1.md').read_text()
        hist = (self.tmp / 'history' / 'thread1.md').read_text()
        self.assertTrue(chan.startswith(self.pre + cr.pointer(1)))
        self.assertTrue(chan.endswith(''.join(rnd(i) for i in range(6, 9))))
        self.assertIn(''.join(rnd(i) for i in range(1, 6)), hist)
        # second rotation appends, pointer not duplicated
        with (self.tmp / 'thread1.md').open('a') as fh:
            fh.write(rnd(9) + rnd(10))
        r2 = cr.rotate(1, keep=3, min_bytes=0, quiet=0, now=10**12)
        self.assertEqual(r2['moved_rounds'], 2)
        chan = (self.tmp / 'thread1.md').read_text()
        self.assertEqual(chan.count('Older rounds'), 1)
        hist = (self.tmp / 'history' / 'thread1.md').read_text()
        for i in range(1, 8):
            self.assertEqual(hist.count(f'body {i}\n'), 1)
        self.assertEqual(cr.rotate(1, keep=3, min_bytes=0, quiet=0, now=10**12)['state'], 'few-rounds')

    def test_refuses_small_or_recent(self):
        self.assertEqual(cr.rotate(1, keep=3)['state'], 'small')
        self.assertEqual(cr.rotate(1, keep=3, min_bytes=0, quiet=3600)['state'], 'recently-written')
        self.assertEqual(cr.rotate(1, keep=3, min_bytes=0, quiet=0, dry_run=True, now=10**12)['state'], 'would-rotate')
        self.assertEqual((self.tmp / 'thread1.md').read_text(), self.text)


if __name__ == '__main__':
    unittest.main()
