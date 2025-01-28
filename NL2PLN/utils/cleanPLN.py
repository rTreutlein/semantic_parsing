
from NL2PLN.metta.metta_handler import MeTTaHandler

def balance_parentheses(expr: str) -> str:
    """Balance parentheses in an expression by adding or removing at the end."""
    # Add opening parenthesis if expression starts with colon
    if expr.startswith(':'):
        expr = '(' + expr
        
    open_count = expr.count('(')
    close_count = expr.count(')')
    
    if open_count > close_count:
        # Add missing closing parentheses
        return expr + ')' * (open_count - close_count)
    elif close_count > open_count:
        # Remove only excess closing parentheses from the end
        excess = close_count - open_count
        i = len(expr) - 1
        
        # First verify the end of string contains only closing parentheses
        while i >= 0 and excess > 0:
            if expr[i] != ')':
                # Found non-parenthesis - give up and return original
                return expr
            i -= 1
            excess -= 1
            
        # If we got here, we found enough closing parentheses at the end
        # Now remove the exact number of excess ones
        excess = close_count - open_count
        return expr[:-excess]
    return expr

def removeObjcts(expr: str) -> str:
    metta = MeTTaHandler('tmp.json',read_only=True)
    metta.run("!(bind! &kb (new-space))")
    metta.run(f"!(add-atom &kb {expr})")
    res = metta.run_clean("!(match &kb (: $prf (-> (: $po Object) $r)) (: $prf $r))")

    if (len(res) == 0):
        return expr

    print(res[0])

    if (res[0] == expr):
        return expr
    else:
        return removeObjcts(res[0])

def replaceUnicode(expr: str) -> str:
    expr = expr.replace("\u03a3", "Σ")
    expr = expr.replace(">", "BiggerThan")
    expr = expr.replace("<", "SmallerThan")
    return expr

def cleanPLN(expr: str) -> str:
    expr = balance_parentheses(expr)
    expr = removeObjcts(expr)
    expr = replaceUnicode(expr)
    return expr
