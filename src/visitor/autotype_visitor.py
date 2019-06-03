from src.tools.semantic import *
from src.tools.utils import get_common_basetype
from src.tools.ast import *
from src.visitor import visitor

class AutoTypeVisitor(object):
    def __init__(self, context, errors=[]):
        self.context =  context
        self.errors = errors
        self.current_type = None
        self.current_method = None

    def assign_auto_type(self, typex, node, scope, other_type):
        if isinstance(node, VariableNode):
            varinfo = scope.find_variable(node.lex)
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

    def _get_method(self, typex, name):
        try:
            return typex.get_method(name)
        except SemanticError as e:
            return MethodError(name, [], [], ErrorType())


    def _get_unnassigned(self, scope):
        for var in scope.locals:
            if var.type.name == 'AUTO_TYPE':
                self.errors.append(AUTO_TYPE_ERROR % var.name)
        for child in scope.children:
            self._get_unnassigned(child)


    def _change_args(self, scope, stype, node):
        meth = self._get_method(stype, node.id)
        arg_types = [self.visit(arg, scope) for arg in node.args]
        
        for atype, ptype, pname in zip(arg_types, meth.param_types, meth.param_names):
            if ptype == AutoType() and atype != AutoType():
                scp = scope.get_class_scope().functions[node.id]
                varinfo = scp.find_variable(pname)
                varinfo.type = atype
                self.current_type.change_type(meth, pname, varinfo.type)


    def _check_binary_node(self, node, scope):
        ltype = self.visit(node.left, scope)

        if ltype.name == 'AUTO_TYPE':
            self.assign_auto_type(ltype, node.left, scope, IntType())
            ltype = IntType()
        
        rtype = self.visit(node.right, scope)
        if rtype.name == 'AUTO_TYPE':
            self.assign_auto_type(rtype, node.right, scope, IntType())
            rtype = IntType()
        return ltype, rtype


    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node, scope):
        for declaration, child_scope in zip(node.declarations, scope.children):
            self.visit(declaration, child_scope)
        self._get_unnassigned(scope)


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


    @visitor.when(ConstantBoolNode)
    def visit(self, node, scope):
        return BoolType()


    @visitor.when(ConstantStrNode)
    def visit(self, node, scope):
        return StringType()


    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        self.current_method = self.current_type.get_method(node.id)
        
        return_type = self.visit(node.body, scope)
        
        for pname, ptype in node.params:
            varinfo = scope.find_variable(pname)
            if varinfo.type.name != ptype:
                self.current_type.change_type(self.current_method, pname, varinfo.type)

        if self.current_method.return_type == AutoType():
            self.current_method.return_type = return_type


    @visitor.when(VarDeclarationNode)
    def visit(self, node, scope):
        varinfo = scope.find_variable(node.id)

        if node.expr != None:
            typex = self.visit(node.expr, scope)
            if varinfo.type.name == 'AUTO_TYPE':
                varinfo.type = typex
            return typex

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
     
        self._change_args(scope, stype, node)
        return self._get_method(stype, node.id).return_type


    @visitor.when(BaseCallNode)
    def visit(self, node, scope):
        self.visit(node.obj, scope)
        
        try:
            stype = self.context.get_type(node.id)
            self._change_args(scope, stype, node)
            return self._get_method(stype, node.id).return_type
        except SemanticError:
            return ErrorType()


    @visitor.when(StaticCallNode)
    def visit(self, node, scope):
        stype = self.current_type

        self._change_args(scope, stype, node)
        return self._get_method(stype, node.id).return_type


    @visitor.when(BinaryArithNode)
    def visit(self, node, scope):
        ltype, rtype = self._check_binary_node(node, scope)
        return IntType() if ltype == rtype == IntType() else ErrorType()


    @visitor.when(BinaryLogicalNode)
    def visit(self, node, scope):
        ltype, rtype = self._check_binary_node(node, scope)
        return BoolType() if ltype == rtype == IntType() else ErrorType()


    @visitor.when(UnaryLogicalNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)

        if ltype.name == 'AUTO_TYPE':
            self.assign_auto_type(ltype, node.expr, scope, BoolType())
            ltype = BoolType()
        return ltype if ltype == BoolType() else ErrorType()


    @visitor.when(UnaryArithNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)

        if ltype.name == 'AUTO_TYPE':
            self.assign_auto_type(ltype, node.expr, scope, IntType())
            ltype = IntType()
        return ltype if ltype == IntType() else ErrorType()


    @visitor.when(ConstantNumNode)
    def visit(self, node, scope):
        return IntType()

    
    @visitor.when(VariableNode)
    def visit(self, node, scope):
        return scope.find_variable(node.lex).type
            
    
    @visitor.when(InstantiateNode)
    def visit(self, node, scope):
        return self.context.get_type(node.lex)

    
    @visitor.when(IsVoidNode)
    def visit(self, node, scope):
        self.visit(node.expr, scope)
        return BoolType()

    @visitor.when(BlockNode)
    def visit(self, node, scope):
        value = None
        for exp in node.expr_list:
            value = self.visit(exp, scope)
        return value

    @visitor.when(LetNode)
    def visit(self, node, scope):
        child_scope = scope.expr_dict[node]
        for init in node.init_list:
            self.visit(init, child_scope)
        return self.visit(node.expr, child_scope)
    
    @visitor.when(WhileNode)
    def visit(self, node, scope):
        typex = self.visit(node.cond, scope)
        
        if typex == AutoType():
            self.assign_auto_type(typex, node.cond, scope, BoolType())
        
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

        return get_common_basetype([true_type, false_type])


    @visitor.when(CaseNode) 
    def visit(self, node, scope):
        type_expr = self.visit(node.expr, scope)

        new_scope = scope.expr_dict[node]
        types = []
        for case, c_scope in zip(node.case_list, new_scope.children):
            types.append(self.visit(case, c_scope))

        return get_common_basetype(types)
        

    @visitor.when(OptionNode)
    def visit(self, node, scope):
        var_info = scope.find_variable(node.id)
        typex = self.visit(node.expr, scope)

        if var_info.type.name == 'AUTO_TYPE':
            var_info.type = typex

        return typex