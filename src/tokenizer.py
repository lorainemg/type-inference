from .cool_grammar import *
import re

class Token:
    """
    Basic token class.

    Parameters
    ----------
    lex : str
        Token's lexeme.
    token_type : Enum
        Token's type.
    """

    def __init__(self, lex, token_type):
        self.lex = lex
        self.token_type = token_type

    def __str__(self):
        return f'{self.token_type}: {self.lex}'

    def __repr__(self):
        return str(self)

    @property
    def is_valid(self):
        return True

class UnknownToken(Token):
    def __init__(self, lex):
        Token.__init__(self, lex, None)

    def transform_to(self, token_type):
        return Token(self.lex, token_type)

    @property
    def is_valid(self):
        return False

def tokenizer(G, fixed_tokens):
    def decorate(func):
        def tokenize_text(text):
            tokens = []
            lex_string = []
            start = False
            for lex in text.split():
                if not start and lex == '"':
                    start = True
                    lex_string = []
                elif start and lex == '"':
                    start = False
                    pattern = ('[ ]+' + ('[ ]+'.join([w for w in lex_string]))) + ('[ ]+' if len(lex_string) else "")
                    match = re.search(pattern, text).group()
                    token = Token(match[1:-1] if len(match) > 2 else "", string)
                elif start:
                    lex_string.append(lex)
                else:
                    try:
                        token = fixed_tokens[lex]
                    except KeyError:
                        token = UnknownToken(lex)
                        try:
                            token = func(token)
                        except TypeError:
                            pass
                if not start:
                    tokens.append(token)
            tokens.append(Token('$', G.EOF))
            return tokens

        if hasattr(func, '__call__'):
            return tokenize_text
        elif isinstance(func, str):
            return tokenize_text(func)
        else:
            raise TypeError('Argument must be "str" or a callable object.')
    return decorate

fixed_tokens = { t.Name: Token(t.Name, t) for t in G.terminals if t not in { idx, num, string }}


@tokenizer(G, fixed_tokens)
def tokenize_text(token):
    lex = token.lex
    try:
        float(lex)
        return token.transform_to(num)
    except ValueError:
        if invalid_token(lex):
            return UnknownToken(lex)
        else:
            return token.transform_to(idx)

def invalid_token(lex):
    return re.match('[a-zA-Z][a-zA-Z0-9]*', lex) is None

def get_tokens(tokens):
    indent = 0
    pending = []
    res = ''
    for token in tokens:
        pending.append(token)
        if token.token_type in { ocur, ccur, semi }:
            if token.token_type == ccur:
                indent -= 1
            res += '    '*indent + ' '.join(str(t.token_type) for t in pending) + '\n'
            pending.clear()
            if token.token_type == ocur:
                indent += 1
    return res + ' '.join([str(t.token_type) for t in pending])

def get_errors(tokens):
    return [f'Invalid token "{tok.lex}"' for tok in tokens if tok.token_type is None]