%option noyywrap
%option yylineno

%{
#include <stdio.h>


enum Token{
    IDENFR=1,INTCON,STRCON,MAINTK,CONSTTK,INTTK,BREAKTK,CONTINUETK,IFTK,ELSETK,ARRAYTK,
    NOT,AND,OR,WHILETK,GETINTTK,PRINTFTK,RETURNTK,PLUS,MINU,VOIDTK,MULT,DIV,
    MOD,LSS,LEQ,GRE,GEQ,EQL,NEQ,ASSIGN,SEMICN,COMMA,LPARENT,RPARENT,LBRACK,RBRACK,LBRACE,RBRACE,
    LEX_ERR
};

%} 

digit [0-9]
letter [A-Za-z]

MultilineComment "/*"([^\*]|(\*)*[^\*/])*(\*)*"*/"
SingleLineComment "//".*$


%%
"main" {printf("%s : MAINTK\n", yytext); return MAINTK; }
"const" {printf("%s : CONSTTK\n", yytext); return CONSTTK; }
"int" {printf("%s : INTTK\n", yytext); return INTTK; }
"break" {printf("%s : BREAKTK\n", yytext); return BREAKTK; }
"continue" {printf("%s : CONTINUETK\n", yytext); return CONTINUETK; }
"if" {printf("%s : IFTK\n", yytext); return IFTK; }
"else" {printf("%s : ELSETK\n", yytext); ; return ELSETK; }
"while" {printf("%s : WHILETK\n", yytext); return WHILETK; }
"getint" {printf("%s : GETINTTK\n", yytext); return GETINTTK; }
"printf" {printf("%s : PRINTFTK\n", yytext); return PRINTFTK; }
"return" {printf("%s : RETURNTK\n", yytext); return RETURNTK; }
"void" {printf("%s : VOIDTK\n", yytext); return VOIDTK; }
"array" {printf("%s : ARRAYTK\n", yytext); return ARRAYTK; }

"!" {printf("%s : NOT\n", yytext); return NOT; }
"&&" {printf("%s : AND\n", yytext); return AND; }
"||" {printf("%s : OR\n", yytext); return OR; }
"+" {printf("%s : PLUS\n", yytext); return PLUS; }
"-" {printf("%s : MINU\n", yytext); return MINU; }
"*" {printf("%s : MULT\n", yytext); return MULT; }
"/" {printf("%s : DIV\n", yytext); return DIV; }
"%" {printf("%s : MOD\n", yytext); return MOD; }
"<" {printf("%s : LSS\n", yytext); return LSS; }
"<=" {printf("%s : LEQ\n", yytext); return LEQ; }
">" {printf("%s : GRE\n", yytext); return GRE; }
">=" {printf("%s : GEQ\n", yytext); return GEQ; }
"==" {printf("%s : EQL\n", yytext); return EQL; }
"!=" {printf("%s : NEQ\n", yytext); return NEQ; }
"=" {printf("%s : ASSIGN\n", yytext); return ASSIGN; }
";" {printf("%s : SEMICN\n", yytext); return SEMICN; }
"," {printf("%s : COMMA\n", yytext); return COMMA; }
"(" {printf("%s : LPARENT\n", yytext); return LPARENT; }
")" {printf("%s : RPARENT\n", yytext); return RPARENT; }
"[" {printf("%s : LBRACK\n", yytext); return LBRACK; }
"]" {printf("%s : RBRACK\n", yytext); return RBRACK; }
"{" {printf("%s : LBRACE\n", yytext); return LBRACE; }
"}" {printf("%s : RBRACE\n", yytext); return RBRACE; }

[a-zA-Z][a-zA-Z0-9]* {printf("%s : IDENFR\n", yytext); return IDENFR;}
{digit}+(\.{digit}+)?([eE][+-]?{digit}+)? {printf("%s : INTCON\n", yytext); return INTCON;}
\"[^"]*\"  {printf("%s : STRCON\n", yytext); return STRCON;}

{MultilineComment} {}
{SingleLineComment} {}

[ \n] {}
[ \r\t] {}
. {printf("Lexical error - line %d : %s\n",yylineno,yytext);return LEX_ERR;}

%%



    int main(int argc, char** argv) {
        if(argc > 1) {
            if(!(yyin = fopen(argv[1], "r"))) {
               perror(argv[1]);
               return  1;
            }

           while(yylex()) { };

           fclose(yyin);
        } else printf("No source file given!\n");

        return 0;
        
    }



