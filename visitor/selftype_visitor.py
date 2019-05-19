from tools.semantic import *
from visitor import visitor
from tools.ast import *

class SelfTypeVisitor(object):
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
        vinfo = scope.find_variable(node.id)
        if node.type == 'SELF_TYPE':
            vinfo.type = self.current_type


    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        self.current_method = self.current_type.get_method(node.id)

        for pname, ptype in node.params:
            if ptype == 'SELF_TYPE':
                varinfo = scope.find_variable(pname)
                varinfo.type = self.current_type
                self.current_type.change_type(self.current_method, pname, self.current_type)

           
        if node.type == 'SELF_TYPE':
            self.current_method.return_type = self.current_type 
         
        self.visit(node.body, scope)


    @visitor.when(VarDeclarationNode)
    def visit(self, node, scope):
        varinfo = scope.find_variable(node.id)

        if node.type == 'SELF_TYPE':
            varinfo.type = self.current_type


    @visitor.when(BlockNode)
    def visit(self, node, scope):
        for exp in node.expr_list:
            self.visit(exp, scope)

    @visitor.when(LetNode)
    def visit(self, node, scope):
        child_scope = scope.let_dict[node]
        for init in node.init_list:
            self.visit(init, child_scope)
        self.visit(node.expr, child_scope)

    @visitor.when(CaseNode) 
    def visit(self, node, scope):
        self.visit(node.expr, scope)

        new_scope = scope.let_dict[node]
        for case, c_scope in zip(node.case_list, new_scope.children):
            self.visit(case, c_scope)
        

    @visitor.when(OptionNode)
    def visit(self, node, scope):
        var_info = scope.find_variable(node.id)
        self.visit(node.expr)

        if var_info.type.name == 'SELF_TYPE':
            var_info.type = self.current_type

        