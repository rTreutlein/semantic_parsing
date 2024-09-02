from typing import List, Tuple, Callable, Any, Union
from dataclasses import dataclass, field
import itertools
import re

@dataclass(frozen=True)
class Atom:
    type: str
    value: Any

    def __eq__(self, other):
        if not isinstance(other, Atom):
            return False
        return self.type == other.type and self.value == other.value

    def __hash__(self):
        return hash((self.type, self.value))

@dataclass(frozen=True)
class Expression:
    operator: Atom
    arguments: Tuple[Union['Expression', Atom], ...] = field(default_factory=tuple)

    def __eq__(self, other):
        if not isinstance(other, Expression):
            return False
        return self.operator == other.operator and self.arguments == other.arguments

    def __hash__(self):
        return hash((self.operator, self.arguments))

    @classmethod
    def create(cls, operator: Atom, arguments: List[Union['Expression', Atom]]):
        return cls(operator, tuple(arguments))

# Type aliases
Rule = Callable[..., Expression]

# Define functions for each rule
def modus_ponens(p, q):
    ptype = p.arguments[1]
    qtype = q.arguments[1]
    if isinstance(p, Expression) and ptype.operator.value == 'ImplicationLink' and ptype.arguments[0] == qtype:
        return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'modus_ponens'), p.arguments[0]), p.arguments[1]))
    return None

def modus_ponens_inheritance(p, q):
    if isinstance(p, Expression) and p.operator.value == 'InheritanceLink' and p.arguments[0] == q.arguments[1]:
        return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'modus_ponens_inheritance'), p.arguments[0]), p.arguments[1]))
    return None

def hypothetical_syllogism(p, q):
    if isinstance(p, Expression) and p.operator.value == 'ImplicationLink' and \
       isinstance(q, Expression) and q.operator.value == 'ImplicationLink' and \
       p.arguments[1] == q.arguments[0]:
        return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'hypothetical_syllogism'), p.arguments[0]), Expression(Atom('Symbol', 'ImplicationLink'), (p.arguments[0], q.arguments[1]))))
    return None

def disjunctive_syllogism_left(p, q):
    if isinstance(p, Expression) and p.operator.value == 'OrLink' and \
       isinstance(q, Expression) and q.operator.value == 'NotLink' and p.arguments[0] == q.arguments[0]:
        return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'disjunctive_syllogism_left'), p.arguments[0]), p.arguments[1]))
    return None

def disjunctive_syllogism_right(p, q):
    if isinstance(p, Expression) and p.operator.value == 'OrLink' and \
       isinstance(q, Expression) and q.operator.value == 'NotLink' and p.arguments[1] == q.arguments[0]:
        return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'disjunctive_syllogism_right'), p.arguments[1]), p.arguments[0]))
    return None

def conjunction_introduction(p, q):
    return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'conjunction_introduction'), p), Expression(Atom('Symbol', 'AndLink'), (p, q))))

def conjunction_elimination_left(p):
    if isinstance(p, Expression) and p.operator.value == 'AndLink':
        return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'conjunction_elimination_left'), p.arguments[0]), p.arguments[0]))
    return None

def conjunction_elimination_right(p):
    if isinstance(p, Expression) and p.operator.value == 'AndLink':
        return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'conjunction_elimination_right'), p.arguments[1]), p.arguments[1]))
    return None

def disjunction_introduction(p, q):
    return Expression(Atom('Symbol', ':'), (Expression(Atom('Symbol', 'disjunction_introduction'), p), Expression(Atom('Symbol', 'OrLink'), (p, q))))

# Add the functions to the rb list
rb = [modus_ponens, modus_ponens_inheritance, hypothetical_syllogism, disjunctive_syllogism_left, disjunctive_syllogism_right, conjunction_introduction, conjunction_elimination_left, conjunction_elimination_right, disjunction_introduction]

def match(pattern: Union[Expression, Atom], expression: Union[Expression, Atom]) -> dict | None:
    """Simple pattern matching function"""
    bindings = {}
    
    def match_recursive(p, e):
        if isinstance(p, Atom) and p.type == 'Variable':
            if p.value in bindings:
                return bindings[p.value] == e
            bindings[p.value] = e
            return True
        if isinstance(p, Atom) and isinstance(e, Atom):
            return p.value == e.value
        if isinstance(p, Expression) and isinstance(e, Expression):
            if p.operator != e.operator or len(p.arguments) != len(e.arguments):
                return False
            return all(match_recursive(pa, ea) for pa, ea in zip(p.arguments, e.arguments))
        return False

    if match_recursive(pattern, expression):
        return bindings
    return None

def synthesize(query: Expression, kb: List[Expression], rb: List[Rule], depth: int) -> List[Expression]:
    if depth == 0:
        return [axiom for axiom in kb if match(query, axiom)]

    results = set()

    # Try axioms
    results.update([axiom for axiom in kb if match(query, axiom)])

    # Try rules
    for rule in rb:
        num_premises = rule.__code__.co_argcount
        
        if num_premises == 0:
            conclusion = rule()
            if match(query, conclusion):
                results.add(conclusion)
        else:
            query = Expression(Atom('Symbol', ':'), (Atom('Variable', '$term'), Atom('Variable', '$type')))
            all_premises = synthesize(query,kb,rb,depth-1)
            for premise_combination in itertools.combinations(all_premises, num_premises):
                conclusion = rule(*premise_combination)
                if conclusion is not None and match(query, conclusion):
                    results.add(conclusion)

    return list(results)

def printall(lst):
    for result in lst:
        print(print_sexpr(result))

def filter_expressions_by_operator(results: List[Expression], operator: str) -> List[Expression]:
    """
    Filter out expressions with a certain operator from a list of Expression results.
    
    :param results: List of Expression results to filter
    :param operator: The operator to filter out
    :return: Filtered list of Expression results
    """
    def has_operator(expr: Union[Expression, Atom], op: str) -> bool:
        if isinstance(expr, Expression):
            return expr.operator.value == op or any(has_operator(arg, op) for arg in expr.arguments)
        return False

    return [result for result in results if not has_operator(result, operator)]

def parse_sexpr(sexpr: str) -> Union[Expression, Atom]:
    """
    Parse an S-expression string into an Expression or Atom.
    
    :param sexpr: The S-expression string to parse
    :return: An Expression or Atom object
    """
    tokens = re.findall(r'\(|\)|[^\s()]+', sexpr)
    
    def parse_tokens(tokens):
        if tokens[0] != '(':
            # It's an atom
            return Atom('Symbol', tokens[0]), tokens[1:]
        
        # It's an expression
        tokens = tokens[1:]  # Skip opening parenthesis
        operator, tokens = parse_tokens(tokens)
        arguments = []
        
        while tokens[0] != ')':
            arg, tokens = parse_tokens(tokens)
            arguments.append(arg)
        
        return Expression.create(operator, arguments), tokens[1:]  # Skip closing parenthesis
    
    result, _ = parse_tokens(tokens)
    return result

def print_sexpr(expr: Union[Expression, Atom]) -> str:
    """
    Convert an Expression, Atom, or Query to an S-expression string.
    
    :param expr: The Expression, Atom, or Query to convert
    :return: An S-expression string
    """
    if isinstance(expr, Atom):
        return expr.value
    elif isinstance(expr, Expression):
        return f"({expr.operator.value} {' '.join(print_sexpr(arg) for arg in expr.arguments)})"
    else:
        raise ValueError(f"Unexpected type: {type(expr)}")

def parse_query(query_str: str) -> Expression | Atom:
    """
    Parse a full query string into an Expression.
    
    :param query_str: The query string to parse
    :return: An Expression object
    """
    return parse_sexpr(query_str)

def remove_common_elements(list1: List[Expression], list2: List[Expression]) -> List[Expression]:
    """
    Remove elements from list1 that appear in list2.
    
    :param list1: The list to remove elements from
    :param list2: The list of elements to remove
    :return: A new list with common elements removed
    """
    # Convert list2 to a set for faster lookup
    set_list2 = set(list2)
    return [item for item in list1 if item not in set_list2]

def clean(a: Expression) -> List[Expression]:
    """
    Clean the given expression by removing certain types of expressions.
    
    :param a: The expression to clean
    :return: A list of cleaned expressions
    """
    if isinstance(a, Expression) and a.operator.value == ':':
        inner_expr = a.arguments[1]
        if isinstance(inner_expr, Expression):
            op = inner_expr.operator.value
            if op in ['DisjunctionIntroduction', 'ConjunctionIntroduction', 
                      'ConjunctionEliminationLeft', 'ConjunctionEliminationRight']:
                return []
    return [a]

def fc(kb: List[Expression], rb: List[Rule]) -> List[Expression]:
    """
    Perform forward chaining on the knowledge base.
    
    :param kb: The current knowledge base
    :param rb: The rule base
    :return: The new knowledge base after forward chaining
    """
    query = Expression(Atom('Symbol', ':'), (Atom('Variable', '$term'), Atom('Variable', '$type')))
    depth_0_results = synthesize(query, kb, rb, 0)
    print("depth0------------------------------")
    printall(depth_0_results)
    depth_1_results = synthesize(query, kb, rb, 1)
    print("depth1------------------------------")
    printall(depth_1_results)
    
    # Remove common elements between depth_1_results and depth_0_results
    new_results = remove_common_elements(depth_1_results, depth_0_results)
    
    # Clean the new results
    cleaned_results = [result for expr in new_results for result in clean(expr)]
    
    return list(set(cleaned_results))
