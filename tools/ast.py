class Node:
    pass

class ProgramNode(Node):
    def __init__(self, declarations):
        self.declarations = declarations

class DeclarationNode(Node):
    pass

class ExpressionNode(Node):
    pass

class ClassDeclarationNode(DeclarationNode):
    def __init__(self, idx, features, parent=None):
        self.id = idx
        self.parent = parent
        self.features = features

class FuncDeclarationNode(DeclarationNode):
    def __init__(self, idx, params, return_type, body):
        self.id = idx
        self.params = params
        self.type = return_type
        self.body = body

class AttrDeclarationNode(DeclarationNode):
    def __init__(self, idx, typex):
        self.id = idx
        self.type = typex

class VarDeclarationNode(ExpressionNode):
    def __init__(self, idx, typex, expr):
        self.id = idx
        self.type = typex
        self.expr = expr

class AssignNode(ExpressionNode):
    def __init__(self, idx, expr):
        self.id = idx
        self.expr = expr

class CallNode(ExpressionNode):
    def __init__(self, obj, idx, args):
        self.obj = obj
        self.id = idx
        self.args = args

class BlockNode(ExpressionNode):
    def __init__(self, expr_list):
        self.expr_list = expr_list

class BaseCallNode(ExpressionNode):
    def __init__(self, obj, typex, idx, args):
        self.obj = obj
        self.id = idx
        self.args = args
        self.type = typex


class StaticCallNode(ExpressionNode):
    def __init__(self, idx, args):
        self.id = idx
        self.args = args


class AtomicNode(ExpressionNode):
    def __init__(self, lex):
        self.lex = lex

class BinaryNode(ExpressionNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class WhileNode(ExpressionNode):
    def __init__(self, cond, expr):
        self.cond = cond
        self.expr = expr

class ConditionalNode(ExpressionNode):
    def __init__(self, cond, stm, else_stm):
        self.cond = cond
        self.stm = stm
        self.else_stm = else_stm

class CaseNode(ExpressionNode):
    def __init__(self, expr, case_list):
        self.expr = expr
        self.case_list = case_list

class OptionNode(ExpressionNode):
    def __init__(self, idx, typex, expr):
        self.id = idx
        self.typex = typex
        self.expr = expr

class LetNode(ExpressionNode):
    def __init__(self, init_list, expr):
        self.init_list = init_list
        self.expr = expr

class ConstantNumNode(AtomicNode):
    pass

class VariableNode(AtomicNode):
    pass

class InstantiateNode(AtomicNode):
    pass

class BinaryNotNode(AtomicNode):
    pass

class NotNode(AtomicNode):
    pass

class IsVoidNode(AtomicNode):
    pass

class PlusNode(BinaryNode):
    pass

class MinusNode(BinaryNode):
    pass

class StarNode(BinaryNode):
    pass

class DivNode(BinaryNode):
    pass

class LessNode(BinaryNode):
    pass

class LessEqNode(BinaryNode):
    pass

class EqualNode(BinaryNode):
    pass