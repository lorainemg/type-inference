from .tools.utils import ContainerSet, compute_firsts, compute_local_first
from .tools.grammar import Item
from .tools.automata import State, multiline_formatter

class ShiftReduceParser:
    SHIFT = 'SHIFT'
    REDUCE = 'REDUCE'
    OK = 'OK'
    
    def __init__(self, G, verbose=False):
        self.G = G
        self.verbose = verbose
        self.action = {}
        self.goto = {}
        self._build_parsing_table()
    
    def _build_parsing_table(self):
        raise NotImplementedError()

    def __call__(self, w):
        stack = [ 0 ]
        cursor = 0
        output = []
        operations = []

        while True:
            state = stack[-1]
            lookahead = w[cursor].token_type
            lex = w[cursor].lex
            if self.verbose: print(stack, w[cursor:])
            
            try:
                action, tag = self.action[state, lookahead]
            except KeyError:
                print(cursor)
                raise Exception(f'Cannot understand the {lookahead} {lex}')
                
            # Your code here!!! (Shift case)
            if action == self.SHIFT:
                stack.append(tag)
                cursor += 1
            
            # Your code here!!! (Reduce case)
            elif action == self.REDUCE:
                prod = tag
                for _ in prod.Right:
                    stack.pop()
                output.append(prod)
                stack.append(self.goto[stack[-1], prod.Left])
            
            # Your code here!!! (OK case)
            elif action == self.OK: 
                stack.pop()
                assert len(stack) == 1 and stack[-1] == 0
                return output, operations
            
            # Your code here!!! (Invalid case)
            else: raise Exception()
            
            operations.append(action)

def expand(item, firsts):
    next_symbol = item.NextSymbol
    if next_symbol is None or not next_symbol.IsNonTerminal:
        return []
    
    lookaheads = ContainerSet()
    
    for prev in item.Preview():
        lookaheads.update(compute_local_first(firsts, prev))            
    
    assert not lookaheads.contains_epsilon
        
    return [Item(prod, 0, lookaheads) for prod in next_symbol.productions]

def compress(items):
    centers = {}

    for item in items:
        center = item.Center()
        try:
            lookaheads = centers[center]
        except KeyError:
            centers[center] = lookaheads = set()
        lookaheads.update(item.lookaheads)
    
    return { Item(x.production, x.pos, set(lookahead)) for x, lookahead in centers.items() }

def closure_lr1(items, firsts):
    closure = ContainerSet(*items)
    
    changed = True
    while changed:
        changed = False
        
        new_items = ContainerSet()
        for item in closure:
            new_items.extend(expand(item, firsts))

        changed = closure.update(new_items)
        
    return compress(closure)

def goto_lr1(items, symbol, firsts=None, just_kernel=False):
    assert just_kernel or firsts is not None, '`firsts` must be provided if `just_kernel=False`'
    items = frozenset(item.NextItem() for item in items if item.NextSymbol == symbol)
    return items if just_kernel else closure_lr1(items, firsts)

def build_LR1_automaton(G):
    assert len(G.startSymbol.productions) == 1, 'Grammar must be augmented'
    
    firsts = compute_firsts(G)
    firsts[G.EOF] = ContainerSet(G.EOF)
    
    start_production = G.startSymbol.productions[0]
    start_item = Item(start_production, 0, lookaheads=(G.EOF,))
    start = frozenset([start_item])
    
    closure = closure_lr1(start, firsts)
    automaton = State(frozenset(closure), True)
    
    pending = [ start ]
    visited = { start: automaton }
    
    while pending:
        current = pending.pop()
        current_state = visited[current]
        
        closure = closure_lr1(current, firsts)
        for symbol in G.terminals + G.nonTerminals:
            new_items = frozenset(goto_lr1(closure, symbol, just_kernel=True))
            if not new_items:
                continue
            try:
                next_state = visited[new_items]
            except KeyError:
                pending.append(new_items)
                next_state = State(frozenset(closure_lr1(new_items, firsts)), True)
                visited[new_items] = next_state 
            current_state.add_transition(symbol.Name, next_state)
    
    # automaton.set_formatter(multiline_formatter)
    return automaton

class LR1Parser(ShiftReduceParser):
    def _build_parsing_table(self):
        G = self.G.AugmentedGrammar(True)
        
        automaton = build_LR1_automaton(G)
        # automaton.write_to('test.svg')

        for i, node in enumerate(automaton):
            if self.verbose: print(i, '\t', '\n\t '.join(str(x) for x in node.state), '\n')
            node.idx = i

        for node in automaton:
            idx = node.idx
            for item in node.state:
                # Your code here!!!
                prod = item.production
                if item.IsReduceItem:
                    if prod.Left == G.startSymbol:
                        self._register(self.action, (idx, G.EOF), (self.OK, 0))
                    else:
                        for symbol in item.lookaheads:
                            self._register(self.action, (idx, symbol), (self.REDUCE, prod))
                else:
                    next_symb = item.NextSymbol
                    if next_symb.IsTerminal:
                        self._register(self.action, (idx, next_symb), (self.SHIFT, node.transitions[next_symb.Name][0].idx))
                    else:
                        self._register(self.goto, (idx, next_symb), node.transitions[next_symb.Name][0].idx)
    
        
    @staticmethod
    def _register(table, key, value):
        assert key not in table or table[key] == value, 'Shift-Reduce or Reduce-Reduce conflict!!!'
        table[key] = value