import pytest
from unittest.mock import patch, mock_open
from NL2PLN.utils.checker import check_predicate_logic, HumanCheck
import os

def test_check_predicate_logic_valid():
    test_input = "forall x: (Human(x) -> Mortal(x))"
    expected_output = "(! (x) (=> (Human x) (Mortal x)))"
    
    with patch('os.popen') as mock_popen:
        mock_popen.return_value.read.return_value = expected_output
        result = check_predicate_logic(test_input)
        assert result == expected_output

def test_check_predicate_logic_invalid():
    test_input = "invalid logic"
    
    with patch('os.popen') as mock_popen:
        mock_popen.return_value.read.return_value = "Error: Invalid syntax"
        result = check_predicate_logic(test_input)
        assert result is None

def test_check_predicate_logic_with_fix():
    test_input = "slightly wrong logic"
    fixed_input = "fixed logic"
    expected_output = "(fixed metta)"
    
    def mock_fix(input_str, error):
        return fixed_input
    
    with patch('os.popen') as mock_popen:
        mock_popen.side_effect = [
            type('obj', (), {'read': lambda: "Error: needs fixing"}),
            type('obj', (), {'read': lambda: expected_output})
        ]
        result = check_predicate_logic(test_input, fix_function=mock_fix)
        assert result == expected_output

def test_human_check_approve():
    test_input = "test output"
    test_sentence = "test sentence"
    
    with patch('builtins.input', return_value='y'):
        result = HumanCheck(test_input, test_sentence)
        assert result == test_input

def test_human_check_edit_manual():
    """
    This test requires manual intervention.
    When prompted:
    1. Enter 'n' to indicate you want to edit
    2. Make changes in the editor that opens
    3. Save and close the editor
    4. Verify the output matches your changes
    """
    test_input = "test output"
    test_sentence = "test sentence"
    
    result = HumanCheck(test_input, test_sentence)
    print(f"\nResulting output: {result}")
    
    # Manual verification required
    user_verify = input("\nDoes the output match your edits? (y/n): ")
    assert user_verify.lower() == 'y', "Test failed: Output doesn't match expected edits"
