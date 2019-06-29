import unittest
from reg import *
from reg import _, _any


def for_all_compile(raw_case):
    def case(test_case_obj):
        for com in [
            compile0,
            compile1
        ]:
            raw_case(test_case_obj, com)

    return case


class SmokeTestReg(unittest.TestCase):
    def _true(self, *lst):
        for e in lst:
            self.assertTrue(e)

    def _false(self, *lst):
        for e in lst:
            self.assertFalse(e)

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

    @for_all_compile
    def test6(self, compile):
        a = compile(s('abc'))

        self._true(
            a('abc')
        )

        self._false(
            a('a'),
            a('ab'),
            a('abcd'),
            a('abd')
        )

    @for_all_compile
    def test7(self, compile):
        a = s('abc')
        b = s('def')

        r = compile(hm(a | b))

        self._true(
            r(''),
            r('abc'),
            r('def'),
            r('abcabc'),
            r('defdef'),
            r('abcdef'),
            r('defabc'),
            r('abc' * 7),
            r('def' * 10),
            r('abcdef' * 30),
        )

        self._false(
            r('abc def'),
            r('acbdef'),
            r('abcde'),
            r('abdef'),
        )

    @for_all_compile
    def test8(self, compile):
        a = s('abc')
        b = s('def')

        r = compile(
            h1m((a + b) | (b + a))
        )

        self._true(
            r('abcdef'),
            r('defabc'),
            r('abcdef' * 2),
            r('defabc' * 2),
            r('abcdef' + 'defabc'),
            r('defabc' + 'abcdef'),
            r('abcdef' * 10),
            r('defabc' * 10),
        )

        self._false(
            r(''),
            r('abcde'),
            r('abcdefa'),
            r('defabd'),
            r('ddddddd'),
        )

    @for_all_compile
    def test9(self, compile):
        a = _any('a', 'b', 'c', 'd', 'e', 'f')
        r = compile(a)

        self._true(
            r('a'),
            r('b'),
            r('f')
        )

        self._false(
            r('g'),
            r('h'),
            r('kkk'),
            r('aa')
        )

    @for_all_compile
    def test10(self, compile):
        a = _('a')

        r = compile(rep(a, max=3))
        self._true(
            r(''),
            r('a'),
            r('aa'),
            r('aaa')
        )
        self._false(
            r('aaaa'),
            r('b'),
            r('bb'),
            r('bbb'),
            r('aaab')
        )

        r = compile(rep(a, min=3))
        self._true(
            r('aaa'),
            r('aaaa'),
            r('a' * 10),
            r('a' * 100)
        )
        self._false(
            r(''),
            r('a'),
            r('aa'),
            r('aab'),
            r('baa'),
            r('aaaab')
        )

        r = compile(rep(a, min=5, max=8))
        self._true(
            r('a' * 5),
            r('a' * 6),
            r('a' * 7),
            r('a' * 8)
        )
        self._false(
            r(''),
            r('a'),
            r('aa'),
            r('aaa'),
            r('aaaa'),
            r('aaaaaab')
        )

        r = compile(rep(a))
        self._true(
            r(''),
            r('a'),
            r('a' * 10),
            r('a' * 100)
        )
        self._false(
            r('b'),
            r('b' * 3),
            r(('a' * 10) + 'b'),
            r(('a' * 100) + 'b')
        )


if __name__ == '__main__':
    unittest.main()
