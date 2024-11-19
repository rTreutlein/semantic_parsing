import pytest
from NL2PLN.utils.common import extract_logic, parse_lisp_statement

def test_parse_lisp_statement():
    # Test single line statement
    lines = ["(+ 1 2)"]
    assert parse_lisp_statement(lines) == ["(+ 1 2)"]
    
    # Test multi-line statement
    lines = ["(define (factorial n)", "  (if (= n 0)", "    1", "    (* n (factorial (- n 1)))))"]
    assert parse_lisp_statement(lines) == ["(define (factorial n) (if (= n 0) 1 (* n (factorial (- n 1)))))"]
    
    # Test cleanup after final parenthesis
    lines = ["(+ 1 2) ; comment"]
    assert parse_lisp_statement(lines) == ["(+ 1 2)"]

def test_extract_logic():
    # Test basic extraction
    response = """```
From Context:
(: n Int)

Type Definitions:
(: factorial (-> Int Int))

Statements:
(define (factorial n)
  (if (= n 0)
    1
    (* n (factorial (- n 1))))) ; recursive case
```"""
    result = extract_logic(response)
    assert result is not None
    assert result["from_context"] == ["(: n Int)"]
    assert result["type_definitions"] == ["(: factorial (-> Int Int))"]
    assert result["statements"] == ["(define (factorial n) (if (= n 0) 1 (* n (factorial (- n 1)))))"]

    # Test performative response
    response = """```performative
This is a performative statement
```"""
    assert extract_logic(response) == "Performative"

    # Test invalid response
    response = "No code blocks here"
    assert extract_logic(response) is None

    # Test empty statements
    response = """```
Type Definitions:
(: add (-> Int Int Int))

Statements:
```"""
    assert extract_logic(response) is None
