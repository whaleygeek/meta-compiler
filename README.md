# Meta Compiler

## What is this?

This is a clean re-implementation of a small compiler writing toolkit called
META-II.  META-II was designed in 1964 by D.V.Schorre.

There is a reprint of the original article in the April 1980 edition of
Dr Dobbs Journal, which you can read from _The Internet Archive_
[here](https://archive.org/details/dr_dobbs_journal_vol_05_201803/page/n155/mode/2up)

The toolkit provides the parsing and code generation stages of a very simple
syntax directed translator. Given a textual specification of a language grammar,
and annotations to that grammar for code generation actions, it translates
from an input language to a target language. If you have an assembler and a
simulator for that target language, you can assemble and then run your program.

Also presented here is a technique we have developed that allows you to generate
instructions for a target CPU, and via a set of C macros, turn that into a C
program that you can compile and run (thus giving you a cheap simulator).

## Where did it come from?

META-II was originally written by D.V. Shorre at UCLA, published in 1964.
His original paper was later re-published in Dr Dobbs Journal, Volume 5 No. 
4 April 1980, which was how I discovered it (from a pile of antique computer 
magazines bought as a job lot from a second hand bookshop).

## Why did I reimplement it?

I have a keen interest in compiler theory, and through some current research
work in this area, I was looking back through time to see how the compiler
theories of today were formed. This was one of the many papers I discovered
on my dig through the archives.

Meta II shows the beginnings of the development of syntax directed translation
algorithms and techniques, and is one of the earliest practical examples I could 
find of a textual input format that was used to mechanistically generate a 
program that is a complete syntax analyser.

## How to run the example

You need a C compiler installed. I assume gcc is installed, but if you have
another compiler, you can change the settings at the top of the makefile.

Change into the src directory and type `make` which will then self check the
compiler (by self-compiling, see later!), and through a number of steps you will 
get an executable file called `test1`.

Run this `test1` file to see the following output:

```bash
davidw $ ./test1
*
 *
  *
   *
    *
     *
      *
       *
        *
         *
          *
           *
            *
             *
              *
               *
                *
                 *
                  *
                   *
davidw $ 
```

**An Apology**: If you are using Windows and don't have any development tools 
installed, there's probably not much I can do to help here, sadly.
You _might_ consider using the 
[Raspberry Pi Desktop](https://www.raspberrypi.org/software/operating-systems/) 
running inside a
[Virtual Box virtual machine](https://www.virtualbox.org/wiki/Downloads), 
as that has all of the necessary development tools pre-installed.

## How complete is the reimplementation?

This is a reasonably complete implementation, in that it uses the same 
internal virtual machine instruction set and the same textual specification
techniques. However, I didn't have a spare IBM 1401 computer to hand,
so I wrote it in Python instead. Also, the original article allowed for the
programs to be entered on a punched-card keypunch, and I didn't have one of
those in my archives either; so I removed the symbolic artifacts that were
unique to keypunching punch cards, and used a standard ASCII character set.

## What can you use META-II for?

* Write, compile, and run simple VALGOL1 programs.
* Design a syntax directed compiler for a reasonably sized high level
language, and then annotate the compiler to generate code for a machine of your
choosing that will run that code.
* Perform research into automated syntax directed translation.
* Design and completely test your own mini language

## Other useful information

* [Analysis of the design of META-II](./analysis.md)
* [Where meta-II fits into the history of compilers](./history.md)

## References

Schorre, D.V., Meta II: A Syntax-Oriented Compiler Writing Language
UCLA Computing Facility, 1964
http://www.ibm-1401.info/Meta-II-schorre.pdf

Schorre, D.V., 
Meta II: A Syntax-Oriented Compiler Writing Language
Dr Dobbs Journal, April 1980
5(4) pp. 17-25.

AQA, Assembly Language Instruction Set: AS and A-level paper 2,
AQA-75162-75172-ALI, 2015
https://filestore.aqa.org.uk/resources/computing/AQA-75162-75172-ALI.PDF

Higginson, P., AQA Assembly simulator,
https://www.peterhigginson.co.uk/AQA/

Higginson, P., Notes about AQA Assembly Language limitations,
https://www.peterhigginson.co.uk/AQA/info.html

## Copyright
(c) David Whale,
January 2021
