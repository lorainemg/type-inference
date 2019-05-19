from tools.semantic import *
from visitor import visitor
from tools.utils import get_common_basetype
from tools.ast import *

class AutoTypeVisitor(object):
    def __init__(self, context, errors=[]):
        self.context =  context
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
        varinfo = scope.find_variable(node.id)
        if varinfo.type.name == 'AUTO_TYPE' and node.expr is not None:
            varinfo.type = self.visit(node.expr, scope)


    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        self.current_method = self.current_type.get_method(node.id)
        
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

        if varinfo.type.name == 'AUTO_TYPE':
            typex = self.visit(node.expr, scope)
            varinfo.type = typex

        return varinfo.type

    @visitor.when(AssignNode)
    def visit(self, node, scope):
        vinfo = scope.find_variable(node.id)  
        typex = self.visit(node.expr, scope)

        if vinfo.type.name == 'AUTO_TYPE':
            vinfo.type = typex
                        
        return typex


    @visitor.when(CallNode)
    def visit(self, node, scope):
        stype = self.visit(node.obj, scope)

        if stype.name == 'AUTO_TYPE':
            raise SemanticError(f'Can\'t infer the type of {node.obj}')    
            
        meth = stype.get_method(node.id)
        return meth.return_type


    @visitor.when(BaseCallNode)
    def visit(self, node, scope):
        stype = self.visit(node.obj, scope)

        if stype.name == 'AUTO_TYPE':
            raise SemanticError(f'Can\'t infer the type of {node.obj}')    
            
        meth = stype.get_method(node.id)
        return meth.return_type
    
    @visitor.when(StaticCallNode)
    def visit(self, node, scope):
        stype = self.current_type
        if stype.name == 'AUTO_TYPE':
            raise SemanticError(f'Can\'t infer the type of {stype.name}')    
            
        meth = stype.get_method(node.id)
        return meth.return_type


    @visitor.when(BinaryArithNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        if isinstance(node.left, VariableNode) and ltype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.left.lex)
            varinfo.type = ltype = IntType()

        rtype = self.visit(node.right, scope)
        if isinstance(node.right, VariableNode) and rtype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.right.lex)
            varinfo.type = ltype = IntType()

        return IntType() if ltype == rtype == IntType() else ErrorType()

    @visitor.when(BinaryLogicalNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        if isinstance(node.left, VariableNode) and ltype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.left.lex)
            varinfo.type = ltype = IntType()

        rtype = self.visit(node.right, scope)
        if isinstance(node.right, VariableNode) and rtype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.right.lex)
            varinfo.type = rtype = IntType()

        return BoolType() if ltype == rtype == IntType() else ErrorType()


    @visitor.when(UnaryLogicalNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)
        if isinstance(node.expr, VariableNode) and ltype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.expr.lex)
            varinfo.type = ltype = BoolType()

        return ltype

    @visitor.when(UnaryArithNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)
        if isinstance(node.expr, VariableNode) and ltype.name == 'AUTO_TYPE':
            varinfo = scope.find_variable(node.expr.lex)
            varinfo.type = IntType()

        return ltype


    @visitor.when(ConstantNumNode)
    def visit(self, node, scope):
        return IntType()

    
    @visitor.when(VariableNode)
    def visit(self, node, scope):
        return scope.find_variable(node.lex).type
            
    
    @visitor.when(InstantiateNode)
    def visit(self, node, scope):
        return self.context.get_type(node.lex)


    @visitor.when(UnaryNode)
    def visit(self, node, scope):
        return self.visit(node.expr)

    @visitor.when(BlockNode)
    def visit(self, node, scope):
        value = None
        for exp in node.expr_list:
            value = self.visit(exp, scope)
        return value

    @visitor.when(LetNode)
    def visit(self, node, scope):
        child_scope = scope.let_dict[node]
        for init in node.init_list:
            self.visit(init, child_scope)
        return self.visit(node.expr, child_scope)
    
    @visitor.when(WhileNode)
    def visit(self, node, scope):
        self.visit(node.cond, scope)
        self.visit(node.expr, scope)
        
        return self.context.get_type('Object')


    @visitor.when(ConditionalNode)
    def visit(self, node, scope):
        self.visit(node.cond, scope)
        true_type = self.visit(node.stm, scope)
        false_type = self.visit(node.else_stm, scope)
        
        if true_type.name == 'AUTO_TYPE' and false_type.name != 'AUTO_TYPE':
            self.assign_auto_type(true_type, node.stm, scope, false_type)
            true_type = false_type
        elif false_type.name == 'AUTO_TYPE' and true_type.name != 'AUTO_TYPE':
            self.assign_auto_type(false_type, node.else_stm, scope, true_type)
            false_type = true_type

        return true_type if true_type.name == false_type.name else ErrorType()


    def assign_auto_type(self, typex, node, scope, other_type):
        if isinstance(node, VarDeclarationNode):
            varinfo = scope.find_variable(node.id)
            varinfo.type = other_type
        elif isinstance(node, (BaseCallNode, CallNode, StaticCallNode)):
            if isinstance(node, BaseCallNode):
                typex = self.context.get_type(node.type)
            elif isinstance(node, StaticCallNode):
                typex = self.current_type
            elif isinstance(node, CallNode):
                typex = self.visit(node.obj, scope)
            meth = typex.get_method(node.id)
            meth.return_type = other_type


    @visitor.when(CaseNode) 
    def visit(self, node, scope):
        type_expr = self.visit(node.expr, scope)

        new_scope = scope.let_dict[node]
        types = []
        for case, c_scope in zip(node.case_list, new_scope.children):
            types.append(self.visit(case, c_scope))

        return get_common_basetype(types)
        

    @visitor.when(OptionNode)
    def visit(self, node, scope):
        var_info = scope.find_variable(node.id)
        typex = self.visit(node.expr)

        if var_info.type.name == 'AUTO_TYPE':
            var_info.type = typex

        return var_info.type