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
        self.context.create_type('String')
        self.context.create_type('Int')
        self.context.create_type('Object')
        self.context.create_type('Bool')
        self.context.create_type('AUTO_TYPE')
        self.context.create_type('SELF_TYPE')
        for dec in node.declarations:
            self.visit(dec)

    @visitor.when(ClassDeclarationNode)
    def visit(self, node):
        try:
            self.context.create_type(node.id)
        except SemanticError as e:
            self.errors.append(e.text)