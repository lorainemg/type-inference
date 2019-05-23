from src.tools.semantic import *
from src.visitor import visitor
from src.tools.ast import *

class VarCollector:
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
        scope.define_variable('self', self.current_type)
        
        for feat in node.features:
            if isinstance(feat, AttrDeclarationNode):
                self.visit(feat, scope)
        for feat in node.features:
            if isinstance(feat, FuncDeclarationNode):
                self.visit(feat, scope)
    
        
    @visitor.when(AttrDeclarationNode)
    def visit(self, node, scope):
        scope.define_attribute(self.current_type.get_attribute(node.id))

        
    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        # Ver si el método está definido en el padre
        parent = self.current_type.parent 
        pnames = [param[0] for param in node.params]
        ptypes = [param[1] for param in node.params]

        self.current_method = self.current_type.get_method(node.id)
        
        new_scope = scope.create_child()

        # Añadir las variables de argumento
        for pname, ptype in node.params:
            new_scope.define_variable(pname, self._get_type(ptype))
            
        self.visit(node.body, new_scope)
        
        
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
            return
        
        if scope.is_defined(node.id):
            self.errors.append(LOCAL_ALREADY_DEFINED %(node.id, self.current_method.name))        
            return

        vtype = self._get_type(node.type)
        var_info = scope.define_variable(node.id, vtype)
        self.visit(node.expr, scope)

            
        
    @visitor.when(AssignNode)
    def visit(self, node, scope):
        if node.id == 'self':
            self.errors.append(SELF_IS_READONLY)
            
        vinfo = scope.find_variable(node.id)
        if vinfo is None:
            self.errors.append(VARIABLE_NOT_DEFINED %(node.id, self.current_method.name))
            vtype = ErrorType()
            self.scope.define_variable(node.id, vtype)
        else:
            vtype = vinfo.type
            
        self.visit(node.expr, scope)
    
    @visitor.when(BlockNode)
    def visit(self, node, scope):
        for exp in node.expr_list:
            self.visit(exp, scope)
    

    @visitor.when(LetNode)
    def visit(self, node, scope):
        n_scope = scope.create_child()
        scope.let_dict[node] = n_scope
        for init in node.init_list:
            self.visit(init, n_scope)
        
        self.visit(node.expr, n_scope)

    #no necesario
    @visitor.when(BinaryNode)
    def visit(self, node, scope):
        self.visit(node.left, scope)
        self.visit(node.right, scope)

    
    @visitor.when(VariableNode)
    def visit(self, node, scope):
        if not scope.is_defined(node.lex):
            self.errors.append(VARIABLE_NOT_DEFINED %(node.lex, self.current_method.name))
            vinfo = scope.define_variable(node.lex, ErrorType())
        else:
            vinfo = scope.find_variable(node.lex)
        return vinfo.type


    @visitor.when(WhileNode)
    def visit(self, node, scope):
        self.visit(node.cond, scope)
        self.visit(node.expr, scope)

    @visitor.when(ConditionalNode)
    def visit(self, node, scope):
        self.visit(node.cond, scope)
        self.visit(node.stm, scope)
        self.visit(node.else_stm, scope)

    
    @visitor.when(CaseNode)
    def visit(self, node, scope):
        self.visit(node.expr, scope)

        new_scp = scope.create_child()
        scope.let_dict[node] = new_scp

        for case in node.case_list:
            self.visit(case, new_scp.create_child())
        
    @visitor.when(OptionNode)
    def visit(self, node, scope):
        typex = self.context.get_type(node.typex)
        
        self.visit(node.expr, scope)
        scope.define_variable(node.id, typex)

    @visitor.when(CallNode)
    def visit(self, node, scope):
        stype = self.visit(node.obj, scope)
        
        try:
            meth = stype.get_method(node.id)
        except SemanticError as e:
            self.errors.append(e.text)
            stype.methods[node.id] = MethodError(node.id, [], [], ErrorType())
            return ErrorType()
    
    