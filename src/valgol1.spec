.SYNTAX PROGRAM

PRIMARY =
    .ID
        .OUT('//PRIMARY ID')
        .OUT('LDR(R0,' * ')')
        .OUT('STR(R0, SP--)')
    / .NUMBER
        .OUT('//PRIMARY NUM')
        .OUT('MOV(R0,' * ')')
        .OUT('STR(R0, SP--)')
    / '(' EXP ')'
    ;

TERM =
    PRIMARY $ ( '*' PRIMARY .OUT('//mult') )
    ;

EXP1 =
    TERM
    $ ( '+' TERM
        .OUT('//EXP1 ADD')
        .OUT('LDR(R0, ++SP)')
        .OUT('LDR(R1, ++SP)')
        .OUT('ADD(R0, R0, R1)')
        .OUT('STR(R0, SP--)')
    / '-' TERM
        .OUT('//EXP1 SUB')
        .OUT('LDR(R0, ++SP)')
        .OUT('LDR(R1, ++SP)')
        .OUT('SUB(R0, R0, R1)')
        .OUT('STR(R0, SP--)')
    )
    ;

EXP =
     EXP1 ( '.=' EXP1
        .OUT('//EXP EQ')
        .OUT('LDR(R0, ++SP)')
        .OUT('LDR(R1, ++SP)')

        .OUT('CMP(R0, R1)')
        .OUT('MOV(R0, 0)')
        .OUT('BEQ(' *1 ')')
        .OUT('MOV(R0, 1)')
        .OUT('LABEL(' *1 ')')

        .OUT('STR(R0, SP--)')
          / .EMPTY )
     ;

RVAL =
    EXP
        .OUT('//RVAL')
        .OUT('LDR(R0, ++SP)')
    ;

LVAL =
    .ID
        .OUT('//LVAL')
        .OUT('STR(R0,' * ')')
    ;

ASSIGNST =
    RVAL '='
        .OUT('//ASSIGN')
    LVAL
    ;

UNTILST =
    '.UNTIL'
        .OUT('//UNTIL continue')
        .OUT('LABEL(' *1 ')')
    EXP
        .OUT('//UNTIL compare')
        .OUT('LDR(R0, ++SP)')
        .OUT('CMP(R0, 0)')
        .OUT('BEQ(' *2 ')')
    '.DO' ST
        .OUT('//UNTIL end')
        .OUT('B(' *1 ')')
        .OUT('//UNTIL break')
        .OUT('LABEL(' *2 ')')
    ;

CONDST =
    '.IF'
        .OUT('//IF')
    EXP '.THEN'
        .OUT('//THEN')
    ST
    '.ELSE'
        .OUT('//ELSE')
        .OUT('// ' *1)
    ST
        .OUT('// ' *2)
        .OUT('//ENDIF')
    ;

IOST =
    'EDIT' '(' EXP ',' .STRING
        .OUT('//EDIT')
        .OUT('LDR(R0, SP++)')
        .OUT('MOV(R1, ' * ')')
        ')'
    / 'PRINT'
        .OUT('//PRINT')
        .OUT("MOV(R2, ' ')")
        .OUT('LABEL(' *1 ')')
        .OUT('CMP(R0, 0)')
        .OUT('BEQ(' *2 ')')
        .OUT('SUB(R0, R0, 1)')
        .OUT('STR(R2, OUT)')
        .OUT('B(' *1 ')')
        .OUT('LABEL(' *2 ')')
        .OUT('STR(R1, OUT)')
        .OUT('MOV(R1, 10)')
        .OUT('STR(R1, OUT)')
    ;

IDSEQ1 =
    .ID
        .OUT('ALLOC(' * ')')
    ;

IDSEQ = IDSEQ1 $ (',' IDSEQ1)
    ;

DEC =
    '.VAR' IDSEQ
    ;

ST =
    IOST / ASSIGNST / UNTILST / CONDST / BLOCK
    ;

BLOCK =
    '.BEGIN' .OUT('{') (DEC ';' / .EMPTY) ST $ (';' ST ) '.END' .OUT('}')
    ;

PROGRAM =
    .OUT('#include "asm.h"')
    BLOCK
    .OUT('END()')
    ;

.END
