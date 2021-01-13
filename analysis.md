# Analysis of META-II features and implementation

NOTE: If you are not familiar with the general features provided by the Lex
and Yacc tool, do a quick Google search now and make sure you understand
roughly what they are used for. That will make it a bit easier for you
to follow this section.

## Nice features of META-II

META-II is an old tool by current day standards.
However, it still has the beginnings of some great automated features,
even though it doesn't take advantage of modern wisdom about parsing.

Here is a brief overview of its features:

* A context free language grammar is specified in textual format, and
it parses this into a machine that will then recognise that grammar.
This feature alone allows META-II to be used as a validation harness,
whereby it will give a boolean result as to whether any given sentence
is valid or invalid in the language defined by that grammar.
That's great, for example, for writing validators, test harnesses, and
other tools.

* The original META-II paper from Schorre specifies a small but complete
virtual machine with a tiny and easy to implement instruction set.
META-II generates code for this virtual machine, and in essense it auto
generates for you, an interpreter that looks at an input sentence, and
attempts to match it against the grammar.
This means that your specification of the language grammar is executable,
and can be used to write real programs that run on real computers.

* Annotations can be made to the grammar in the form of .OUT and .LABEL
commands, that generate output when specific grammar rules, or parts of
rules, are matched.
This allows the grammar to be used in a syntax-directed-translation mode,
whereby as each part of a language is matched, it can generate the appropriate
target code that implements that part of the language.
e.g. when an IF statement is matched in a language grammar, META-II can
output a comparison statement and a branch, that implements that IF statement.

* META-II is self-compiling; i.e. you can specify the META-II language in
it's own grammar, run that grammar through itself, and you get an interpreter
that recognises the META-II syntax.

* The virtual machine specification is tiny, only 17 instructions, each
with very basic semantics that are easy to implement.
The whole program fitted on a 1960's computer with only 8K of memory.
This means it can be implemented on tiny microcontrollers like some of the
really small devices from Atmel (such as the ATTiny 85 as used in the Adafruit
Gemma, for example).

* The generator generates a limitless supply of branch labels for you,
and provides a way to generate and to refer to those labels.
This means you don't have to write any code to build a working parser that
generates target code with branch instructions in it, META-II handles all that
for you. This is great for auto generating assembly language, and as will
be seen elsewhere in this repository, generating C code.

* META-II contains a method to capture matched source text (called _lexemes_
in the classical literature), such as the characters that make up an identifier
name, or the characters that make up a number.
These can then be copied verbatim, or simple string concatenation used,
to output them into the target program listing.

## Performance issues

META-II is tiny, but was written before some more modern theories were 
established. As a result of this, there are various inefficiences in how it
works, and while it generates a _correct_ and _equivalent_ machine from an
arbitrary language grammar, it does not generate an _optimal_ implementation.

Here is why:

* Every time it tries to match an identifier, a number, or a literal string,
it runs a 'skip whitespaces' routine. This means that if there are a number
of choices on what a token actually is, it will restart from the start of the
token and skip whitespaces for every possible option of that token.
This is called back-tracking.
The amount of re-skipping is small and self contained, but it is not optimal.
(This could have been fixed in the present implementation but we chose to
implement the code as close as possible to the original specification).

* Where a grammar rule has alternate tokens that may be valid at that time,
META-II will systematically try each alternative until one matches.
This is again called back-tracking.
This means that if part of your grammar might allow an IDENTIFIER, a NUMBER, or 
a number of different SYMBOLs at that point, META-II will try them all until
it finds one that matches. This causes a number of re-scans of the current
token until a match is found.
(This is harder to fix, and is inherrent in the design of META-II in that it
does not have a separate lexical analyser phase to pre-detect a valid token).

* Due to the lack of a lexical analyser, META-II cannot take advantage of now
well established methods that can build an optimal non-backtracking lexical
analyser. It also means that lexical analysis and syntax analysis is somewhat
'muddled together' in its design. On one hand this is a good thing, as there
is one way to match, but it is non optimal. For a large program, this
extra back-tracking will be noticeable when parsing large programs.

* Another way of thinking of the lack of a lexical analysis phase, is that
META-II does not do its alternate comparisions against integer numbered
token id's like a modern compiler will do; for every check for a specific
token type, it has to repeatedly look at the characters and decide if that
token matches or not. Conversely, a lexical analyser that pre-prepares uniquely 
numbered tokens, allows the syntax analyser to do a simple integer comparison
to detect a token. Additionally, if the Yacc parser engine uses a switch() 
statement to select the outcome based on the next token, most C compilers
will generate an efficient jump table that executes really fast.

* META-II requires a predictive grammar (a grammar where there is no
backtracking allowed at the syntactic level). This helps performance, because
the next token always defines the path to take (but remember that token selection
uses a lot of character-level backtracking to detect the next token).

## String captures

As mentioned earlier, META-II supports a simple string capture mechanism.
e.g. a .ID or .NUM or .STRING directive will tell META-II to match those
items, and capture the lexeme (matched character span) so that it can be
output to the target code stream later. This is useful, and means that you
don't write code (like in Yacc and Lex) to indicate what to do when a
match occurs; you instead provide an output statement to direct META-II
how to generate a snippet of output.

This 'no code' approach does limit your options quite a lot, compared to
the full power of the 'code annotations' supported by Yacc and Lex.
You can copy the last matched lexeme to the output stream, or output
a literal piece of text, or output a label, but that is all!

This often requires you to bend the grammar a bit and perhaps refactor
it with an extra layer in the grammar to fudge context, and output different
output strings depending on how a series of tokens was matched. This
contextual bending goes against modern compiler theory.
Also, the lack of any actions other than .OUT and .LABEL mean if you run out
of steam with this approach, there is nowhere to go. It may therefore mean
that some target languages are just impossible to generate, and you have to
write additional post-processing tools to make up for that.

## Lack of an attributed grammar

Yacc allows any grammar rule to pass attributes up the parse tree as
grammar rules are matched, and this is a really powerful method of communicating
and combining various parts of the matched syntax in order to generate target
code (or indeed as the Yacc manual demonstrates, implement the obligatory
expression interpreter example). You just can't do that with META-II as it
provides you a purely data driven environment with no code extension at all.

## Factored groupings

META-II has a ( ) pair that allows you to group items together within a
grammar rule, and this gives more expressive power to the language that helps
with some of the more tricky grammars, and as a result of these groups,
a META-II grammar is often a lot smaller than a full context-free grammar
that you might write for Yacc.

## Repeating groups

META-II has a $ operator that means '0 or more repetitions of the next item',
and the $ operator can be used to prefix a grouped item with ( ) also.
This is very powerful, and in addition to groups, it means that META-II
grammars are usually a lot smaller than a Yacc grammar. It also makes
them closer to EBNF, which was invented at around the same time.

## Ambiguity number 1

By far the biggest issue in META-II compared to modern toolkits like Yacc and
Lex, is that it doesn't give you all the tools required to deal with ambiguity,
and there are many pitfalls for the unwary. It is quite easy to write a grammar
that looks correct, but that suffers from some deeply rooted ambiguity problem,
and here it is clear that a lot of this extra wisdom came a lot later than
the work that was done on META-II.

This can be worked around with some modifications to the language, but if you
are trying to parse a specific language specification, you might find it
impossible. For example, I attempted to implement a small subset of Pascal.
I managed to get something that looked like it worked, but the 'begin'
and 'end' keywords were causing trouble. This turned out to be due to ambiguity
with an identifier (specified with .ID) as the string 'end' also matches
an identifier. Depending on the precedence and hierarchy in your grammar, it may 
be impossible to rewrite it such that the BEGIN and END keywords (all keywords!)
are processed before a .ID directive.

It is noteable that in all of the META-II examples a dot appears before keywords;
this is not a stylistic thing, it is deeply rooted in the fact that it provides
a way to disambiguate keywords from identifiers! This is another example where
the lack of a lexical analyser makes the job too hard to deal with in META-II,
because in a modern compiler, the lexical analyser resolves any ambiguity
between keywords and identifiers for you due to the way Lex (for example) 
codes priority based on the order that tokens are defined in the specification;
you always define the keywords in its specification first, and the identifier
specification comes later.

Interestingly, the 'begin' keyword did not suffer this fate like 'end'
did, due to it being placed differently in the hierarcy of the grammar with
respect to an identifier specified with the .ID directive.
(This was pretty hard to debug and track down, but very instructive!)

## Ambiguity number 2a

Another issue caused by lack of a lexical analyser, was highlighted when
I tried to implement a grammar for a subset of the C language.
Consider these 4 computations.

```
a = b || c;   // 1
a = b | c;    // 2
a = b && c;   // 3
a = b & c;    // 4
```

Annoyingly, all but 1 would parse correctly. I couldn't understand why 1 was
failing but 3 was passing. It turns out there is a complex web of issues
here that is very instructive.

To debug this, I added .OUT statements when each was matched, and it became
clear that it was matching against the wrong part of the grammar.

* In case 2, it was correctly matching as a bitwise-or.
* In case 4, it was correctly matching as a bitwise-and.
* In case 1, it was matching as a bitwise-or followed by a syntax error??!
* In case 3, it was matching as a bitwise-and followed by an address-of??!!

This explained why case 3 worked, it was really being interpreted as:

```
a = b &    &c;
```

Syntactically this was valid, but semantically it was WRONG!

Case 1 was a little harder to track down. It turns out that because META-II
doesn't have a seprate lexical analyser phase, it does not implement what is
known in modern compiler theory as _token disambiguation_, and it turns out this
is vital for the above to parse correctly. Without token disambiguation, there
is an ambiguity, and because the bitwise-or and logical-or are at different
levels in the precendence hierarchy of the grammar, it will never work!

Lex, as an example, will make sure that where there are ambiguities, it
resolves them by matching the longer token first. 
i.e. faced with two rules, namely a single bar character and a double bar 
character, it will always try to match the longest, and if that doesn't match, 
it will match the next longest. Depending on which order you put the token
specifications in the Lex file, you may get a warning as it imposes the
longest-match rule here.

META-II however just matches the first thing you ask it to check against.
So the grammar is coded to check for a single bar at a higher precedence level
than a double bar, so it gets checked first. Because of how the characters
are matched (minimal prefix matching) with the .STRING directive, it matches
the single bar (bitwise-or) then has another single-bar to process, which is
not valid in that context, and a syntax error occurs.

With the double ```and``` (logical and) it actually matches a bitwise-and first,
there is another ```and``` token following, and that matches as the address-of 
operator, which is valid followed by the identifier ```c``` and it parses 
without error.

This is pretty bad news for a compiler writing tool, you always want ambiguity
to be dealt with in a consistent way, and you never want it to incorrectly
accept a program in a way that the semantics are changed! This also breaks
down the principle that you can start by writing the syntax analyser first
and feed it a load of programs to make sure it works, then later add the
semantic analysis/code generation and assume your syntax analyser is tested!

When I studied compilers at university, and we learnt that Lex does some
clever things to disambiguate tokens that are similar (indeed it says as such in 
its user guide), I never quite appreciated why that was. 
This demonstrates the power of following in the footsteps of those before you, 
and taking principles right back to the point they were discovered, as a way to 
really understand them!

## Ambiguity number 2b

Armed with the knowledge of Ambiguity 2a, I set about to see if there were
other bad choices made by the lack of any token disambiguation. 
I was getting a syntax error with this code, that I didn't understand:

```
if (a >= b)
```

With the knowledge of the issue with META-II matching the shortest prefix of a
token that was being analysed, this was easy to diagnose (and fix).
The greater than symbol matches as a greater-than check, and the equals
symbol was being matched as an assignment-operator, and the two together
are not valid C.

The fix here was to change the order in the grammar (as greater-than and
greater-equal are in the same level of the grammar) so that META-II checks
for the longer tokens first. But that is a bit of a hack, that is not
always possible.









 