#! /usr/bin/env python3
#  meta.py  21/09/2019  D.J.Whale
#
# An interpreter for the META-II virtual machine

import sys
import traceback


#----- CONFIG ------------------------------------------------------------------

ERR_SYNTAX_ERROR = "Syntax error"
QUOTE            = "'\""
WHITESPACE       = " \t\r\n"

# Set to True to get a trace of executed VM instructions.
DEBUG = False

def debug(*args):
    s = ""
    for a in args:
        s += str(a)
    sys.stderr.write(s)
    sys.stderr.write("\n")


#------ ERROR HANDLING ---------------------------------------------------------

def fail(context=""):
    """Raise a fatal error and stop"""
    print()

    # if no linenos, don't try to print them
    try:
        lineref = ",lineno=%d" % ip_to_lineno[ip]
    except:
        lineref = ""
    sys.stderr.write("failed(ip=%d%s):%s\n"% (ip, lineref, context))

    print_py_stack(traceback.extract_stack())
    print_m2_stack()
    exit(1)

def print_py_stack(s):
    sys.stderr.write("pystack:")
    for si in s[1:-1]:
        sys.stderr.write("%s(%s) " % (si.name, str(si.lineno)))

    sys.stderr.write("\n")


#----- VM PROGRAM LOADER -------------------------------------------------------

# The full program to execute. A list of instructions
instrs = []  # list of tuple (operand, optional-address)

label_to_ip = {}  # map label->ip, for efficient jumps

ip_to_lineno = {}  # map ip->lineno, for error message use

def add_instr(token, lineno):
    ip = len(instrs)  # ip of next instr
    if isinstance(token, str):
        # LABEL
        token = token.strip()
        if len(token) != 0:
            label_to_ip[token] = ip
    else:
        # INSTR
        instrs.append(token)
        ip_to_lineno[ip] = lineno

def parse_line(line):
    """Parse a line of <label> | <spc>+ instr <spc>+ [addr]"""
    # All parts are space separated
    # But if see a single quote, must read until next single quote.
    # returns None if nothing (blank line, comment etc).
    # Returns a string if it is a valid label line.
    # Returns a tuple of (instr, addr) if it is an instruction line.

    # Empty lines produce nothing
    if len(line) == 0: return None

    # A line starting with a non space, is always a label,
    if line[0] != ' ':
        # LABEL
        # ... but it must not have any spaces on the line.
        if ' ' in line:
            fail("parse_line:spaces are not allowed on label lines")
            return None
        line = line.strip()  # strip nl
        return line  # a string is a label instr

    # It must be an instruction line.
    line = line.strip()  # strip leading ws and trailing ws/nl

    # Everything up to first ws is instruction,
    # optional rest is address. Address might have spaces in it if quoted.
    if not ' ' in line:
        # instr
        return (line, )
    else:
        # instr addr
        ws = line.index(" ")
        instr = line[:ws]
        addr = line[ws+1:].strip()
        return (instr, addr)

def load_instrs(filename):
    with open(filename) as file:
        lineno = 1
        for l in file.readlines():
            #debug("parse_line:", l)
            instr = parse_line(l)
            ##debug("  gives instr:%s" % str(instr))
            if instr is not None:
                add_instr(instr, lineno)
            lineno += 1

def dump_instrs():
    ip = 0
    for i in instrs:
        debug("%d:%s" % (ip, i))
        ip += 1

    for l in label_to_ip:
        ip = label_to_ip[l]
        debug("%s->%d:%s" % (l, ip, instrs[ip]))


#----- VM PROGRAM EXECUTOR -----------------------------------------------------

# current index into instrs[]
ip = 0

def fetch():
    """Get instr at ip, advance ip to next"""
    global ip
    instr = instrs[ip]
    ip += 1
    return instr

def jump(*, label=None, addr=None):
    """Find the ip of a given label and jump to it"""
    global ip, finished

    ##debug("jump: (%s, %s)" % (str(label), str(addr)))

    if label is not None:
        ##debug("  to label %s" % label)
        try:
            addr = label_to_ip[label]
        except KeyError:
            fail("jump:missing label:%s" % label)

    ##debug("jump to:%s" % str(addr))
    ip = addr

#----- INPUT READER ------------------------------------------------------------

file = None
cache = ""
lookahead = 0
saved = ""

def nextline():
    """Read next line from input stream and append to cache"""
    global cache
    if cache is None:
        fail("nextline:end of file")

    line = file.readline()
    if line != "":
        cache += line
        return line[0]
    else:
        cache = None

def peek():
    """read currently pointed to char (including current lookahead)"""
    if cache is None:
        fail("peek:end of file")
    if lookahead >= len(cache):
        ##debug("peek: nextline")
        ch = nextline()
    else:
        ch = cache[lookahead]
        ##debug("peek: ch='%s' (%d)" % (ch, len(ch)))
    return ch

def advance(n=1):
    """Advance lookahead ptr by n"""
    global lookahead
    assert lookahead <= len(cache)
    lookahead += n

def discard():
    """Discard any lookahead by resetting lookahead=0"""
    global lookahead
    lookahead = 0

def save(n=None):
    """Delete n {default lookahead amount) chars from input stream"""
    global cache, lookahead, saved
    if cache is None:
        return
    if n is None: n = lookahead
    assert n <= lookahead
    saved = cache[:n]
    cache = cache[n:]
    lookahead -= n

def recall():
    """Read the last string saved with save()"""
    return saved

def skipws():
    """skip and consume ws on input until we get to next non ws"""
    # if current char, on entry, is not whitespace, do nothing
    # so that we could interleave this and not damage ongoing save/recall
    ch = peek()
    if not ch in WHITESPACE: return ch

    while True:
        ch = peek()
        if ch not in WHITESPACE:
            save()
            return ch
        advance()


#----- LEXER -------------------------------------------------------------------

def id():
    """Try for an identifier"""
    ##debug("{TRY ID}")
    # After deleting initial blanks in the input string,
    skipws()

    # test if it begins with an identifier,
    # i.e. a letter followed by a sequence of letters and/or digits.
    #NOTE, first must be letter
    #NOTE: must be at least 1 char long
    # If not,
    # reset switch.
    ch = peek()
    if not (ch.isalpha() or ch == '_'):
        discard()
        return False

    #NOTE, non first can be letter or digit
    #NOTE: terminate on non letter/digit
    while True:
        advance()
        ch = peek()
        if not (ch.isalnum() or ch == "_"): break

    # If so,
    # delete the identifier and set switch.
    ##debug("<<< match id '%s'" % str(cache))
    save()
    return True

def number():
    """Try to read a number"""
    # After deleting initial blanks in the input string,
    ##debug("{TRY NUMBER}")
    skipws()

    # test if it begins with a number,
    # NOTE: must start with a digit
    # If not,
    # reset switch.
    ch = peek()
    if not ch.isdigit():
        discard()
        return False

    advance()

    # i.e. a string of digits which may contain embedded periods,
    # but may not begin or end with a period.
    # Moreover, no two periods may be next to one an other.
    # NOTE: must end with a digit
    # NOTE: non digit/period will terminate
    # NOTE: if just seen a period, seeing a second period will be a no-match
    prev_was_dot = False
    while True:
        ch = peek()
        if ch == '.':
            if prev_was_dot:
                discard()
                return False
            prev_was_dot = True
        else:
            if not ch.isdigit():
                # If a number is found,
                # delete it and set switch.
                save()
                return True
            prev_was_dot = False
        advance()

def dot_string():
    """Try to read a quoted string"""
    # After deleting initial blanks in the input string,
    ##debug("{TRY QUOTED}")
    skipws()

    # test if it begins with a string,
    # i.e. a single quote
    ch = peek()
    if ch not in QUOTE:
        # If not,
        # reset switch.
        discard()
        return False

    advance()
    quote = ch  # the open quote we found

    # followed by a sequence of any characters other than a single quote.
    # NOTE: any non quote char following will be part of string
    # including WS
    # NOTE: next quote will be end of string
    while True:
        ch = peek()
        if ch == quote:  # close quote must match open quote
            # If a string is found,
            # delete it and set switch.
            advance()
            save()
            return True
        advance() # include this character

def is_literal(s):
    """Try to read a specific literal"""
    ##debug("{TRY LITERAL '%s'}" % s)

    # NOTE, will erroneously match shorter prefixes,
    # so '&' and '&&' will match '&'.
    # This is just a limitation of the meta-II approach.
    skipws()

    # compare it to the string given as argument.
    la = 0
    ls = len(s)
    while la != ls:
        ch = peek()
        ##debug("literal %s   %s == %s" % (s, ch, s[la]))
        if ch != s[la]: # no match
            # If not met,
            # reset switch
            ##debug("  <<<literal '%s' did not match input:'%s'"% (str(s), str(cache)))
            discard()
            return False
        la += 1
        advance()

    # If the comparison is met,
    # delete the matched portion from the input
    ##debug("  <<< literal matched '%s'" % str(cache))
    save()
    # and set switch.
    return True


#----- LABEL SEQUENCE GENERATOR ------------------------------------------------

labels = []

def nextlabel(index=1):
    """Allocate the next label for a given sequence"""
    while index > len(labels):
        labels.append(None)
    index -= 1 # 1.. => A..

    if labels[index] is None:
        labels[index] = 1
    else:
        labels[index] += 1

    return format("%c%02d" % (chr(ord('A') + index), labels[index]))

def gen(index=1):
    """Generate or read current sequence for a given index"""
    v = rd_local(index)
    if v is None:
        v = nextlabel(index)
        wr_local(index, v)
    return v

def gen1():
    """Generate label 1"""
    # This concerns the current label 1 cell.
    # i.e. the next to top cell in the stack,
    # which is either clear or contains a generated label.
    # If clear, generate a label and put it into that cell.
    # Whether the label has just been put into the cell or was already there,
    # output it.
    # finally, insert a blank character in the output following the label.
    dot_out(gen(1))

def gen2():
    """Generate label 2"""
    # This concerns the current label 2 cell.
    # i.e. the top cell in the stack,
    # which is either clear or contains a generated label.
    # If clear, generate a label and put it into that cell.
    # Whether the label has just been put into the cell or was already there,
    # output it.
    # finally, insert a blank character in the output following the label.
    dot_out(gen(2))


#----- STACK -------------------------------------------------------------------

stack = []

def _call(retaddr=None):
    """Push a new stack frame with retaddr in cell 0 of it"""
    ##debug("call, will return to addr:%s" % str(retaddr))
    stack.append([retaddr])

def _ret(): # -> ip index
    """Pop top stack frame and return address in cell 0 of it"""
    if len(stack) == 0:
        ##debug("ret, stack empty, finished")
        return None
    else:
        r = stack.pop()
        ##debug("ret, retaddr=%s" % r)
        return r

def _top():
    """Get the top stack frame (retaddr, locals...)"""
    return stack[len(stack)-1]

def rd_local(index=1):
    """Read the value of a given local variable index"""
    t = _top() # len 1 when no locals
    # locals numbered from 1
    while index >= len(t):
        t.append(None)
    return t[index]

def wr_local(index=1, value="NONE"):
    """Write a new value to a given local variable index"""
    t = _top() # len 1 when no locals
    # locals numbered from 1
    while index >= len(t):
        t.append(None)
    t[index] = value

def print_m2_stack():
    debug("m2stack:")
    for item in stack:
        item = item[0] # retaddr
        try:
            debug(item, instrs[item]) # the thing we called
        except:
            debug("?")

#----- BRANCH ------------------------------------------------------------------

def branch(label):
    """Branch unconditionally to the address of a given label"""
    jump(label=label)

def call(label):
    """Call subroutine at address dictated by a label"""
    # Enter the subroutine beginning in location AAA.
    # If the top two terms of the stack are blank,
    # push the stack down by one cell.
    # Otherwise, push it down by three cells.
    # Set a flag in the stack to indicate whether it has been pushed
    # by one or three cells.
    # This flag and the exit address go into the third cell.
    # Clear the top two cells to blanks
    # to indicate that they can accept addresses
    # which may be generated in the subroutine.
    ra = ip
    ##debug("call %s" % label)
    _call(ra) # return address
    jump(label=label)

def ret():
    """Return from called routine"""
    global finished
    # Return to the exit address,
    # popping up the stack by one or three cells according to the flag.
    # If the stack is popped by only one cell
    # then clear the top two cells to blanks
    # because they were blank when the subroutine was entered.
    ra = _ret()
    ##debug("ret to %s" % str(ra))
    if ra is None:
        finished = True
    else:
        jump(addr=ra[0])

def brancht(flag, label):
    """Branch if true, to address dictated by a label"""
    # Branch to location AAA if switch is on.
    # Otherwise, continue in sequence.
    if flag:
        jump(label=label)

def branchf(flag, label):
    """Branch if false, to address dictated by a label"""
    # Branch to locatio AAA if switch os off.
    # Otherwise, continue in sequence.
    if not flag:
        jump(label=label)

def branche(flag):
    """Branch if error, to error routine"""
    # Halt if switch is off.
    # Otherwise, continue in sequence.
    if flag:
        fail("branche:BE instruction executed")


#----- EMITTER -----------------------------------------------------------------

def blank_line():
    """Factory to generate a new blank line"""
    return ['', '']

F_LABEL      = 0
F_PROG       = 1
field_idx    = F_PROG
current_line = blank_line()

def to_label():
    """Next dot_out() will be to the label column"""
    global field_idx
    assert field_idx != F_LABEL, "to_label: already in label field"
    field_idx = F_LABEL

def to_prog():
    """Next dot_out() will be to the prog column"""
    global field_idx
    field_idx = F_PROG

def dot_out(s):
    """Write string to output"""
    global field_idx
    if field_idx == F_LABEL:
        current_line[field_idx] = s
        to_prog()
    else:
        current_line[field_idx] += s

def wr_saved():
    """Output the last sequence of characters saved from the input string"""
    dot_out(saved)

def out():
    """Output current line and move to next output line"""
    global field_idx, current_line

    if len(current_line[0]) != 0:
        # A label line
        print(current_line[0])
        assert len(current_line[1]) == 0, "out: label and instr on same line? %s" % str(current_line)
    else:
        # An instruction line
        print(" "*8, current_line[1].strip())
    current_line = blank_line()
    to_prog()


#----- VIRTUAL MACHINE INSTRUCTION INTERPRETER ---------------------------------

switch = False
finished = False

def addarg(fn):
    """function decorator where an argument is expected"""
    if not hasattr(fn, "nargs"):
        fn.nargs = 1
    else:
        fn.nargs += 1
    return fn

class M2Instruction():
    @staticmethod
    def exec(line):
        ##debug("exec:%s" % str(line))
        if isinstance(line, str):
            instr = line
        elif isinstance(line, tuple):
            instr = line[0]
        else:
            assert False, "exec: what is this:%s" % line

        try:
            fn = getattr(M2Instruction, instr)

            if callable(fn):
                if not hasattr(fn, "nargs"):
                    ##debug("  exec:%s" % fn)
                    fn()
                else:
                    nargs = getattr(fn, "nargs")
                    assert nargs == 1
                    ##debug("  exec:%s(%s)" % (fn, line[1]))
                    fn(line[1])
            else:
                fail("exec:Unknown instr:%s" % instr)

        except AttributeError as e:
            fail("exec:Unknown instr:%s" % instr)

    @staticmethod
    @addarg
    def TST(string):
        """TEST - Try for a specific literal"""
        # After deleting initial blanks in the input string,
        # compare it to the string given as argument.
        # If the comparision is met, delete the matched portion from the input
        # and set the switch.
        # If not met, reset switch.
        global switch
        string = string[1:-1] # strip quotes
        switch = is_literal(string)

    @staticmethod
    def ID():
        """IDENTIFIER - Try for an identifier"""
        # After deleting initial blanks in the input string,
        # test if it begins with an identifier.
        # i.e. A letter followed by a sequence of letters and/or digits.
        # If so delete the identifier and set the switch.
        # If not, reset switch.
        global switch
        switch = id()

    @staticmethod
    def NUM():
        """NUMBER - Try for a number"""
        # After deleting initial blanks in the input string,
        # test if it begins with a number.
        # A number is a string of digits which may contain embedded periods,
        # but may not begin or end with a period.
        # No two periods may be next to one another.
        # If a numbet is found, delete it and set switch.
        # If not, reset switch.
        global switch
        switch = number()

    @staticmethod
    def SR():
        """STRING - Try for a quoted string"""
        # After deleting initial blanks in the input string,
        # test if it begins with a string.
        # i.e. a single quote followed by a sequence of any characters other
        # than a single quote, followed by another single quote.
        # If a string is found, delete it and set the switch.
        # If not, reset switch.
        global switch
        switch = dot_string()

    @staticmethod
    @addarg
    def CLL(aaa):
        """CALL - Call Subroutine"""
        # Enter the subroutine beginning in location aaa.
        # If the top two terms of the stack are blank,
        # push the stack down by one cell.
        # Otherwise, push it down by three cells.
        # Set a flag in the stack to indicate where it has been pushed by
        # one or three cells.
        # This flag and the exit address go into the third cell.
        # Clear the top two cells to blanks to indicate that they can accepted
        # addresses which may be generated within the subroutine.
        call(aaa)

    @staticmethod
    def R():
        """RETURN - Return to caller"""
        # Return to the exit address, popping up the stack by one or three cells
        # according to the flag.
        # If the stack is popped by only one cell, then clear the top two cells
        # to blanks, because they were blank when the subroutine was entered.
        ret()

    @staticmethod
    def SET():
        """SET - Set switch"""
        # Set branch switch ON.
        global switch
        switch = True

    @staticmethod
    @addarg
    def B(aaa):
        """BRANCH - Branch unconditional"""
        # Branch unconditionally to location aaa.
        branch(aaa)

    @staticmethod
    @addarg
    def BT(aaa):
        """BRANCH IF TRUE - Branch if true"""
        # Branch to location aaa if switch is ON.
        # Otherwise, continue in sequence.
        brancht(switch, aaa)

    @staticmethod
    @addarg
    def BF(aaa):
        """BRANCH IF FALSE - Branch if false"""
        # Branch to location aaa if switch is OFF.
        # Otherwise, continue in sequence.
        branchf(switch, aaa)

    @staticmethod
    def BE():
        """BRANCH TO ERROR IF FALSE - Branch if false to error handler"""
        # Halt if swithch is OFF.
        # Otherwise, continue in sequence.
        if not switch:
            dump_instrs()
            fail("BE:branch to error executed")

    @staticmethod
    @addarg
    def CL(string):
        """COPY LITERAL - Copy literal"""
        # Output the variable length string given as the argument.
        # A blank character will be inserted in the output following the string.
        string = string[1:-1]  # strip quotes
        dot_out(string + " ")

    @staticmethod
    def CI():
        """COPY INPUT - Copy saved input to output"""
        # Output the last sequence of characters deleted from the input string.
        # This command may not function properly if the laste command which
        # could cause deletion failed to do so.
        wr_saved()

    @staticmethod
    def GN1():
        """GENERATE 1 - Generate label 1"""
        # This concerns the current label 1 cell.
        # i.e. The next to top cell in the stack, which is either clear
        # or contains a generated label.
        # If clear, generate a label and put it into that cell.
        # Whether the label has just been put into the cell or was already
        # there, output it.
        # Finally, insert a blank character in the output following the label.
        gen1()

    @staticmethod
    def GN2():
        """GENERATE 2 - Generate label 2"""
        # Same as GN1, except that it concerns the current label 2 cell.
        # i.e. the top cell in the stack.
        gen2()

    @staticmethod
    def LB():
        """LABEL - Next write is to label field"""
        # Set the output counter to card column 1.
        to_label()

    @staticmethod
    def OUT():
        """OUTPUT - output current line"""
        # punch card and reset output counter to card column 8.
        out()

    @staticmethod
    def END():
        """END - Finish machine"""
        # Denotes the end of the program.
        global finished
        finished = True

def loop() -> bool:
    """FETCH/DECODE/EXECUTE loop"""
    global ip
    ip = 0

    while not finished:
        ##debug("--- LOOP")
        i = fetch()
        ##debug("loop reads: %s" % str(i))
        M2Instruction.exec(i)
    return switch


#===== PYTHON HAND-CODED META-II PARSER ========================================

#----- GRAMMAR HELPERS ---------------------------------------------------------

def required(flag):
    """Expect True"""
    if not flag:
        fail("required:item missing")

def any(fn, *args):
    """Allow 0..n occurences (iteration)"""
    seen = False
    while True:
        if not fn(*args): break
        seen = True
    return seen

def stackme(fn):
    """Decorator for statement fns"""
    def wrap():
        _call()
        r = fn()
        _ret()
        return r
    return wrap


#----- META-I GRAMMAR ----------------------------------------------------------

@stackme
def out1():
    # OUT1 =
    # '*1'
    if is_literal("*1"):
        # .OUT('GN1')
        dot_out("GN1")
        out()

    # / '*2'
    elif is_literal("*2"):
        # .OUT('GN2')
        dot_out("GN2")
        out()

    # / '*'
    elif is_literal("*"):
        # .OUT('CI')
        dot_out("CI")
        out()

    # / .STRING
    elif dot_string():
        # .OUT('CL ' *);
        dot_out("CL ")
        wr_saved()
        out()

    else:
        return False

    return True

@stackme
def output():
    # OUTPUT =
    #    (
    def g1():
        # '.OUT'
        if is_literal(".OUT"):
            # '('
            required(is_literal("("))

            # $
            # OUT1
            any(out1)

            # ')'
            required(is_literal(")"))

        # / '.LABEL'
        # .OUT('LB')
        # OUT1
        elif is_literal(".LABEL"):
            dot_out("LB")
            out()
            required(out1())

        else:
            return False

        return True
    if not g1(): return False
    #    )
    #    .OUT('OUT');
    dot_out("OUT")
    out()
    return True

@stackme
def ex3():
    # EX3 =
    # .ID
    if id():
        # .OUT('CLL ' *)
        dot_out("CLL ")
        wr_saved()
        out()

    # / .STRING
    elif dot_string():
        # .OUT('TST ' *)
        dot_out("TST ")
        wr_saved()
        out()

    # / '.ID'
    elif is_literal(".ID"):
        # .OUT('ID')
        dot_out("ID")
        out()

    # / '.NUMBER'
    elif is_literal(".NUMBER"):
        # .OUT('NUM')
        dot_out("NUM")
        out()

    # / '.STRING'
    elif is_literal(".STRING"):
        # .OUT('SR')
        dot_out("SR")
        out()

    # / '('
    elif is_literal("("):
        # EX1
        required(ex1())
        # ')'
        required(is_literal(")"))

    # / '.EMPTY'
    elif is_literal(".EMPTY"):
        # .OUT('SET')
        dot_out("SET")
        out()

    # / '$'
    elif is_literal("$"):
        # .LABEL
        to_label()

        # *1
        gen1()
        out()

        # EX3
        required(ex3())

        # .OUT('BT ' *1)
        dot_out("BT ")
        gen1()
        out()

        # .OUT('SET');
        dot_out("SET")
        out()

    else:
        return False
    return True

@stackme
def ex2():
    # EX2 =
    #    (
    def g1():
        # EX3
        if ex3():
            # .OUT('BF ' *1)
            dot_out("BF ")
            gen1()
            out()

        # / OUTPUT
        elif output():
            pass

        else:
            return False
        return True
    if not g1(): return False
    #    )

    #    $
    #    (
    def g2():
        # EX3
        if ex3():
            # .OUT('BE')
            dot_out("BE")
            out()

        # / OUTPUT
        elif output():
            pass

        else:
            return False

        return True
    any(g2)
    #    )

    # .LABEL
    to_label()

    # *1;
    gen1()
    out()
    return True


@stackme
def ex1():
    # EX1 =
    #    EX2
    if not ex2(): return False

    #    $
    #    (
    def ex1b():
        # '/'
        if not is_literal("/"): return False
        # .OUT('BT ' *1)
        dot_out("BT ")
        gen1()
        out()

        # EX2
        required(ex2())
        return True
    any(ex1b)
    #    )

    # .LABEL
    to_label()

    # *1;
    gen1()
    out()
    return True

@stackme
def statement():
    # ST = .ID
    if not id(): return False

    # .LABEL
    to_label()

    # *
    wr_saved()
    out()

    # '='
    required(is_literal("="))

    # EX1
    required(ex1())

    # ';'
    required(is_literal(";"))

    # .OUT('R');
    dot_out("R")
    out()
    return True

@stackme
def program():
    # PROGRAM = '.SYNTAX'
    if not is_literal(".SYNTAX"): return False

    # .ID
    required(id())

    # .OUT('B ' *)
    dot_out("B ")
    wr_saved()
    out()

    # $ ST
    any(statement)

    # '.END'
    required(is_literal(".END"))

    # .OUT('END');
    dot_out("END")
    out()
    return True


#----- RUNNABLE TOOL -----------------------------------------------------------

def run(f, fn) -> None:
    global file

    file = f
    if not fn():
        fail("run:incomplete")
    else:
        print()

def meta2_py(f):
    global file

    run(f, program)

def meta2_vm(spec_name, f):
    global file

    load_instrs(spec_name)
    run(f, loop)

if __name__ == "__main__":
    USAGE = \
"""Usage:
m2         use built-in gen0 metaii program to parse stream
m2 <prog>  use provided <prog> to parse stream
"""

    if len(sys.argv) == 1:
        # m2
        meta2_py(sys.stdin)

    elif len(sys.argv) == 2:
        # m2 <prog>
        prog_name = sys.argv[1]
        meta2_vm(prog_name, sys.stdin)

    else:
        exit(USAGE)

# END
