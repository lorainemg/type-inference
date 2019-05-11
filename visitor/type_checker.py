from tools.semantic import *
from visitor import visitor
from tools.ast import *

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
    def visit(self, node, scope=None):
        scope = Scope()
        for declaration in node.declarations:
            self.visit(declaration, scope.create_child())
        return scope

    
    @visitor.when(ClassDeclarationNode)
    def visit(self, node, scope):
        self.current_type = self._get_type(node.id)
        
        for feat in node.features:
            if isinstance(feat, AttrDeclarationNode):
                self.visit(feat, scope)
        for feat in node.features:
            if isinstance(feat, FuncDeclarationNode):
                self.visit(feat, scope)
    
        
    @visitor.when(AttrDeclarationNode)
    def visit(self, node, scope):
        scope.define_variable(node.id, self._get_type(node.type))

        
    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        # Ver si el método está definido en el padre
        parent = self.current_type.parent 
        pnames = [param[0] for param in node.params]
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
        
        new_scope = scope.create_child()
        # Añadir las variables de argumento
        for pname, ptype in node.params:
            new_scope.define_variable(pname, self._get_type(ptype))
            
        for statement in node.body:
            self.visit(statement, new_scope)
        
        
    def _get_type(self, ntype):
        try:
            return self.context.get_type(ntype)
        except SemanticError as e:
            self.errors.append(e.text)
            return ErrorType()
        
    
    @visitor.when(VarDeclarationNode)
    def visit(self, node, scope):
        if node.id == 'self':
            self.errors.append(SELF_IS_READONLY)

        if scope.is_defined(node.id):
            self.errors.append(LOCAL_ALREADY_DEFINED %(node.id, self.current_method.name))
            return
        
        vtype = self._get_type(node.type)
        var_info = scope.define_variable(node.id, vtype)
        typex = self.visit(node.expr, scope)
        if not typex.conforms_to(vtype):
            self.errors.append(INCOMPATIBLE_TYPES %(vtype.name, typex.name))
        return vtype
            
        
    @visitor.when(AssignNode)
    def visit(self, node, scope):
        if node.id == 'self':
            self.errors.append(SELF_IS_READONLY)
            
        vinfo = scope.find_variable(node.id)
        if vinfo is None:
            self.errors.append(VARIABLE_NOT_DEFINED %(node.id, self.current_method.name))
            vtype = ErrorType()
        else:
            vtype = vinfo.type
            
        typex = self.visit(node.expr, scope)
        if not typex.conforms_to(vtype):
            self.errors.append(INCOMPATIBLE_TYPES %(typex.name, vtype.name))
            
        return typex
            
        
    @visitor.when(CallNode)
    def visit(self, node, scope):
        stype = self.visit(node.obj, scope)
        
        try:
            meth = stype.get_method(node.id)
        except SemanticError as e:
            self.errors.append(e.text)
            return ErrorType()
        
        arg_types = [self.visit(arg, scope) for arg in node.args]
        for atype, ptype in zip(arg_types, meth.param_types):
            if not atype.conforms_to(ptype):
                self.errors.append(INCOMPATIBLE_TYPES % (atype.name, ptype.name))

        return meth.return_type
    
    
    @visitor.when(BinaryNode)
    def visit(self, node, scope):
        ltype = self.visit(node.left, scope)
        rtype = self.visit(node.right, scope)
        if ltype != rtype != IntType():
            self.errors.append(INVALID_OPERATION %(ltype.name, rtype.name))
            return ErrorType()
        return IntType()
    
    
    @visitor.when(ConstantNumNode)
    def visit(self, node, scope):
        return IntType()

    
    @visitor.when(VariableNode)
    def visit(self, node, scope):
        if not scope.is_defined(node.lex):
            self.errors.append(VARIABLE_NOT_DEFINED %(node.id, self.current_method.name))
            return ErrorType()
        return scope.find_variable(node.lex).type
            
    
    @visitor.when(InstantiateNode)
    def visit(self, node, scope):
        return self._get_type(node.lex)
