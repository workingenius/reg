import unittest
from reg import *
from reg import _


class SmokeTestReg(unittest.TestCase):
    def test1(self):
        self.assertTrue(compile(_('a'))('a'))

    def test2(self):
        self.assertTrue(
            compile(
                c(
                    h01(_('b')),
                    h01(_('a')),
                    _('b'),
                    _('a')
                )
            )('ba')
        )

    def test3(self):
        def complex_n(n):
            return c(*[h01(_('a')) for i in range(n)] + [_('a') for i in range(n)])

        self.assertTrue(
            compile(complex_n(20))('a' * 20)
        )


if __name__ == '__main__':
    unittest.main()
