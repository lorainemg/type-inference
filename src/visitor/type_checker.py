from src.tools.semantic import *
from src.tools.ast import *
from src.visitor import visitor
from src.tools.utils import get_common_basetype

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
        for declaration, new_scope in zip(node.declarations, scope.children):
            self.visit(declaration, new_scope)
        

    
    def _get_type(self, ntype):
        try:
            return self.context.get_type(ntype)
        except SemanticError as e:
            self.errors.append(e.text)
            return ErrorType()


    def _get_method(self, typex, name):
        try:
            return typex.get_method(name)
        except SemanticError as e:
            if typex != ErrorType() and typex != AutoType() :
                self.errors.append(e.text)
            return MethodError(name, [], [], ErrorType())


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
            typex = self.visit(node.expr, scope)
            if not typex.conforms_to(varinfo.type):
                self.errors.append(INCOMPATIBLE_TYPES %(typex.name, varinfo.type.name))
                return ErrorType()
            return typex
        return self._get_type(node.type)


        
    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        parent = self.current_type.parent 
        ptypes = [param[1] for param in node.params]

        self.current_method = method = self.current_type.get_method(node.id)
        if parent is not None:
            try:
                old_meth = parent.get_method(node.id)
                if old_meth.return_type.name != method.return_type.name:
                    if node.type != 'SELF_TYPE':
                        self.errors.append(WRONG_SIGNATURE % (node.id, parent.name))
                elif any(type1.name != type2.name for name, type1, type2 in zip(ptypes, method.param_types, old_meth.param_types)):
                    if name != 'SELF_TYPE':
                        self.errors.append(WRONG_SIGNATURE % (node.id, parent.name))
            except SemanticError:
                pass


        result = self.visit(node.body, scope)
        
        if not result.conforms_to(method.return_type):
            self.errors.append(INCOMPATIBLE_TYPES %(method.return_type.name, result.name))

    
    @visitor.when(VarDeclarationNode)
    def visit(self, node, scope):

        var_info = scope.find_variable(node.id)
        vtype = var_info.type

        if node.expr != None:
            typex = self.visit(node.expr, scope)
            if not typex.conforms_to(var_info.type):
                self.errors.append(INCOMPATIBLE_TYPES %(vtype.name, typex.name))
            return typex
        return vtype
            
        
    @visitor.when(AssignNode)
    def visit(self, node, scope):
        vinfo = scope.find_variable(node.id)
        vtype = vinfo.type
            
        typex = self.visit(node.expr, scope)

        if not typex.conforms_to(vtype):
            self.errors.append(INCOMPATIBLE_TYPES %(vtype.name, typex.name))
        return typex
            

    def _check_args(self, meth, scope, args):
        arg_types = [self.visit(arg, scope) for arg in args]
        
        if len(arg_types) > len(meth.param_types):
            self.errors.append(TOO_MANY_ARGUMENTS % meth.name)
        elif len(arg_types) < len(meth.param_types):
            for arg in meth.param_names[len(arg_types):]:
                self.errors.append(MISSING_PARAMETER % (arg, meth.name))

        for atype, ptype in zip(arg_types, meth.param_types):
            if not atype.conforms_to(ptype):
                self.errors.append(INCOMPATIBLE_TYPES % (ptype.name, atype.name))
        

    @visitor.when(CallNode)
    def visit(self, node, scope):
        stype = self.visit(node.obj, scope)

        meth = self._get_method(stype, node.id)
        self._check_args(meth, scope, node.args)
        return meth.return_type


    @visitor.when(BaseCallNode)
    def visit(self, node, scope):
        obj = self.visit(node.obj, scope)
        typex = self._get_type(node.type)

        if not obj.conforms_to(typex):
            self.errors.append(INCOMPATIBLE_TYPES % (typex.name, obj.name))
            return ErrorType()
        
        meth = self._get_method(typex, node.id)
        self._check_args(meth, scope, node.args)
        return meth.return_type


    @visitor.when(StaticCallNode)
    def visit(self, node, scope):
        typex = self.current_type

        meth = self._get_method(typex, node.id)
        self._check_args(meth, scope, node.args)
        return meth.return_type


    @visitor.when(ConstantNumNode)
    def visit(self, node, scope):
        return IntType()


    @visitor.when(ConstantBoolNode)
    def visit(self, node, scope):
        return BoolType()

   
    @visitor.when(ConstantStrNode)
    def visit(self, node, scope):
        return StringType()


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
        return self.visit(node.expr, scope)


    @visitor.when(IsVoidNode)
    def visit(self, node, scope):
        self.visit(node.expr, scope)
        return BoolType()


    @visitor.when(ConditionalNode)
    def visit(self, node, scope):
        cond = self.visit(node.cond, scope)

        if cond.name != 'Bool':
            self.errors.append(INCORRECT_TYPE % (cond.name, 'Bool'))
        
        true_type = self.visit(node.stm, scope)
        false_type = self.visit(node.else_stm, scope)
      
        if true_type.conforms_to(false_type):
            return false_type
        elif false_type.conforms_to(true_type):
            return true_type
        else:
            self.errors.append(INCOMPATIBLE_TYPES % (false_type.name, true_type.name))
            return ErrorType()
        

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

    
    @visitor.when(CaseNode) 
    def visit(self, node, scope):
        type_expr = self.visit(node.expr, scope)

        new_scope = scope.expr_dict[node]
        types = []
        var_types = []
        for case, c_scope in zip(node.case_list, new_scope.children):
            t, vt = self.visit(case, c_scope)
            types.append(t)
            var_types.append(vt)

        for t in var_types:
            if not type_expr.conforms_to(t):
                self.errors.append(INCOMPATIBLE_TYPES % (t.name, type_expr.name))
                return ErrorType()

        return get_common_basetype(types)
        

    @visitor.when(OptionNode)
    def visit(self, node, scope):
        var_info = scope.find_variable(node.id)
        typex = self.visit(node.expr, scope)
        return typex, var_info.type

            
    @visitor.when(BinaryArithNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        rtype = self.visit(node.right, scope)
        if ltype != rtype != IntType():
            self.errors.append(BOPERATION_NOT_DEFINED %('Arithmetic', ltype.name, rtype.name))
            return ErrorType()
        return IntType()


    @visitor.when(BinaryLogicalNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        rtype = self.visit(node.right, scope)
        if ltype != rtype != IntType():
            self.errors.append(BOPERATION_NOT_DEFINED %('Logical', ltype.name, rtype.name))
            return ErrorType()

        return BoolType()


    @visitor.when(UnaryLogicalNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)
        if ltype != BoolType():
            self.errors.append(UOPERATION_NOT_DEFINED %('Logical', ltype.name))
            return ErrorType()

        return BoolType()



    @visitor.when(UnaryArithNode)
    def visit(self, node, scope):
        ltype = self.visit(node.expr, scope)
        if ltype != IntType():
            self.errors.append(UOPERATION_NOT_DEFINED %('Arithmetic', ltype.name))
            return ErrorType()
        return IntType()