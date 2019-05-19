from tools.grammar import Grammar
from tools.ast import *

# grammar
G = Grammar()

# non-terminals
program = G.NonTerminal('<program>', startSymbol=True)
class_list, def_class = G.NonTerminals('<class-list> <def-class>')
feature_list, def_attr, def_func = G.NonTerminals('<feature-list> <def-attr> <def-func>')
param_list, param, expr_list = G.NonTerminals('<param-list> <param> <expr-list>')
expr, arith, term, factor, atom = G.NonTerminals('<expr> <arith> <term> <factor> <atom>')
func_call, arg_list, case, call, block = G.NonTerminals('<func-call> <arg-list> <case> <call> <block>')
let_assign, let_list, cases_list, op, comp = G.NonTerminals('<let-assign> <let-list> <cases-list> <op> <comp>')
void, bin_no, base_call, dot_call, log_no = G.NonTerminals('<void> <bin-no> <base-call> <dot-call> <log-no>')

# terminals
classx, let, defx, printx, inheritsx = G.Terminals('class let def print inherits')
semi, colon, comma, dot, opar, cpar, ocur, ccur, larrow, arroba, rarrow, nox = G.Terminals('; : , . ( ) { } <- @ => ~')
equal, plus, minus, star, div, less, lesseq = G.Terminals('= + - * / < <=')
idx, num, new, ifx, then, elsex, fi, whilex, loop, pool = G.Terminals('id int new if then else fi while loop pool')
inx, of, esac, isvoid, casex = G.Terminals('in of esac isvoid case')
notx, true, false = G.Terminals('not true false')

# productions
program %= class_list, lambda h,s: ProgramNode(s[1])

# <class-list>   ???
class_list %= def_class, lambda h,s: [s[1]]
class_list %= def_class + class_list, lambda h,s: [s[1]] + s[2]

# <def-class>    ???
def_class %= classx + idx + ocur + feature_list + ccur + semi, lambda h,s: ClassDeclarationNode(s[2], s[4])
def_class %= classx + idx + inheritsx + idx +  ocur + feature_list + ccur + semi, lambda h,s: ClassDeclarationNode(s[2], s[6], s[4])

# <feature-list> ???
feature_list %= G.Epsilon, lambda h,s: []
feature_list %= def_attr + semi + feature_list, lambda h,s: [s[1]] + s[3]
feature_list %= def_func + semi + feature_list, lambda h,s: [s[1]] + s[3]

# <def-attr>     ???
def_attr %= idx + colon + idx, lambda h,s: AttrDeclarationNode(s[1], s[3])
def_attr %= idx + colon + idx + larrow + expr, lambda h,s: AttrDeclarationNode(s[1], s[3], s[5])

# <def-func>     ???
def_func %= idx + opar + param_list + cpar + colon + idx + ocur + expr + ccur, lambda h,s: FuncDeclarationNode(s[1], s[3], s[6], s[8])

param_list %= G.Epsilon, lambda h,s: []
param_list %= param, lambda h,s: [ s[1] ]
param_list %= param + comma + param_list, lambda h,s: [ s[1] ] + s[3]

# <param>        ???
param %= idx + colon + idx, lambda h,s: (s[1], s[3])

# # <expr-list>    ???
# expr_list %= expr, lambda h,s: []
# expr_list %= expr + semi + expr_list, lambda h,s: [s[1]] + s[3] 

# <expr>         ??? 

expr %= let + let_list + inx + expr, lambda h,s: LetNode(s[2], s[4])
expr %= casex + expr + of + cases_list + esac, lambda h,s: CaseNode(s[2], s[4])
expr %= ifx + expr + then + expr + elsex + expr + fi, lambda h,s: ConditionalNode(s[2], s[4], s[6])
expr %= whilex + expr + loop + expr + pool, lambda h,s: WhileNode(s[2], s[4])

expr %= arith, lambda h,s: s[1]

let_list %= let_assign, lambda h,s: [s[1]]
let_list %= let_assign + comma + let_list, lambda h,s: [s[1]] + s[3]

let_assign %= param + larrow + expr, lambda h, s: VarDeclarationNode(s[1][0], s[1][1], s[3])
let_assign %= param, lambda h,s: s[1]

cases_list %= case + semi, lambda h,s: [s[1]] 
cases_list %= case + semi + cases_list, lambda h,s: [s[1]] + s[3]

case %= idx + colon + idx + rarrow + expr, lambda h,s: OptionNode(s[1], s[3], s[4]) 

# <arith>        ???
arith %= idx + larrow + expr, lambda h,s: AssignNode(s[1], s[3])
arith %= log_no, lambda h,s: s[1]

log_no %= notx + comp, lambda h,s: NotNode(s[2])
log_no %= comp, lambda h,s: s[1]

comp %= comp + less + op, lambda h,s: LessNode(s[1], s[3])
comp %= comp + lesseq + op, lambda h,s: LessEqNode(s[1], s[3])
comp %= comp + equal + op, lambda h,s: EqualNode(s[1], s[3])
comp %= op, lambda h,s: s[1]

op %= op + plus + term, lambda h,s: PlusNode(s[1], s[3])
op %= op + minus + term, lambda h,s: MinusNode(s[1], s[3])
op %= term, lambda h,s: s[1]

# <term>         ???
term %= term + star + void, lambda h,s: StarNode(s[1], s[3])
term %= term + div + void, lambda h,s: DivNode(s[1], s[3])
term %= void, lambda h,s: s[1]

void %= isvoid + bin_no, lambda h,s: IsVoidNode(s[2])
void %= bin_no, lambda h,s: s[1]

bin_no %= nox + base_call, lambda h,s: BinaryNotNode(s[2])
bin_no %= base_call, lambda h,s: s[1]

base_call %= dot_call + arroba + idx + dot + func_call, lambda h,s: BaseCallNode(s[1], s[3], *s[5])
base_call %= dot_call, lambda h,s: s[1]

dot_call %= call + dot + func_call, lambda h,s: CallNode(s[1], *s[3])
dot_call %= call, lambda h,s: s[1]

call %= func_call, lambda h,s: StaticCallNode(*s[1])
call %= factor, lambda h,s: s[1]


# <factor>       ???
factor %= atom, lambda h,s: s[1]
factor %= opar + expr + cpar, lambda h,s: s[2]

# <atom>         ???
atom %= num, lambda h,s: ConstantNumNode(s[1])
atom %= idx, lambda h,s: VariableNode(s[1])
atom %= new + idx, lambda h,s: InstantiateNode(s[2])
atom %= ocur + block + ccur, lambda h,s: BlockNode(s[2])

block %= expr + semi, lambda h,s: [s[1]]
block %= expr + semi + block, lambda h,s: [s[1]] + s[3]

# <func-call>    ???
func_call %= idx + opar + arg_list + cpar, lambda h,s: (s[1], s[3]) 

arg_list %= expr, lambda h,s: [ s[1] ]
arg_list %= G.Epsilon, lambda h,s: []
arg_list %= expr + comma + arg_list, lambda h,s: [ s[1] ] + s[3]