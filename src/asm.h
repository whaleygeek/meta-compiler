// asm.h  06/01/2021  D.J.Whale
//   A set of macros and wrappers to turn ASM into C
//
// SAMPLE PROGRAM - displays * on stdout then ends
//   #include "asm.h"
//   MOV(R0, 42)
//   STR(R0, OUT)
//   HALT()
//   END()
// input char (blocking, line-oriented buffering)
//    LDR(R0, IN)   // read from memory location IN
// putback char (useful for parser algorithms with lookahead)
//    STR(R0, IN)   // write to memory location IN
// output char
//    STR(R0, OUT)  // write to memory location OUT
//
// If you want a stack:
//  push R1:
//      STR(R1, SP)
//      SUB(SP, SP, 1)
//
//  pop R1:
//      ADD(SP, SP, 1)
//      LDR(R1, SP)
//
// If you want procedures:
//   You must handle parameter passing and return results yourself
//   but this will use the C stack to call and return.
//     JSR(name)
//     FN(name)
//       RET()
//     ENDFN()

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>

// CONFIGURATION
#define NUM_REGS 13
#define MEM_SIZE 1024
#define STKTOP   MEM_SIZE-4
#define FAIL     MEM_SIZE-3
#define IN       MEM_SIZE-2
#define OUT      MEM_SIZE-1

// REGISTERS
#define R(N)     regs[N]
#define R0 R(0)
#define R1 R(1)
#define R2 R(2)
#define R3 R(3)
#define R4 R(4)
#define R5 R(5)
#define R6 R(6)
#define R7 R(7)
#define R8 R(8)
#define R9 R(9)
#define R10 R(10)
#define R11 R(11)
#define R12 R(12)
#define SP  R(12)

// DEBUG
#if DEBUG
#define P(M)   printf("%s ",   (M))
#define PN(M)  printf("%s\n",  (M))
#define PV(V)  printf("%d ",   (V))
#define PVN(V) printf("%d\n", (V))
#else
#define P(M)
#define PN(M)
#define PV(V)
#define PVN(V)
#endif

// LABELS
#define L(LABEL)          L_ ## LABEL
#define LABEL(LABEL)      L(LABEL): ;

// ALLOCATE SPACE ON STACK FOR LOCAL VARIABLES
#define ALLOC(NAME)       P("ALLOC"); P(#NAME); const uint32_t NAME = SP--; PVN(NAME);
// INSTRUCTIONS
#define STR(Rd, MA)       P("STR");  P(#Rd); PN(#MA);           store(Rd, MA); PVN(Rd);
#define LDR(Rd, MA)       P("LDR");  P(#Rd); PN(#MA);           Rd = load(MA); PVN(Rd);
#define ADD(Rd, Rn, OP2)  P("ADD");  P(#Rd); P(#Rn); PN(#OP2);  Rd = Rn + OP2; PVN(Rd);
#define SUB(Rd, Rn, OP2)  P("SUB");  P(#Rd); P(#Rn); PN(#OP2);  Rd = Rn - OP2; PVN(Rd);
#define MOV(Rd, OP2)      P("MOV");  P(#Rd); PN(#OP2);          Rd = OP2;      PVN(Rd);
#define AND(Rd, Rn, OP2)  P("AND");  P(#Rd); P(#Rn); PN(#OP2);  Rd = Rn & OP2; PVN(Rd);
#define ORR(Rd, Rn, OP2)  P("ORR");  P(#Rd); P(#Rn); PN(#OP2);  Rd = Rn | OP2; PVN(Rd);
#define EOR(Rd, Rn, OP2)  P("EOR");  P(#Rd); P(#Rn); PN(#OP2);  Rd = Rn ^ OP2; PVN(Rd);
#define MVN(Rd, OP2)      P("MVN");  P(#Rd); PN(#OP2);          Rd = ~OP2;     PVN(Rd);
#define LSL(Rd, Rn, OP2)  P("LSL");  P(#Rd); P(#Rn); PN(#OP2);  Rd = Rn << OP2;PVN(Rd);
#define LSR(Rd, Rn, OP2)  P("LSR");  P(#Rd); P(#Rn); PN(#OP2);  Rd = Rn >> OP2;PVN(Rd);
#define CMP(Rn, OP2)      P("CMP");  P(#Rn); PN(#OP2);          cmp(Rn, OP2);

#define B(LABEL)          P("B");   PN(# LABEL); goto L(LABEL);
#define BEQ(LABEL)        P("BEQ"); PN(# LABEL); if (z)             {P("yes"); goto L(LABEL);};
#define BNE(LABEL)        P("BNE"); PN(# LABEL); if (!z)            {P("yes"); goto L(LABEL);};
#define BLT(LABEL)        P("BLT"); PN(# LABEL); if (n != v)        {P("yes"); goto L(LABEL);};
#define BGT(LABEL)        P("BGT"); PN(# LABEL); if (!z && (n ==v)) {P("yes"); goto L(LABEL);};

#define HALT()            PN("HALT"); return;
#define END()

// PSEUDO-INSTRUCTIONS
#define FN(NAME)    void NAME () {
#define ENDFN()     }
#define BSR(NAME)   NAME ();
#define RET()       return;

// MACHINE STATE
uint32_t regs[NUM_REGS];
uint32_t mem[MEM_SIZE];
bool n; // negative flag
bool z; // zero flag
bool c; // carry flag
bool v; // overflow flag

void fail(char * msg)
{
    fprintf(stderr, "fail:%s\n", msg);
    exit(1);
}

// MEMORY-MAPPED IO ROUTINES
uint32_t load(uint32_t mar)
{
    assert(mar < MEM_SIZE);
    switch (mar)
    {
        case IN:   return getchar();
        case FAIL: fail("possible stack underflow");
        default:   return mem[mar];
    }
}

void store(uint32_t v, uint32_t mar)
{
    assert(mar < MEM_SIZE);
    switch (mar)
    {
        case IN:   ungetc(v, stdin); break;
        case OUT:  putchar(v);       break;
        case FAIL: fail("possible stack underflow");
        default:   mem[mar] = v;     break;
    }
}

#define NEGATIVE 0x80000000

bool is_add_carry(uint32_t dst, uint32_t src, uint32_t res)
{
    // R = D + S
    // d s r  c
    // 0 0 0  0
    // 0 0 1  1 **** 00
    // 0 1 0  0
    // 0 1 1  0
    // 1 0 0  0
    // 1 0 1  0
    // 1 1 0  1 **** 11
    // 1 1 1  0
    bool s = ((src & NEGATIVE) != 0);
    bool d = ((dst & NEGATIVE) != 0);
    bool r = ((res & NEGATIVE) != 0);
    return (s == d) && (s != r);
}

bool is_sub_carry(uint32_t dst, uint32_t src, uint32_t res)
{
    // R = D - S   C = signed (D<S)
    //
    // d s r  c
    // 0 0 0  0    02-01 = 01  2 < 1    = false
    // 0 0 1  1  * 01-02 = FF  1 < 2    = true   ****
    // 0 1 0  0    01-FF = 02  1 < -1   = false
    // 0 1 1  0    01-80 = 81  1 < -128 = false
    // 1 0 0  1  * 80-01 = 7F -128 < 1  = true   ****
    // 1 0 1  1  * 80-00 = 80 -128 < 0  = true   ****
    // 1 1 0  0    FE-FE = 00 -2 < -2   = false
    // 1 1 1  1  * FE-FF = FF -2 < -1   = true   ****
    //
    // d & !s
    // (d==s) & r

    bool s = ((src & NEGATIVE) != 0);
    bool d = ((dst & NEGATIVE) != 0);
    bool r = ((res & NEGATIVE) != 0);
    return (d && ! s) || ((d == s) && r);
}

bool is_sub_overflow(uint32_t dst, uint32_t src, uint32_t res)
{
    // R = D-S  C = signed overflow means from -lim to +lim or
    //              from +lim to -lim
    //
    // d s r  c
    // 0 0 0  0    02-01 = 01
    // 0 0 1  0    01-02 = FF
    // 0 1 0  0    01-FF = 02
    // 0 1 1  1    01-80 = 81
    //
    // 1 0 0  1    80-01 = 7F
    // 1 0 1  0    80-00 = 80
    // 1 1 0  0    FF-FF = 00
    // 1 1 1  1    FE-FF = FF
    //
    // !d & (s&r)
    // d & (s==r)

    bool s = ((src & NEGATIVE) != 0);
    bool d = ((dst & NEGATIVE) != 0);
    bool r = ((res & NEGATIVE) != 0);
    return (! d && (s && r)) || (d && (s == r));
}

void cmp(uint32_t lhs, uint32_t rhs)
{
uint32_t res;

    res = lhs - rhs;
    //printf("%u = %u - %u  ", res, lhs, rhs);

    //negative (N) set if result is -ve, clear if result is +ve
    n = (res & NEGATIVE) != 0;

    //zero (Z)     set if result is 0, clear if result is NZ
    z = (res == 0);

    //carry (C)    set if carry occurred as an unsigned operation
    c = is_sub_carry(lhs, rhs, res);

    //overflow (V) 2's complement compare
    v = is_sub_overflow(lhs, rhs, res);
    //printf("z:%u n:%u c:%u v:%u\n", z, n, c, v);
}

void run(); // forward declaration

int main(void)
{
    memset(regs, sizeof(regs), 0);
    memset(mem, sizeof(mem), 0);
    z = c = v = 0;
    SP = STKTOP;
    run();
    return regs[0]; // result code
}

void run()

    // User code goes here. END() adds closing brace.

// END OF FILE: asm.h
