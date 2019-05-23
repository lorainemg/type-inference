import itertools
import pydot
import uuid

class ContainerSet:
    def __init__(self, *values, contains_epsilon=False):
        self.set = set(values)
        self.contains_epsilon = contains_epsilon

    def add(self, value):
        n = len(self.set)
        self.set.add(value)
        return n != len(self.set)

    def extend(self, values):
        change = False
        for value in values:
            change |= self.add(value)
        return change

    def set_epsilon(self, value=True):
        last = self.contains_epsilon
        self.contains_epsilon = value
        return last != self.contains_epsilon

    def update(self, other):
        n = len(self.set)
        self.set.update(other.set)
        return n != len(self.set)

    def epsilon_update(self, other):
        return self.set_epsilon(self.contains_epsilon | other.contains_epsilon)

    def hard_update(self, other):
        return self.update(other) | self.epsilon_update(other)

    def find_match(self, match):
        for item in self.set:
            if item == match:
                return item
        return None

    def __len__(self):
        return len(self.set) + int(self.contains_epsilon)

    def __str__(self):
        return '%s-%s' % (str(self.set), self.contains_epsilon)

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.set)

    def __nonzero__(self):
        return len(self) > 0

    def __eq__(self, other):
        if isinstance(other, set):
            return self.set == other
        return isinstance(other, ContainerSet) and self.set == other.set and self.contains_epsilon == other.contains_epsilon

def compute_local_first(firsts, alpha):
    first_alpha = ContainerSet()
    
    try:
        alpha_is_epsilon = alpha.IsEpsilon
    except:
        alpha_is_epsilon = False
    
    if alpha_is_epsilon:
        first_alpha.set_epsilon()
    else:
        all_epsilon = True
        for x in alpha:
            first_alpha.update(firsts[x])
            
            if not firsts[x].contains_epsilon:
                all_epsilon = False
                break
        #else: si el break no se ejecutó en un ciclo
        else:
            first_alpha.set_epsilon()
                    
    return first_alpha

def compute_firsts(G):
    firsts = {}
    change = True
    
    for terminal in G.terminals:
        firsts[terminal] = ContainerSet(terminal)
        
    for nonterminal in G.nonTerminals:
        firsts[nonterminal] = ContainerSet()
    
    while change:
        change = False
        
        for production in G.Productions:
            X = production.Left
            alpha = production.Right
            
            first_X = firsts[X]
                
            try:
                first_alpha = firsts[alpha]
            except:
                first_alpha = firsts[alpha] = ContainerSet()

            local_first = compute_local_first(firsts, alpha)
            
            change |= first_alpha.hard_update(local_first)
            change |= first_X.hard_update(local_first)
                    
    return firsts

def path_to_objet(typex):
    path = []
    c_type = typex

    while c_type:
        path.append(c_type)
        c_type = c_type.parent

    path.reverse()
    return path

def get_common_basetype(types):
    paths = [path_to_objet(typex) for typex in types]
    tuples = zip(*paths)

    for i, t in enumerate(tuples):
        gr = itertools.groupby(t)
        if len(list(gr)) > 1:
            return paths[0][i-1]

def parse_tree_right(productions):
    
    def parse(G, productions, i):
        left, right = productions[i]
        
        node = pydot.Node(uuid.uuid4().hex, label=left.Name, shape ="circle", style="filled", fillcolor="white") 
        G.add_node(node)

        for symbol in reversed(right):
            if symbol.IsTerminal:
                child = pydot.Node(uuid.uuid4().hex, label=symbol.Name, shape="circle", style="filled", fillcolor="white")
                G.add_node(child)
                G.add_edge(pydot.Edge(node, child))
            else:
                child, i = parse(G, productions, i + 1)
                G.add_edge(pydot.Edge(node, child))

        if right.IsEpsilon:
            child = pydot.Node(uuid.uuid4().hex, label='ε', shape="circle", style="filled", fillcolor="white")
            G.add_node(child)
            G.add_edge(pydot.Edge(node, child)) 
        return node, i
    
    productions.reverse()
    G = pydot.Dot(graph_type='digraph')
    node, i = parse(G, productions, 0)
   
    return G
