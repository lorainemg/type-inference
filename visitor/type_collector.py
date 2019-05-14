from tools.semantic import SemanticError
from tools.semantic import Attribute, Method, Type
from tools.semantic import VoidType, ErrorType
from tools.semantic import Context
from visitor import visitor
from tools.ast import *

class TypeCollector(object):
    def __init__(self, errors=[]):
        self.context = None
        self.errors = errors
    
    @visitor.on('node')
    def visit(self, node):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node):
        self.context = Context()
        self.context.create_type('int')
        self.context.create_type('AUTO_TYPE')
        for dec in node.declarations:
            self.visit(dec)

    @visitor.when(ClassDeclarationNode)
    def visit(self, node):
        try:
            self.context.create_type(node.id)
        except SemanticError as e:
            self.errors.append(e.text)