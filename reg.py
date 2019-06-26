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


class Fragment(object):
    """A helper to compose state automata"""

    def starting_state(self):
        raise NotImplementedError

    def append(self, frag):
        raise NotImplementedError


class FragEnding(Fragment):
    def starting_state(self):
        return EndState()

    def append(self, frag):
        raise AppendEndingError


class FragChar(Fragment):
    def __init__(self, char):
        self.state = State(char=char)

    def starting_state(self):
        return self.state

    def append(self, frag):
        self.state.nxt = frag.starting_state()


class FragConcat(Fragment):
    def __init__(self, *frag_lst):
        assert frag_lst
        self.frag_lst = frag_lst

        for f1, f2 in zip(frag_lst[:-1], frag_lst[1:]):
            f1.append(f2)

    def starting_state(self):
        return self.frag_lst[0].starting_state()

    def append(self, frag):
        self.frag_lst[-1].append(frag)


class FragAlter(Fragment):
    def __init__(self, frag1, frag2):
        self.frag1 = frag1
        self.frag2 = frag2
        self.state = BranchState(nxt=frag1.starting_state(), alter=frag2.starting_state())

    def starting_state(self):
        return self.state

    def append(self, frag):
        self.frag1.append(frag.starting_state())
        self.frag2.append(frag.starting_state())


class Frag01(Fragment):
    def __init__(self, frag):
        self.frag = frag
        self.state = BranchState(nxt=frag.starting_state())

    def starting_state(self):
        return self.state

    def append(self, frag):
        self.frag.append(frag)
        self.state.alter = frag.starting_state()


class FragMany(Fragment):
    def __init__(self, frag):
        self.frag = frag
        self.state = BranchState(nxt=frag.starting_state())
        frag.append(self)

    def starting_state(self):
        return self.state

    def append(self, frag):
        self.state.alter = frag.starting_state()


class Frag1Many(Fragment):
    def __init__(self, frag):
        self.frag = frag
        self.state = BranchState(nxt=frag.starting_state())
        frag.append(self)

    def starting_state(self):
        return self.frag.starting_state()

    def append(self, frag):
        self.state.alter = frag.starting_state()


def compile0(frag):
    if isinstance(frag, RegularTreeNode):
        frag = frag.to_frag()

    frag.append(FragEnding())

    def match_from_state(string, state):
        # recursive implementation

        if state.ending and string:
            return False

        elif state.ending and not string:
            return True

        elif not state.ending and not string:
            return False

        if state.diverging:
            return match_from_state(string, state.nxt) or match_from_state(string, state.alter)

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

    frag.append(FragEnding())

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
                    tmp.add(stt.nxt)
                    tmp.add(stt.alter)

                # have forarded states divided
                tmp_non_div, tmp_div = divide(tmp)

                # merge ordinary states together
                non_div |= tmp_non_div

                # check diverging states
                div = tmp_div

                # repeat till there is no more diverging states

            return non_div

        states = {frag.starting_state()}

        for char in string:
            # ending state can't forward any more
            # just drop it
            states = {st for st in states if not st.ending}

            states = forward(states)
            states = {st.nxt for st in states if st.ordinary and st.char == char}
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
        return FragAlter(self.rt1, self.rt2)


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


_ = RTChar
s = RTString
c = RTConcat
h01 = RT01  # has 0 or 1
hm = RTMany  # has many
h1m = RT1Many  # has 1 or many
