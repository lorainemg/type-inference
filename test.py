from cool_grammar import *
from visitor.format_visitor import FormatVisitor
from visitor.type_builder import TypeBuilder
from visitor.type_collector import TypeCollector
from visitor.type_checker import TypeChecker
from visitor.type_inference import TypeInference
from lr1 import LR1Parser
from tokenizer import tokenize_text, pprint_tokens
from evaluations import evaluate_reverse_parse

text = '''
class A {
    a : int ;
    def suma ( a : int , b : int ) : int {
        a + b ;
    }
    b : int ;
}

class B : A {
    c : A ;
    def f ( d : int , a : A ) : void {
        let f : int = 8 ;
        let c = new A ( ) . suma ( 5 , f ) ;
        c ;
    }
}
'''

text1 = '''
class A {
    a : Z ;
    def suma ( a : int , b : B ) : int {
        a + b ;
    }
    b : int ;
    c : C ;
}

class B : A {
    c : A ;
    def f ( d : int , a : A ) : void {
        let f : int = 8 ;
        let c = new A ( ) . suma ( 5 , f ) ;
        c ;
    }
    z : int ;
    z : A ;
}

class C : Z {
}

class D : A {
    def suma ( a : int , d : B ) : int {
        d ;
    }
}

class E : A {
    def suma ( a : A , b : B ) : C {
        a ;
    }
}

class F : B {
    def f ( d : int , a : A ) : void {
        a ;
    }
}
'''

text2 = '''
class A {
    a : int ;
    def suma ( a : int , b : int ) : int {
        a + b ;
    }
    b : int ;
}

class B : A {
    c : int ;
    def f ( d : int , a : A ) : void {
        let f : int = 8 ;
        let c = new A ( ) . suma ( 5 , f ) ;
        c ;
    }
}
'''

text3 = '''
class A {
    a : int ;
    def suma ( a : int , b : int ) : int {
        a + b + new B ( ) ;
    }
    b : int ;
}

class B : A {
    c : A ;
    def f ( d : int , a : A ) : void {
        let f : int = 8 ;
        let c = new A ( ) . suma ( 5 , f ) ;
        d ;        
    }
}
'''

test1 = '''
class Main {
    def main ( a : int ) : AUTO_TYPE {
        let x : AUTO_TYPE = 3 + 2 ;
    }
}
'''

test2 = '''
class Point {
    x : AUTO_TYPE ;
    y : AUTO_TYPE ;

    def init ( n : int , m : int ) : AUTO_TYPE {
        let x = n ;
        let y = m ;
    }
}
'''

test3 = '''
class Main { 
    def succ ( n : AUTO_TYPE ) : AUTO_TYPE { 
        n + 1 ; 
    } 
}
'''

def run_pipeline(G, text):
    print('=================== TEXT ======================')
    print(text)
    print('================== TOKENS =====================')
    tokens = tokenize_text(text)
    pprint_tokens(tokens)
    print('=================== PARSE =====================')
    parser = LR1Parser(G)
    parse, operations = parser([t.token_type for t in tokens])
    print('\n'.join(repr(x) for x in parse))
    print('==================== AST ======================')
    ast = evaluate_reverse_parse(parse, operations, tokens)
    formatter = FormatVisitor()
    tree = formatter.visit(ast)
    print(tree)
    print('============== COLLECTING TYPES ===============')
    errors = []
    collector = TypeCollector(errors)
    collector.visit(ast)
    context = collector.context
    print('Errors:', errors)
    print('Context:')
    print(context)
    print('=============== BUILDING TYPES ================')
    builder = TypeBuilder(context, errors)
    builder.visit(ast)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('Context:')
    print(context)
    print('=============== CHECKING TYPES ================')
    checker = TypeChecker(context, errors)
    scope = checker.visit(ast)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('=============== INFERING TYPES ================')
    inferer = TypeInference(context, errors)
    inferer.visit(ast, scope)
    for error in errors:
        print('\t', error)
    print(']')
    print('Context:')
    print(context)
    print('Scope:')
    print(scope)
    return ast, errors, context, scope

ast, errors, context, scope = run_pipeline(G, test3)