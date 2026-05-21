// Dax.g4 — ANTLR4 grammar for Data Analysis Expressions (DAX).
//
// PLACEHOLDER. The real grammar will be forked from the DaxStudio project's
// open-source grammar (Apache 2.0):
//   https://github.com/DaxStudio/DaxStudio/tree/master/src/DaxStudio.Parser
//
// Action items for first PR:
//   1. Fork DaxStudio's ANTLR4 grammar into this file.
//   2. Run `antlr4 -Dlanguage=Python3 Dax.g4` to generate Python lexer + parser.
//   3. Add a quarterly diff-against-upstream CI job that surfaces new DAX functions
//      Microsoft has added since our last fork.
//   4. Surface "unknown function" diagnostic when the parser encounters a function
//      not in the coverage registry — fail in CI before customers see it.
//
// Why ANTLR over hand-written recursive descent: ~250 DAX functions is too much
// to maintain by hand, and ANTLR4 has a strong Python runtime + good error recovery.
// Tree-sitter has no mature DAX grammar and weaker batch error-recovery.

grammar Dax;

// ── PLACEHOLDER RULES — REPLACE WITH DaxStudio FORK ──────────────────────

expression
    : literal
    | functionCall
    | columnReference
    | measureReference
    | expression op=('+'|'-'|'*'|'/') expression
    | '(' expression ')'
    ;

literal
    : NUMBER
    | STRING
    | 'TRUE' | 'FALSE'
    ;

functionCall
    : IDENTIFIER '(' (expression (',' expression)*)? ')'
    ;

columnReference
    : tableName=IDENTIFIER '[' columnName=IDENTIFIER ']'
    ;

measureReference
    : '[' measureName=IDENTIFIER ']'
    ;

// ── LEXER ────────────────────────────────────────────────────────────────

IDENTIFIER : [a-zA-Z_][a-zA-Z0-9_ ]* ;
NUMBER     : [0-9]+ ('.' [0-9]+)? ;
STRING     : '"' (~["\\] | '\\' .)* '"' ;

WS         : [ \t\r\n]+ -> skip ;
LINE_COMMENT : '//' ~[\r\n]* -> skip ;
BLOCK_COMMENT: '/*' .*? '*/' -> skip ;
