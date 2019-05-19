from cool_grammar import *
from visitor.format_visitor import FormatVisitor
from visitor.type_builder import TypeBuilder
from visitor.type_collector import TypeCollector
from visitor.type_checker import TypeChecker
from visitor.type_inference import TypeInference
from visitor.autotype_visitor import AutoTypeVisitor
from visitor.selftype_visitor import SelfTypeVisitor
from visitor.var_collector import VarCollector
from lr1 import LR1Parser, build_LR1_automaton
from tokenizer import tokenize_text, pprint_tokens
from evaluations import evaluate_reverse_parse
import tools.semantic as semantic
# from tools.cmp.tools.parsing import LR1Parser


testcool = '''
class P {
 f ( ) : Int { 1 } ; 
} ;

class C inherits P {
 f ( ) : String { 1 } ;

} ;
'''

testcool1 = '''
class Silly {
    copy ( ) : SELF_TYPE { self } ;
} ;  

class Sally inherits Silly { } ;

class Main {
    x : Sally <- ( new Sally ) . copy ( ) ;
    main ( ) : Sally { x } ;
} ;
'''

testcool2 = '''
class Point {
    x : AUTO_TYPE ;
    y : AUTO_TYPE ;
    
    init ( n : Int , m : Int ) : SELF_TYPE {
    {
        x <- n ;
        y <- m ;
    } } ;

    step ( ) : void { { 
        p . translate ( 1 , 1 ) ;
        let p : AUTO_TYPE <- new Point in {
            step ( p ) ;
        } ;
        } } ;
} ;
'''

testcool3 = '''
class A {
    ackermann ( m : AUTO_TYPE , n : AUTO_TYPE ) : AUTO_TYPE {
        if ( m = 0 ) then n + 1 else
            if ( n = 0 ) then ackermann ( m - 1 , 1 ) else
            ackermann ( m - 1 , ackermann ( m , n - 1 ) )
            fi
        fi
    } ;
} ;
'''

testcool4 = '''
class Main {
    ackermann ( m : AUTO_TYPE , n : AUTO_TYPE ) : AUTO_TYPE {
        if ( m = 0 ) then n + 1 else
            if ( n = 0 ) then ackermann ( m - 1 , 1 ) else
                ackermann ( m - 1 , ackermann ( m , n - 1 ) )
            fi  
        fi
    } ;
} ;
'''

def run_pipeline(G, text):
    print('=================== TEXT ======================')
    print(text)
    print('================== TOKENS =====================')
    tokens = tokenize_text(text)
    pprint_tokens(tokens)
    print('=================== PARSE =====================')
    # automaton = build_LR1_automaton(G)
    # automaton.write_to('test.svg')

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
    print('=============== VAR COLLECTOR ================')
    checker = VarCollector(context, errors)
    scope = checker.visit(ast)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('=============== SELF TYPE ================')
    checker = SelfTypeVisitor(context, errors)
    checker.visit(ast, scope)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('=============== AUTO TYPE ================')
    checker = AutoTypeVisitor(context, errors)
    checker.visit(ast, scope)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('=============== CHECKING TYPES ================')
    checker = TypeChecker(context, errors)
    checker.visit(ast, scope)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('Context:')
    print(context)
    print('Scope:')
    print(scope)
    return ast, errors, context, scope

run_pipeline(G, testcool1)
