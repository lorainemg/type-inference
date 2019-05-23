from src.tools.semantic import SemanticError
from src.tools.semantic import Attribute, Method, Type
from src.tools.semantic import VoidType, ErrorType
from src.tools.semantic import Context
from src.tools.ast import *
from src.visitor import visitor

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