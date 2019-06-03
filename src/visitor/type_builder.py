from src.tools.semantic import SemanticError
from src.tools.semantic import Attribute, Method, Type
from src.tools.semantic import VoidType, ErrorType
from src.tools.semantic import Context
from src.visitor import visitor 
from src.tools.ast import *

class TypeBuilder:
    def __init__(self, context, errors=[]):
        self.context = context
        self.current_type = None
        self.errors = errors
    
    @visitor.on('node')
    def visit(self, node):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node):
        for dec in node.declarations:
            self.visit(dec)
    


    @visitor.when(ClassDeclarationNode)
    def visit(self, node):
        try:
            self.current_type = self.context.get_type(node.id)
        except SemanticError as e:
            self.current_type = ErrorType()
            self.errors.append(e.text)
        
        if node.parent is not None:
            try:
                parent = self.context.get_type(node.parent)
                current = parent
                while current is not None:
                    if current.name == self.current_type.name:
                        raise SemanticError(CIRCULAR_DEPENDENCY %(parent.name, self.current_type.name))
                    current = current.parent
            except SemanticError as e:
                parent = ErrorType()
                self.errors.append(e.text)
            self.current_type.set_parent(parent)

        
        for feature in node.features:
            self.visit(feature)
    

    @visitor.when(FuncDeclarationNode)
    def visit(self, node):
        args_names = []
        args_types = []
        for name, type_ in node.params:
            try:
                args_names.append(name)
                args_types.append(self.context.get_type(type_))
            except SemanticError as e:
                args_types.append(ErrorType())
                self.errors.append(e.text)
        
        try:
            return_type = self.context.get_type(node.type)
        except SemanticError as e:
            return_type = ErrorType()
            self.errors.append(e.text)
    
        try:
            self.current_type.define_method(node.id, args_names, args_types, return_type)
        except SemanticError as e:
            self.errors.append(e.text)
    
    @visitor.when(AttrDeclarationNode)
    def visit(self, node):
        try:
            attr_type = self.context.get_type(node.type)
        except SemanticError as e:
            attr_type = ErrorType()
            self.errors.append(e.text)
        
        try:
            self.current_type.define_attribute(node.id, attr_type)
        except SemanticError as e:
            self.errors.append(e.text)