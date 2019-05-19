from tools.semantic import *
from visitor import visitor
from tools.ast import *
from tools.utils import get_common_basetype

class TypeChecker:
    def __init__(self, context, errors=[]):
        self.context = context
        self.current_type = None
        self.current_method = None
        self.errors = errors
        
    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node, scope):
        scope = scope
        for declaration in node.declarations:
            self.visit(declaration, scope.create_child())

    
    def _get_type(self, ntype):
        try:
            return self.context.get_type(ntype)
        except SemanticError as e:
            self.errors.append(e.text)
            return ErrorType()

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
        if node.expr is not None:
            typee = self.visit(node.expr, scope)
            if not typee.conforms_to(varinfo.type):
                self.errors.append(INCOMPATIBLE_TYPES %(typex.name, vtype.name))
                return ErrorType()
        return self._get_type(node.type)


        
    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        # Ver si el método está definido en el padre
        parent = self.current_type.parent 
        ptypes = [param[1] for param in node.params]

        if parent is not None:
            try:
                old_meth = parent.get_method(node.id)
                if old_meth.return_type.name != node.type:
                    self.errors.append(WRONG_SIGNATURE % (node.id, old_meth.name))
                elif any(type1.name != type2.name for type1, type2 in zip(ptypes, old_meth.param_types)):
                    self.errors.append(WRONG_SIGNATURE % (node.id, old_meth.name))
            except SemanticError:
                pass

        self.current_method = self.current_type.get_method(node.id)

        self.visit(node.body, scope)
        
    
    @visitor.when(VarDeclarationNode)
    def visit(self, node, scope):
        var_info = scope.find_variable(node.id, vtype)
        typex = self.visit(node.expr, scope)
        if not typex.conforms_to(varinfo.type):
            self.errors.append(INCOMPATIBLE_TYPES %(vtype.name, typex.name))
        return vtype
            
        
    @visitor.when(AssignNode)
    def visit(self, node, scope):
        vinfo = scope.find_variable(node.id)
        vtype = vinfo.type
            
        typex = self.visit(node.expr, scope)

        if not typex.conforms_to(vtype):
            self.errors.append(INCOMPATIBLE_TYPES %(typex.name, vtype.name))
            
        return typex
            
        
    @visitor.when(CallNode)
    def visit(self, node, scope):
        stype = self.visit(node.obj, scope)
        meth = stype.get_method(node.id)
        arg_types = [self.visit(arg, scope) for arg in node.args]
        for atype, ptype in zip(arg_types, meth.param_types):
            if not atype.conforms_to(ptype):
                self.errors.append(INCOMPATIBLE_TYPES % (atype.name, ptype.name))

        return meth.return_type
    

    @visitor.when(ConstantNumNode)
    def visit(self, node, scope):
        return IntType()

    
    @visitor.when(VariableNode)
    def visit(self, node, scope):
        return scope.find_variable(node.lex).type
    

    @visitor.when(InstantiateNode)
    def visit(self, node, scope):
        return self._get_type(node.lex)

    @visitor.when(WhileNode)
    def visit(self, node, scope):
        cond = self.visit(node.cond, scope)
        
        if cond.name != 'Bool':
            self.errors.append(INCORRECT_TYPE % (cond.name, 'Bool'))
        
        self.visit(node.expr, scope)


    @visitor.when(ConditionalNode)
    def visit(self, node, scope):
        cond = self.visit(node.cond, scope)

        if cond.name != 'Bool':
            self.errors.append(INCORRECT_TYPE % (cond.name, 'Bool'))
        
        true_type = self.visit(node.stm, scope)
        false_type = self.visit(node.else_stm, scope)

        if true_type.conforms_to(false_type) and false_type.conforms_to(true_type):
            self.errors.append(INCOMPATIBLE_TYPES % (true_type.name, false_type.name))
            return ErrorType()

        return get_common_basetype([true_type, false_type])
        

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

        if not typex.conforms_to(var_info.type):
            self.errros.append(INCOMPATIBLE_TYPES % (typex.name, var_info.type.name))
            return ErrorType()

        return var_info.type

            
    @visitor.when(BinaryArithNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        rtype = self.visit(node.right, scope)
        if ltype != rtype != IntType():
            self.errors.append(INVALID_OPERATION %(ltype.name, rtype.name))
            return ErrorType()

        return IntType()

    @visitor.when(BinaryLogicalNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        rtype = self.visit(node.right, scope)
        if ltype != rtype != IntType():
            self.errors.append(INVALID_OPERATION %(ltype.name, rtype.name))
            return ErrorType()

        return BoolType()


    @visitor.when(UnaryLogicalNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)
        if ltype != BoolType():
            self.errors.append(INVALID_OPERATION %(ltype.name, BoolType().name))
            return ErrorType()

        return BoolType()

    @visitor.when(UnaryArithNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)
        if ltype != IntType():
            self.errors.append(INVALID_OPERATION %(ltype.name, IntType().name))
            return ErrorType()

        return IntType()