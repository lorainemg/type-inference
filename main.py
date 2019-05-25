from flask import Flask, render_template, request, redirect


from src.cool_grammar import *
from src.lr1 import LR1Parser, build_LR1_automaton
from src.tokenizer import tokenize_text, get_tokens
from src.evaluations import evaluate_reverse_parse
import src.tools.semantic as semantic
from src.tools.utils import parse_tree_right

from src.visitor.format_visitor import FormatVisitor
from src.visitor.type_builder import TypeBuilder
from src.visitor.type_collector import TypeCollector
from src.visitor.type_checker import TypeChecker
from src.visitor.type_inference import TypeInference
from src.visitor.autotype_visitor import AutoTypeVisitor
from src.visitor.selftype_visitor import SelfTypeVisitor
from src.visitor.var_collector import VarCollector


app = Flask(__name__, )
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/analysis/', methods=['GET', 'POST'])
def analysis():
    text = request.form.get('text')

    # TOKENS
    print(text)
    tokens = tokenize_text(text)
    # PARSER
    parser = LR1Parser(G)
    parse, operations = parser([t.token_type for t in tokens])
    # AST
    ast = evaluate_reverse_parse(parse, operations, tokens)
    # parse_tree_right(parse).write_svg('parse_tree.svg')
    formatter = FormatVisitor()
    tree = formatter.visit(ast)
    # COLLECTING TYPES
    errors = [] 
    collector = TypeCollector(errors)
    collector.visit(ast)
    context = collector.context
    # BUILDING TYPES
    builder = TypeBuilder(context, errors)
    builder.visit(ast)
    # VAR COLLECTOR
    checker = VarCollector(context, errors)
    scope = checker.visit(ast)
    # SELF TYPE
    checker = SelfTypeVisitor(context, errors)
    checker.visit(ast, scope)
    # AUTO TYPE
    checker = AutoTypeVisitor(context, errors)
    checker.visit(ast, scope)
    # CHECKING TYPES
    checker = TypeChecker(context, errors)
    checker.visit(ast, scope)

    return render_template('index.html', 
        text=text,
        tokens=get_tokens(tokens),
        parse=parse,
        tree=formatter.visit(ast),
        context=context,
        errors=errors,
        scope=scope
    )

if __name__ == '__main__':
    app.run(debug=True)