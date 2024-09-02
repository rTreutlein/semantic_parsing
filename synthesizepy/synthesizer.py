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

def match(pattern: Union[Expression, Atom], expression: Union[Expression, Atom]) -> dict:
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

def synthesize(query: Expression, kb: Callable[[], List[Expression]], rb: Callable[[], List[Rule]], depth: int) -> List[Expression]:
    if depth == 0:
        return [axiom for axiom in kb() if match(query, axiom)]

    results = set()

    # Try axioms
    results.update([axiom for axiom in kb() if match(query, axiom)])

    # Try rules
    for rule in rb():
        num_premises = rule.__code__.co_argcount
        
        if num_premises == 0:
            conclusion = rule()
            if match(query, conclusion):
                results.add(conclusion)
        else:
            all_premises = kb()  # Use kb() directly instead of recursive call
            for premise_combination in itertools.combinations(all_premises, num_premises):
                conclusion = rule(*premise_combination)
                if conclusion is not None and match(query, conclusion):
                    results.add(conclusion)

    return list(results)

(= (clean $a)
    (case $a
     (
      ((: (DisjunctionIntroduction $x $y) $t) (empty))
      ((: (ConjunctionIntroduction $x $y) $t) (empty))
      ((: (ConjunctionEliminationLeft $x $y) $t) (empty))
      ((: (ConjunctionEliminationRight $x $y) $t) (empty))
      ($_ $a)
     )
    )
)

(= (fc $kb $rb)
    (let* (($out (inverse-intersect (collapse (synthesize (: $term $type) $kb $rb (S Z))) (collapse (synthesize (: $term $type) $kb $rb Z))))
           ($clean (clean (superpose $out)))
           ($_ (add-atom &self (= ($kb) $clean)))
          )
    $clean
))

def kb() -> List[Expression]:
    return [
        Expression(Atom('Symbol', ':'), (Atom('Symbol', 'a'), Atom('Symbol', 'A'))),
        Expression(Atom('Symbol', ':'), (Atom('Symbol', 'ab'), 
                                         Expression(Atom('Symbol', 'Implication'), 
                                                    (Atom('Symbol', 'A'), Atom('Symbol', 'B'))))),
        Expression(Atom('Symbol', ':'), (Atom('Symbol', 'bc'), 
                                         Expression(Atom('Symbol', 'Implication'), 
                                                    (Atom('Symbol', 'B'), Atom('Symbol', 'C'))))),
    ]

def rb() -> List[Rule]:
    def deduction_rule(p: Expression, q: Expression):
        if not (isinstance(p.arguments[0], Atom) and isinstance(q.arguments[0], Atom)):
            return None
        
        if not (isinstance(p.arguments[1], Expression) and isinstance(q.arguments[1], Expression)):
            return None
        
        if not (p.arguments[1].operator.value == 'Implication' and q.arguments[1].operator.value == 'Implication'):
            return None
        
        if p.arguments[1].arguments[1] != q.arguments[1].arguments[0]:
            return None
        
        result = Expression.create(Atom('Symbol', ':'), [
            Expression.create(Atom('Symbol', 'Deduction'), (p.arguments[0], q.arguments[0])),
            Expression.create(Atom('Symbol', 'Implication'), (p.arguments[1].arguments[0], q.arguments[1].arguments[1]))
        ])
        return result

    return [deduction_rule]

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
    elif isinstance(expr, tuple) and len(expr) == 2:  # Query
        return f"(: {print_sexpr(expr[1])} {print_sexpr(expr[0])})"
    else:
        raise ValueError(f"Unexpected type: {type(expr)}")

def parse_query(query_str: str) -> Expression:
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
    return [item for item in list1 if item not in list2]

if __name__ == "__main__":
    print("\nRunning main program:")
    query = Expression(Atom('Symbol', ':'), [Atom('Variable', '$term'), Atom('Variable', '$type')])
    print("Query:", print_sexpr(query))
    
    print("\nSynthesizing at depth 0:")
    dept0 = synthesize(query, kb, rb, 0)
    print("\nResults at depth 0:")
    printall(dept0)
    
    print("\nSynthesizing at depth 1:")
    dept1 = synthesize(query, kb, rb, 1)
    print("\nResults at depth 1:")
    printall(dept1)
    
    # Remove elements from dept1 that appear in dept0
    unique_dept1 = remove_common_elements(dept1, dept0)
    
    print("\nUnique elements in dept1:")
    printall(unique_dept1)
