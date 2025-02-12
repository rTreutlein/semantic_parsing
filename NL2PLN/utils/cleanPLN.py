from typing import Tuple

from NL2PLN.metta.metta_handler import MeTTaHandler

def balance_parentheses(expr: str) -> Tuple[str,float]:
    score = 1.0
    """Balance parentheses in an expression by adding or removing at the end."""
    # Add opening parenthesis if expression starts with colon
    if expr.startswith(':'):
        expr = '(' + expr
        score = 0.5
        
    open_count = expr.count('(')
    close_count = expr.count(')')
    
    if open_count > close_count:
        # Add missing closing parentheses
        return expr + ')' * (open_count - close_count) , score - 0.5
    elif close_count > open_count:
        # Remove only excess closing parentheses from the end
        excess = close_count - open_count
        i = len(expr) - 1
        
        # First verify the end of string contains only closing parentheses
        while i >= 0 and excess > 0:
            if expr[i] != ')':
                # Found non-parenthesis - give up and return original
                return expr , 0
            i -= 1
            excess -= 1
            
        # If we got here, we found enough closing parentheses at the end
        # Now remove the exact number of excess ones
        excess = close_count - open_count
        return expr[:-excess] , score - 0.5
    return expr , score

def removeObjcts(expr: str) -> Tuple[str,float]:
    metta = MeTTaHandler('tmp.json',read_only=True)
    metta.run("!(bind! &kb (new-space))")
    metta.run(f"!(add-atom &kb {expr})")
    res = metta.run_clean("!(match &kb (: $prf (-> (: $po Object) $r)) (: $prf $r))")

    if (len(res) == 0):
        return expr , 1.0

    print(res[0])

    if (res[0] == expr):
        return expr , 1.0
    else:
        return removeObjcts(res[0])[0] , 0.0

def checkSigma(expr: str) -> Tuple[str,float]:
    metta = MeTTaHandler('tmp.json',read_only=True)
    metta.run("!(bind! &kb (new-space))")
    metta.run(f"!(add-atom &kb {expr})")
    res = metta.run_clean("!(match &kb (: $prf (Σ $a $b)) $prf)")

    if (len(res) == 0):
        return expr , 1.0
    else:
        return expr , 0.0

def replaceUnicode(expr: str) -> str:
    expr = expr.replace("\u03a3", "Σ")
    expr = expr.replace("(> ", "(BiggerThan ")
    expr = expr.replace("(< ", "(SmallerThan ")
    return expr

def cleanPLN(expr: str) -> str:
    expr , _ = balance_parentheses(expr)
    expr , _ = removeObjcts(expr)
    expr = replaceUnicode(expr)
    return expr

def cleanAndScore(expr: str) -> Tuple[str,float]:
    expr , s1 = balance_parentheses(expr)
    expr , s2 = removeObjcts(expr)
    expr = replaceUnicode(expr)
    expr , s3 = checkSigma(expr)
    return expr , min(s1,s2,s3)
