from src.tools.semantic import *
from src.visitor import visitor
from src.tools.ast import *
 
class TypeInference(object):
    def __init__(self, context, errors=[]):
        self.context = context
        self.errors = errors
        self.current_type = None
        self.current_method = None

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node, scope):
        for declaration, child_scope in zip(node.declarations, scope.children):
            self.visit(declaration, child_scope)


    @visitor.when(ClassDeclarationNode)
    def visit(self, node, scope):
        self.current_type = self.context.get_type(node.id)

        fd = [feat for feat in node.features if isinstance(feat, FuncDeclarationNode)]

        for feat in node.features:
            if isinstance(feat, AttrDeclarationNode):
                self.visit(feat, scope)

        for feat, child_scope in zip(fd, scope.children):
            self.visit(feat, child_scope)


    @visitor.when(AttrDeclarationNode)
    def visit(self, node, scope):
        pass

    @visitor.when(AssignNode)
    def visit(self, node, scope):
        return scope.find_variable(node.id).type

    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        self.current_method = self.current_type.get_method(node.id)
        return_type = None
        
        return_type = self.visit(node.body, scope)
        
        for pname, ptype in node.params:
            varinfo = scope.find_variable(pname)
            if varinfo.type.name != ptype:
                self.current_type.change_type(self.current_method, pname, varinfo.type)

        if node.type == 'AUTO_TYPE':
            self.current_method.return_type = return_type 


    @visitor.when(VarDeclarationNode)
    def visit(self, node, scope):
        # _type = self._get_type(node.type)
        varinfo = scope.find_variable(node.id)

        if node.type == 'AUTO_TYPE':
            typex = self.visit(node.expr, scope)
            varinfo.type = typex

        return varinfo.type

    @visitor.when(CallNode)
    def visit(self, node, scope):
        stype = self.visit(node.obj, scope)

        if(stype.name == 'AUTO_TYPE'):
            raise SemanticError(f'Can\'t infer the type of {node.obj}')    
            
        meth = stype.get_method(node.id)
        return meth.return_type


    @visitor.when(BinaryNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        if isinstance(node.left, VariableNode) and ltype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.left.lex)
            varinfo.type = IntType()

        rtype = self.visit(node.right, scope)
        if isinstance(node.right, VariableNode) and rtype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.right.lex)
            varinfo.type = IntType()

        return IntType()


    @visitor.when(ConstantNumNode)
    def visit(self, node, scope):
        return IntType()

    
    @visitor.when(VariableNode)
    def visit(self, node, scope):
        return scope.find_variable(node.lex).type
            
    
    @visitor.when(InstantiateNode)
    def visit(self, node, scope):
        return self.context.get_type(node.lex)