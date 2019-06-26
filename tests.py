import unittest
from reg import *
from reg import _


def for_all_compile(raw_case):
    def case(test_case_obj):
        for com in [compile0, compile1]:
            raw_case(test_case_obj, com)

    return case


class SmokeTestReg(unittest.TestCase):

    @for_all_compile
    def test1(self, compile):
        self.assertTrue(compile(_('a'))('a'))

    @for_all_compile
    def test2(self, compile):
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

    @for_all_compile
    def test3(self, compile):
        def complex_n(n):
            return c(*[h01(_('a')) for i in range(n)] + [_('a') for i in range(n)])

        self.assertTrue(
            compile(complex_n(10))('a' * 10)
        )

    @for_all_compile
    def test4(self, compile):
        a = _('a')

        self.assertTrue(
            compile(c(a, a, a, a))('aaaa')
        )

    @for_all_compile
    def test5(self, compile):
        a = _('a')
        b = _('b')

        r = compile(a | b)

        self.assertTrue(r('a'))
        self.assertTrue(r('b'))
        self.assertFalse(r('d'))


if __name__ == '__main__':
    unittest.main()
