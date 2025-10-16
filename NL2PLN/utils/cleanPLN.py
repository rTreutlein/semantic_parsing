from typing import Tuple

from hyperon import MeTTa

def balance_parentheses(expr: str) -> Tuple[str,float]:
    score = 1.0
    """Balance parentheses in an expression by adding or removing at the end."""
    # Add opening parenthesis if expression starts with colon
    if expr.startswith(':'):
        expr = '(' + expr
        score = 0.6
        
    open_count = expr.count('(')
    close_count = expr.count(')')
    
    if open_count > close_count:
        # Add missing closing parentheses
        return expr + ')' * (open_count - close_count) , score - 0.4
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
        return expr[:-excess] , score - 0.4
    return expr , score

def checkStmt(expr: str) -> float:
    metta = MeTTa()
    try:
        res1 = metta.run(f"!(unify {expr} (: $123prf (WithTV $123stmt (STV $123s $123c))) (if (== (get-metatype $123prf) Variable) 0.0 1.0) 0.0)")[0][0].get_object().value
        res2 = metta.run(f"!(unify {expr} (: $123prf $123stmt (STV $123s $123c)) (if (== (get-metatype $123prf) Variable) 0.0 1.0) 0.0)")[0][0].get_object().value
        return max(float(res1),float(res2)) 
    except:
     return 0.0

def checkImpl(expr: str) -> float:
    metta = MeTTa()
    try:
        res1 = metta.run(f"!(unify {expr} (: $123prf (WithTV (Implication $a $b) (STV $123s $123c))) (if (== (get-metatype $123prf) Variable) 0.0 1.0) 0.0)")[0][0].get_object().value
        res2 = metta.run(f"!(unify {expr} (: $123prf (Implication $a $b) (STV $123s $123c)) (if (== (get-metatype $123prf) Variable) 0.0 1.0) 0.0)")[0][0].get_object().value
        return max(float(res1),float(res2)) 
    except:
     return 0.0

def checkQuery(expr: str) -> float:
    metta = MeTTa()
    try:
        res1 = metta.run(f"!(unify {expr} (: $123prf (WithTV $123stmt $123tv)) (== (get-metatype $123prf) Variable) 0.0)")[0][0].get_object().value
        res2 = metta.run(f"!(unify {expr} (: $123prf $123stmt $123tv) (if (== (get-metatype $123prf) Variable) 1.0 0.0) 0.0)")[0][0].get_object().value
        return max(float(res1),float(res2))
    except:
     return 0.0

def cleanPLN(expr: str) -> str:
    expr , _ = balance_parentheses(expr)
    return expr

def cleanAndScore(expr: str) -> Tuple[str,float]:
    print(expr)
    expr , s1 = balance_parentheses(expr)
    s2 = checkStmt(expr)
    return expr , min(s1,s2)

if __name__ == "__main__":
    print(cleanAndScore("(: $prf (WithTV (Dog max) (STV 1.0 1.0)))"))
