class BaseNode(object):
    pass


class EndNode(BaseNode):
    ending = True


END_NODE = EndNode()


class Node(BaseNode):
    ending = False

    def __init__(self, char, next=None, alter=None):
        self.char = char
        self.next = next
        self.alter = alter


class Frag(object):
    def starting_node(self):
        raise NotImplementedError

    def append(self, frag):
        raise NotImplementedError

    def __add__(self, frag):
        return FragConcat(self, frag)

    def __or__(self, frag):
        return FragAlter(self, frag)


class FragEnding(Frag):
    def starting_node(self):
        return END_NODE

    def append(self, frag):
        raise ValueError


class FragChar(Frag):
    def __init__(self, char):
        self.node = Node(char=char)

    def starting_node(self):
        return self.node

    def append(self, frag):
        self.node.next = frag.starting_node()


class FragConcat(Frag):
    def __init__(self, *frag_lst):
        assert frag_lst
        self.frag_lst = frag_lst

        for f1, f2 in zip(frag_lst[:-1], frag_lst[1:]):
            f1.append(f2)

    def starting_node(self):
        return self.frag_lst[0].starting_node()

    def append(self, frag):
        self.frag_lst[-1].append(frag)


class FragAlter(Frag):
    def __init__(self, frag1, frag2):
        self.frag1 = frag1
        self.frag2 = frag2
        self.node = Node(char=None, next=frag1.starting_node(), alter=frag2.starting_node())

    def starting_node(self):
        return self.node

    def append(self, frag):
        self.frag1.append(frag.starting_node())
        self.frag2.append(frag.starting_node())


class Frag01(Frag):
    def __init__(self, frag):
        self.frag = frag
        self.node = Node(char=None, next=frag.starting_node())

    def starting_node(self):
        return self.node

    def append(self, frag):
        self.frag.append(frag)
        self.node.alter = frag.starting_node()


class FragMany(Frag):
    def __init__(self, frag):
        self.frag = frag
        self.node = Node(char=None, next=frag.starting_node())
        frag.append(self)

    def starting_node(self):
        return self.node

    def append(self, frag):
        self.node.alter = frag.starting_node()


class Frag1Many(Frag):
    def __init__(self, frag):
        self.frag = frag
        self.node = Node(char=None, next=frag.starting_node())
        frag.append(self)

    def starting_node(self):
        return self.frag.starting_node()

    def append(self, frag):
        self.node.alter = frag.starting_node()



def compile0(frag):

    frag.append(FragEnding())

    def match_from_node(string, node):
        # recursive implementation

        if node.ending and string:
            return False

        elif node.ending and not string:
            return True

        elif not node.ending and not string:
            return False

        if node.char is None:
            return match_from_node(string, node.next) or match_from_node(string, node.alter)

        elif node.char == string[0]:
            return match_from_node(string[1:], node.next)

        elif node.char != string[0]:
            return False

    def automata_match(string):
        return match_from_node(string, frag.starting_node())

    return automata_match


def compile1(frag):

    frag.append(FragEnding())

    def automata_match(string):
        # DFM implementation

        def forward(stts):
            """forward non-char states"""

            stts1 = set(stts)

            stts0 = {stt for stt in stts1 if stt.char is None}
            stts1 = stts1 - stts0

            while stts0:
                for stt in stts0:
                    stts1.add(stt.next)
                    stts1.add(stt.alter)

                stts0 = {stt for stt in stts1 if stt.char is None}
                stts1 = stts1 - stts0

            return stts1

        states = {frag.starting_node()}

        for char in string:
            states = forward(states - {END_NODE})
            states = {st.next for st in states if st != END_NODE and st.char == char}
            if not states:
                break

        return END_NODE in states

    return automata_match


compile = compile0

# syntax sugar


def frag_string(string):
    return FragConcat(*[FragChar(c) for c in string])


_ = FragChar
s = frag_string
c = FragConcat
h01 = Frag01  # has 0 or 1
hm = FragMany  # has many
h1m = Frag1Many  # has 1 or many


print(
    compile(_('a'))('a'),
    compile(
        c(
            h01(_('b')),
            h01(_('a')),
            _('b'),
            _('a')
            )
        )('ba')
)


def complex_n(n):
    return c(*[h01(_('a')) for i in range(n)] + [_('a') for i in range(n)])


print(
    compile(complex_n(20))('a' * 20)
)

