"""Regular Expression implementation"""


class RegError(Exception):
    pass


class AppendEndingError(RegError):
    """Can't append to a finished automata"""


class AutomataModifiedError(RegError):
    """Automata get modified during building"""


class BaseState(object):
    pass


class EndState(BaseState):
    ending = True
    diverging = False
    ordinary = False


class OrdinaryState(BaseState):
    ending = False
    diverging = False
    ordinary = True

    def __init__(self, char, nxt=None):
        assert char
        self.char = char
        self._nxt = None

        self.nxt = nxt

    @property
    def nxt(self):
        return self._nxt

    @nxt.setter
    def nxt(self, nxt):
        if self._nxt:
            raise AutomataModifiedError
        self._nxt = nxt


State = OrdinaryState


class BranchState(BaseState):
    ending = False
    diverging = True
    ordinary = False

    def __init__(self, nxt, alter=None):
        self._nxt = None
        self._alter = None

        self.nxt = nxt
        self.alter = alter

    @property
    def nxt_set(self):
        return {self.nxt, self.alter}

    @property
    def nxt(self):
        return self._nxt

    @nxt.setter
    def nxt(self, nxt):
        if self._nxt:
            raise AutomataModifiedError
        self._nxt = nxt

    @property
    def alter(self):
        return self._alter

    @alter.setter
    def alter(self, alter):
        if self._alter:
            raise AutomataModifiedError
        self._alter = alter


class MultiBranchState(BaseState):
    ending = False
    diverging = True
    ordinary = False

    def __init__(self, nxt_set):
        self.nxt_set = set(nxt_set)


class Fragment(object):
    """A helper to compose state automata"""

    def starting_state(self):
        raise NotImplementedError

    def append(self, state):
        raise NotImplementedError


def append(frag, frag_or_state):
    if isinstance(frag_or_state, BaseState):
        frag.append(frag_or_state)
    elif isinstance(frag_or_state, Fragment):
        frag.append(frag_or_state.starting_state())
    else:
        raise TypeError


class FragEnding(Fragment):
    def __init__(self):
        self.state = EndState()

    def starting_state(self):
        return self.state

    def append(self, state):
        raise AppendEndingError


class FragChar(Fragment):
    def __init__(self, char):
        self.state = State(char=char)

    def starting_state(self):
        return self.state

    def append(self, state):
        self.state.nxt = state


class FragConcat(Fragment):
    def __init__(self, *frag_lst):
        assert frag_lst
        self.frag_lst = frag_lst

        for f1, f2 in zip(frag_lst[:-1], frag_lst[1:]):
            append(f1, f2)

    def starting_state(self):
        return self.frag_lst[0].starting_state()

    def append(self, state):
        append(self.frag_lst[-1], state)


class FragAlter(Fragment):
    def __init__(self, frag1, frag2):
        self.frag1 = frag1
        self.frag2 = frag2
        self.state = BranchState(nxt=frag1.starting_state(), alter=frag2.starting_state())

    def starting_state(self):
        return self.state

    def append(self, state):
        append(self.frag1, state)
        append(self.frag2, state)


class Frag01(Fragment):
    def __init__(self, frag):
        self.frag = frag
        self.state = BranchState(nxt=frag.starting_state())

    def starting_state(self):
        return self.state

    def append(self, state):
        append(self.frag, state)
        self.state.alter = state


class FragMany(Fragment):
    def __init__(self, frag):
        self.frag = frag
        self.state = BranchState(nxt=frag.starting_state())
        append(frag, self)

    def starting_state(self):
        return self.state

    def append(self, state):
        self.state.alter = state


class Frag1Many(Fragment):
    def __init__(self, frag):
        self.frag = frag
        self.state = BranchState(nxt=frag.starting_state())
        append(frag, self.state)

    def starting_state(self):
        return self.frag.starting_state()

    def append(self, state):
        self.state.alter = state


class FragChoices(Fragment):
    def __init__(self, choice_lst):
        nxt_set = {State(char=e) for e in choice_lst}
        self.state = MultiBranchState(nxt_set)

    def starting_state(self):
        return self.state

    def append(self, state):
        for s in self.state.nxt_set:
            s.nxt = state


def compile0(frag):
    if isinstance(frag, RegularTreeNode):
        frag = frag.to_frag()

    append(frag, FragEnding())

    def match_from_state(string, state):
        # recursive implementation

        if state.diverging:
            for nxt in state.nxt_set:
                r = match_from_state(string, nxt)
                if r:
                    return r
            return False

        if state.ending and string:
            return False

        elif state.ending and not string:
            return True

        elif not state.ending and not string:
            return False

        elif state.char == string[0]:
            return match_from_state(string[1:], state.nxt)

        elif state.char != string[0]:
            return False

    def automata_match(string):
        return match_from_state(string, frag.starting_state())

    return automata_match


def compile1(frag):
    if isinstance(frag, RegularTreeNode):
        frag = frag.to_frag()

    append(frag, FragEnding())

    def automata_match(string):
        # DFM implementation

        def divide(stts):
            """divide states into non-diverging states and diverging states"""
            return ({st for st in stts if not st.diverging},
                    {st for st in stts if st.diverging})

        def forward(stts):
            """forward all diverging states till there's no diverging states"""

            # divide them into non-diverging states (non_div) and diverging states (div)
            non_div, div = divide(stts)

            # when there is any diverging state
            while div:

                # forward diverging states
                tmp = set()
                for stt in div:
                    tmp |= stt.nxt_set

                # have forarded states divided
                tmp_non_div, tmp_div = divide(tmp)

                # merge ordinary states together
                non_div |= tmp_non_div

                # check diverging states
                div = tmp_div

                # repeat till there is no more diverging states

            return non_div

        states = forward({frag.starting_state()})

        for char in string:
            states = {st for st in states if not st.ending}
            states = {st.nxt for st in states if st.ordinary and st.char == char}
            states = forward(states)

            if not states:
                break

        return any(st.ending for st in states)

    return automata_match


compile = compile0


# Regular Tree -- A readable and reusable regular expression counterpart


class RegularTreeNode(object):
    def to_frag(self):
        raise NotImplementedError

    def __add__(self, other):
        return RTConcat(self, other)

    def __or__(self, other):
        return RTAlter(self, other)


class RTChar(RegularTreeNode):
    def __init__(self, char):
        self.char = char

    def to_frag(self):
        return FragChar(char=self.char)


class RTString(RegularTreeNode):
    def __init__(self, string):
        self.string = string

    def to_frag(self):
        return FragConcat(*[FragChar(x) for x in self.string])


class RTConcat(RegularTreeNode):
    def __init__(self, *rt_lst):
        self.rt_lst = rt_lst

    def to_frag(self):
        return FragConcat(*[rt.to_frag() for rt in self.rt_lst])


class RTAlter(RegularTreeNode):
    def __init__(self, rt1, rt2):
        self.rt1 = rt1
        self.rt2 = rt2

    def to_frag(self):
        return FragAlter(self.rt1.to_frag(), self.rt2.to_frag())


class RT01(RegularTreeNode):
    def __init__(self, rt):
        self.rt = rt

    def to_frag(self):
        return Frag01(self.rt.to_frag())


class RTMany(RegularTreeNode):
    def __init__(self, rt):
        self.rt = rt

    def to_frag(self):
        return FragMany(self.rt.to_frag())


class RT1Many(RegularTreeNode):
    def __init__(self, rt):
        self.rt = rt

    def to_frag(self):
        return Frag1Many(self.rt.to_frag())


class RTChoices(RegularTreeNode):
    def __init__(self, *char_lst):
        self.char_lst = char_lst

    def to_frag(self):
        return FragChoices(self.char_lst)


class RTCounted(RegularTreeNode):
    def __init__(self, rt, min=0, max=None):
        self.rt = rt
        assert min >= 0
        assert max is None or (isinstance(max, int) and max > min)
        self.min = min
        self.max = max

    def to_frag(self):

        # frag list whose amount are certain
        frag_lst_1 = []
        for i in range(self.min):
            frag_lst_1.append(self.rt)

        # frag list whose amount are not certain
        frag_lst_2 = []

        # has max, just append with several "rt?"
        if self.max:
            for i in range(self.max - self.min):
                frag_lst_2.append(RT01(self.rt))

        # no max, append with one "rt*"
        else:
            frag_lst_2.append(RTMany(self.rt))

        return RTConcat(*frag_lst_1 + frag_lst_2).to_frag()


_ = RTChar
s = RTString
c = RTConcat
h01 = RT01  # has 0 or 1
hm = RTMany  # has many
h1m = RT1Many  # has 1 or many
_any = RTChoices
rep = RTCounted  # repeat with count
