# Implementation Notes

## What tech should we use?

When reconstructing a program that was orignally written 56 years ago,
there are a few choices to make.

* I wanted to be true to what META-II was trying to achieve, the fact
that you could take a simple textual specification of a language, and
automatically generate a recogniser for that language.

* I also wanted to feel some of the pain that the developer had felt when
trying to get the program working, but take advantage a little bit of
modern tools.

* But I didn't have an IBM computer or a punched card keypunch to hand,
and reconstructing one or building or finding a simulator didn't seem
that helpful to my key goal, which was to look at early developments
in syntax directed translation.

So, I chose to implement the META-II input language as close
as possible to the original, to get the example valgol1 language working,
and to implement the virtual machine presented using the same instructions.
But I chose to use Python as a way to implement this in a modern language.

Additionally, I wanted to make sure that when adding target code generation
for the language, I was targetting a machine that made sense today
(as the instruction sets of old and new computers are still very similar even
today). For that, I chose the AQA examinations board small specification
of an ARM-like assembly language as the target machine.

## Assembly language 

The choice of the ARM-like assembly language seemed to provide an interesting
future development path, the idea being that I could later generate 
assembly language for the Peter Higginson AQA machine simulator listed
in the references.

But, at this stage of the project, I didn't want to distract too much from
learning and dealing with compatibility issues with other tools.

## Converting from asm to C

So, I chose to use a technique that I have used a number of times throughout
my career, which uses the macro preprocessor of the C language to simply
translate from assembly instructions into short runs of C code. This C
code is then compiled with the C compiler and you get a program that you can
run. You can see the results of this macro development in the
[asm.h](./src/asm.h) file. 

The main difference here is that I didn't have to write an assembler and a
simulator to get code to run, all I had to do was to treat each assembly
language instruction as a macro call with parameters, and to build a very
simple model of registers and instruction execution out of a few arrays and
short sequences of C code. Basically, changing ```MOV R1, #1``` 
to ```MOV(R1, 1)``` is all that is required to turn the assembly language into 
a C macro call,

There are some severe restrictions of the AQA machine as specified by its
authors, not least that there is no binary representation specified, and
it doesn't support any addressing mode apart from immediate and direct.
So it is really hard to implement a stack. 

Fortunately, Peter Higginson has added extensions to his simulator that
support more of the ARM instruction set, and had to define his own binary
encoding inspired by the real ARM processors, so I know that there is a
migration path to running code on his simulator in the future.

## Integers vs floats

The original META-II implementation assumed an underlying machine model
that had a built-in floating point unit, whereas my current implementation
assumes integer only variables - this is so that I don't close off the
possible future path towards running the generated assembly language on
Peter Higginson's AQA simulator (as the AQA specification dictates integer
only operations).

## Multiply and Divide

The valgol1 language specified in the original 1964 META-II paper from
Schurre has a multiply instruction in it, and my current machine does nothing
with it. In fact, it accepts it as a valid program, but generates no code
for the multiply. I had to tweak the example a bit to make it do something
useful given just integer numbers, and no multiply instruction.

One of the tasks of the AQA syllabus is to write a multiply routine from
first principles (presumably using repeated additions, as an efficient
bitwise multiplier is quite complex to write even for A level).

So my plan here is to present a few different multiply and divide routine
implementations, and then get the code generator to make a call to them
and insert the callable assembly language as a way to introduce the idea
of a library function. I already have a mechanism for introducing
simple parameter passing, return results, and call and return within
the bounds of the AQA assembly language instructions that are supported.

## Looking at how it actually works

Note: The makefile is configured so that the intermediate .c file it generates 
is not deleted as part of the build process, so once you run ```make```
you can open the test1.c file and look at the assembly language macro calls
that have been inserted by the code generator, and relate these back to
the macros in asm.h. 

A fun trick here is to type ```gcc -E test1.c```
and you will get dumped to the standard output stream the preprocessed macros,
so you see the runs of C code that will actually be compiled.

Secondly, if you instead type ```gcc -S test1.c```, you will get an assembly
language file for your target machine generated (test1.s), so effectively
this process has translated from valgol1 to AQA asm, then to C, and then
to the machine code format for your machine (in my case, an Intel based mac).

**valgol1 program**
```
.BEGIN
    .VAR X;
    0 = X;
    .UNTIL X .= 20 .DO
    .BEGIN
        EDIT( X+X, '*');
        PRINT;
        X + 1 = X
    .END
.END
```

**assembly language (macros)**
```
     #include "asm.h"
     {
     ALLOC( X)
     //PRIMARY NUM
     MOV(R0, 0)
     STR(R0, SP--)
     //RVAL
     LDR(R0, ++SP)
     //ASSIGN
     //LVAL
     STR(R0, X)
     //UNTIL continue
     LABEL( A01)
     //PRIMARY ID
     LDR(R0, X)
     STR(R0, SP--)
```

**C code**
```
void run()
# 2 "test1.c" 2
{;; const uint32_t X = regs[12]--;;;;; 
    regs[0] = 0;;;;; 
    store(regs[0], regs[12]--);;;;; 
    regs[0] = load(++regs[12]);;;;; 
    store(regs[0], X);;
# 13 "test1.c"
 L_A01: ;;;; 
    regs[0] = load(X);;;;; 
    store(regs[0], regs[12]--);;;;; 
    regs[0] = 20;;;;; 
    store(regs[0], regs[12]--);;;;; 
    regs[0] = load(++regs[12]);;;;; 
    regs[1] = load(++regs[12]);;;;; 
    cmp(regs[0], regs[1]);;;; 
    regs[0] = 0;;;; 
    if (z) {; goto L_A02;};;;; 
    regs[0] = 1;;
# 27 "test1.c"
```

Note: All those semicolons are due to disabled debug macros, the semicolons are 
still inserted.

**Intel assembly language**
```
	.globl	_run
	.align	4, 0x90
_run:                                   ## @run
	.cfi_startproc
## BB#0:
	pushq	%rbp
Ltmp42:
	.cfi_def_cfa_offset 16
Ltmp43:
	.cfi_offset %rbp, -16
	movq	%rsp, %rbp
Ltmp44:
	.cfi_def_cfa_register %rbp
	subq	$16, %rsp
	movq	_regs@GOTPCREL(%rip), %rax
	movl	48(%rax), %ecx
	movl	%ecx, %edx
	addl	$4294967295, %edx       ## imm = 0xFFFFFFFF
	movl	%edx, 48(%rax)
	movl	%ecx, -4(%rbp)
	movl	$0, (%rax)
	movl	(%rax), %edi
	movl	48(%rax), %ecx
	movl	%ecx, %edx
	addl	$4294967295, %edx       ## imm = 0xFFFFFFFF
	movl	%edx, 48(%rax)
	movl	%ecx, %esi
	callq	_store
```