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
func_call, arg_list  = G.NonTerminals('<func-call> <arg-list>')


# terminals
classx, let, defx, printx = G.Terminals('class let def print')
semi, colon, comma, dot, opar, cpar, ocur, ccur = G.Terminals('; : , . ( ) { }')
equal, plus, minus, star, div = G.Terminals('= + - * /')
idx, num, new = G.Terminals('id int new')


# productions
program %= class_list, lambda h,s: ProgramNode(s[1])

# <class-list>   ???
class_list %= def_class, lambda h,s: [s[1]]
class_list %= def_class + class_list, lambda h,s: [s[1]] + s[2]

# <def-class>    ???
def_class %= classx + idx + ocur + feature_list + ccur, lambda h,s: ClassDeclarationNode(s[2], s[4])
def_class %= classx + idx + colon + idx +  ocur + feature_list + ccur, lambda h,s: ClassDeclarationNode(s[2], s[6], s[4])

# <feature-list> ???
feature_list %= G.Epsilon, lambda h,s: []
feature_list %= def_attr + feature_list, lambda h,s: [s[1]] + s[2]
feature_list %= def_func + feature_list, lambda h,s: [s[1]] + s[2]

# <def-attr>     ???
def_attr %= idx + colon + idx + semi, lambda h,s: AttrDeclarationNode(s[1], s[3])

# <def-func>     ???
def_func %= defx + idx + opar + param_list + cpar + colon + idx + ocur + expr_list + ccur, lambda h,s: FuncDeclarationNode(s[2], s[4], s[7], s[9])

param_list %= param, lambda h,s: [ s[1] ]
param_list %= param + comma + param_list, lambda h,s: [ s[1] ] + s[3]

# <param>        ???
param %= idx + colon + idx, lambda h,s: (s[1], s[3])

# <expr-list>    ???
expr_list %= G.Epsilon, lambda h,s: []
expr_list %= expr + semi + expr_list, lambda h,s: [s[1]] + s[3] 
# <expr>         ???
expr %= let + idx + colon + idx + equal + expr, lambda h,s: VarDeclarationNode(s[2], s[4], s[6])
expr %= let + idx + equal + expr, lambda h,s: AssignNode(s[2], s[4])
expr %= arith, lambda h,s: s[1]
# <arith>        ???
arith %= arith + plus + term, lambda h,s: PlusNode(s[1], s[3])
arith %= arith + minus + term, lambda h,s: MinusNode(s[1], s[3])
arith %= term, lambda h,s: s[1]
# <term>         ???
term %= term + star + factor, lambda h,s: StarNode(s[1], s[3])
term %= term + div + factor, lambda h,s: DivNode(s[1], s[3])
term %= factor, lambda h,s: s[1]
# <factor>       ???
factor %= atom, lambda h,s: s[1]
factor %= opar + expr + cpar, lambda h,s: s[2]
factor %= factor + dot + func_call, lambda h,s: CallNode(s[1], *s[3])
# <atom>         ???
atom %= num, lambda h,s: ConstantNumNode(s[1])
atom %= idx, lambda h,s: VariableNode(s[1])
atom %= new + idx + opar + cpar, lambda h,s: InstantiateNode(s[2]) 
# <func-call>    ???
func_call %= idx + opar + arg_list + cpar, lambda h,s: (s[1], s[3]) 

arg_list %= expr, lambda h,s: [ s[1] ]
arg_list %= expr + comma + arg_list, lambda h,s: [ s[1] ] + s[3]