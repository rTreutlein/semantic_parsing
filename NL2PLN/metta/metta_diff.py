#!/usr/bin/env python3
"""
MeTTa Log Diff Tool

Compares two MeTTa interpreter logs using alpha equivalence.
Ignores variable names and line order, focusing on structural differences.
"""

import argparse
import re
import sys
from collections import Counter


def normalize_number(token):
    """
    Normalize numeric tokens to handle equivalent representations.
    E.g., 9.2e-05 -> 9.2e-5, 1.0 -> 1, 1 -> 1 (consistent formatting)
    Also rounds to 5 decimal places to handle small rounding differences.
    """
    try:
        # Try to parse as float first
        num = float(token)
        
        # Check if it's actually an integer value
        if num.is_integer():
            return str(int(num))  # Convert 1.0 -> 1
        else:
            # Round to 5 decimal places to handle small rounding differences
            # This treats 0.998228 and 0.998229 as equivalent
            rounded = round(num, 5)
            if rounded.is_integer():
                return str(int(rounded))
            else:
                # Use 'g' format for consistent representation of floats
                return f"{rounded:g}"
    except ValueError:
        # Not a number, return as-is
        return token


def tokenize_metta_line(line):
    """
    Tokenize a MeTTa line into tokens, preserving structure.
    Returns a list of tokens where variables are marked as such.
    """
    # Simple tokenizer for MeTTa-like syntax
    # Handles parentheses, variables ($...), and other tokens
    tokens = []
    i = 0
    cpu_function_mode = False
    cpu_function_added = False
    
    while i < len(line):
        char = line[i]
        
        if char.isspace():
            i += 1
            continue
        elif char in '()':
            tokens.append(char)
            i += 1
            # Reset CPU function mode when we hit a closing paren
            if char == ')':
                cpu_function_mode = False
                cpu_function_added = False
        elif char == '$':
            # Extract variable name
            j = i + 1
            while j < len(line) and line[j] not in ' ()':
                j += 1
            tokens.append(('VAR', line[i:j]))
            i = j
            # Reset CPU function mode after processing a variable
            if cpu_function_mode:
                cpu_function_mode = False
                cpu_function_added = False
        else:
            # Extract other tokens (atoms, numbers, etc.)
            j = i
            while j < len(line) and not line[j].isspace() and line[j] not in '()$':
                j += 1
            if j > i:
                token = line[i:j]
                
                if token == 'CPU':
                    # Add CPU and enter function normalization mode
                    tokens.append(token)
                    cpu_function_mode = True
                    cpu_function_added = False
                elif cpu_function_mode:
                    # We're in CPU function mode - skip all function-related tokens
                    if not cpu_function_added:
                        # Add the normalized function token only once
                        tokens.append('CPU_FUNCTION')
                        cpu_function_added = True
                    # Skip this token (it's part of the function representation)
                    # Continue until we hit something that's not function-related
                    if not (token.startswith('<') or token == 'function' or token.endswith('>') or 
                           'built-in' in token or '.' in token or token in ['sqrt', 'sin', 'cos', 'tan']):
                        # This token is not part of the function, process it normally
                        normalized_token = normalize_number(token)
                        tokens.append(normalized_token)
                        cpu_function_mode = False
                        cpu_function_added = False
                else:
                    # Normal token processing
                    normalized_token = normalize_number(token)
                    tokens.append(normalized_token)
                
                i = j
            else:
                i += 1
    
    return tokens


def parse_expression(tokens, start=0):
    """
    Parse tokens into a structured expression tree.
    Returns (expression, next_index)
    """
    if start >= len(tokens):
        return None, start
    
    token = tokens[start]
    
    if token == '(':
        # Parse list/expression
        expr = []
        i = start + 1
        while i < len(tokens) and tokens[i] != ')':
            sub_expr, i = parse_expression(tokens, i)
            if sub_expr is not None:
                expr.append(sub_expr)
        if i < len(tokens) and tokens[i] == ')':
            i += 1
        return expr, i
    else:
        # Atomic token
        return token, start + 1


def normalize_commutative_ops(expr):
    """
    Normalize commutative operations by sorting their arguments.
    """
    if not isinstance(expr, list) or len(expr) == 0:
        return expr
    
    # Recursively normalize sub-expressions first
    normalized_expr = [normalize_commutative_ops(item) for item in expr]
    
    # Check if this is a commutative operation
    if len(normalized_expr) >= 3:
        op = normalized_expr[0]
        if op in ['revision', 'And', 'Or', 'conjunction']:  # Add more as needed
            # Sort arguments (skip the operator)
            sorted_args = sorted(normalized_expr[1:], key=str)
            return [op] + sorted_args
    
    return normalized_expr


def normalize_proof_steps(expr):
    """
    Normalize proof step ordering in |- expressions.
    """
    if not isinstance(expr, list) or len(expr) == 0:
        return expr
    
    # Recursively process sub-expressions first
    normalized_expr = [normalize_proof_steps(item) for item in expr]
    
    # Check if this is a |- (turnstile) expression
    if len(normalized_expr) >= 3 and normalized_expr[1] == '|-':
        # The structure is typically: ( ( ) |- ( step1 step2 step3 ... ) )
        if len(normalized_expr) >= 3 and isinstance(normalized_expr[2], list):
            # Sort the proof steps
            proof_steps = normalized_expr[2]
            if isinstance(proof_steps, list):
                sorted_steps = sorted(proof_steps, key=str)
                return [normalized_expr[0], '|-', sorted_steps]
    
    return normalized_expr


def normalize_to_alpha_equivalent(tokens):
    """
    Convert tokens to alpha-equivalent form by:
    1. Replacing all variables with canonical names
    2. Normalizing commutative operations
    3. Normalizing proof step ordering
    """
    # First, parse into expression tree
    expr, _ = parse_expression(tokens)
    if expr is None:
        return tuple(tokens)
    
    # Apply structural normalizations
    expr = normalize_commutative_ops(expr)
    expr = normalize_proof_steps(expr)
    
    # Flatten back to tokens for variable normalization
    def flatten_expr(e):
        if isinstance(e, list):
            result = ['(']
            for item in e:
                result.extend(flatten_expr(item))
            result.append(')')
            return result
        else:
            return [e]
    
    flattened = flatten_expr(expr)
    
    # Now do variable normalization
    var_mapping = {}
    var_counter = 0
    normalized = []
    
    for token in flattened:
        if isinstance(token, tuple) and token[0] == 'VAR':
            var_name = token[1]
            if var_name not in var_mapping:
                var_mapping[var_name] = f'$v{var_counter}'
                var_counter += 1
            normalized.append(var_mapping[var_name])
        else:
            normalized.append(token)
    
    return tuple(normalized)  # Use tuple for hashability


def process_line(line):
    """
    Process a single line into its alpha-equivalent canonical form.
    Returns None if the line is empty or invalid.
    """
    stripped = line.strip()
    if not stripped:
        return None
    
    try:
        tokens = tokenize_metta_line(stripped)
        if not tokens:
            return None
        return normalize_to_alpha_equivalent(tokens)
    except Exception:
        # If parsing fails, treat as opaque string
        return ('UNPARSED', stripped)


def load_and_normalize_log(filepath):
    """Load a log file and return normalized lines with metadata."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)
    
    processed_lines = []
    for line_num, line in enumerate(lines, 1):
        normalized = process_line(line)
        if normalized is not None:
            processed_lines.append((normalized, line_num, line.strip()))
    
    return processed_lines


def format_normalized_line(normalized_tokens):
    """Convert normalized tokens back to readable string."""
    if isinstance(normalized_tokens, tuple) and len(normalized_tokens) > 0:
        if normalized_tokens[0] == 'UNPARSED':
            return normalized_tokens[1]
        else:
            return ' '.join(str(token) for token in normalized_tokens)
    return str(normalized_tokens)


def main():
    parser = argparse.ArgumentParser(
        description="Compare two MeTTa interpreter logs using alpha equivalence"
    )
    parser.add_argument("log1", help="First log file")
    parser.add_argument("log2", help="Second log file")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Show original lines alongside normalized ones")
    parser.add_argument("--show-examples", action="store_true",
                       help="Show example original lines for each unique normalized form")
    
    args = parser.parse_args()
    
    print(f"Comparing {args.log1} and {args.log2}")
    print("=" * 50)
    
    # Load and normalize both logs
    log1_lines = load_and_normalize_log(args.log1)
    log2_lines = load_and_normalize_log(args.log2)
    
    # Create sets of normalized lines for comparison
    log1_normalized = {line[0] for line in log1_lines}
    log2_normalized = {line[0] for line in log2_lines}
    
    # Find differences
    only_in_log1 = log1_normalized - log2_normalized
    only_in_log2 = log2_normalized - log1_normalized
    
    # Count occurrences
    log1_counts = Counter(line[0] for line in log1_lines)
    log2_counts = Counter(line[0] for line in log2_lines)
    
    # Create mappings from normalized to original lines
    log1_examples = {}
    log2_examples = {}
    for norm, line_num, orig in log1_lines:
        if norm not in log1_examples:
            log1_examples[norm] = []
        log1_examples[norm].append(orig)
    
    for norm, line_num, orig in log2_lines:
        if norm not in log2_examples:
            log2_examples[norm] = []
        log2_examples[norm].append(orig)
    
    # Report results
    print(f"Log 1: {len(log1_lines)} lines ({len(log1_normalized)} unique alpha-equivalent forms)")
    print(f"Log 2: {len(log2_lines)} lines ({len(log2_normalized)} unique alpha-equivalent forms)")
    print(f"Common alpha-equivalent forms: {len(log1_normalized & log2_normalized)}")
    print()
    
    if only_in_log1:
        print(f"Alpha-equivalent forms only in {args.log1} ({len(only_in_log1)}):")
        print("-" * 50)
        for norm_line in sorted(only_in_log1, key=lambda x: format_normalized_line(x)):
            count = log1_counts[norm_line]
            count_str = f" (appears {count}x)" if count > 1 else ""
            print(f"  {format_normalized_line(norm_line)}{count_str}")
            
            if args.show_examples:
                examples = list(set(log1_examples[norm_line]))[:3]  # Show up to 3 unique examples
                for example in examples:
                    print(f"    Example: {example}")
                if len(log1_examples[norm_line]) > 3:
                    print(f"    ... and {len(set(log1_examples[norm_line])) - 3} more variants")
        print()
    
    if only_in_log2:
        print(f"Alpha-equivalent forms only in {args.log2} ({len(only_in_log2)}):")
        print("-" * 50)
        for norm_line in sorted(only_in_log2, key=lambda x: format_normalized_line(x)):
            count = log2_counts[norm_line]
            count_str = f" (appears {count}x)" if count > 1 else ""
            print(f"  {format_normalized_line(norm_line)}{count_str}")
            
            if args.show_examples:
                examples = list(set(log2_examples[norm_line]))[:3]  # Show up to 3 unique examples
                for example in examples:
                    print(f"    Example: {example}")
                if len(log2_examples[norm_line]) > 3:
                    print(f"    ... and {len(set(log2_examples[norm_line])) - 3} more variants")
        print()
    
    # Check for frequency differences in common lines
    frequency_diffs = []
    for norm_line in log1_normalized & log2_normalized:
        if log1_counts[norm_line] != log2_counts[norm_line]:
            frequency_diffs.append((norm_line, log1_counts[norm_line], log2_counts[norm_line]))
    
    if frequency_diffs:
        print(f"Alpha-equivalent forms with different frequencies ({len(frequency_diffs)}):")
        print("-" * 50)
        for norm_line, count1, count2 in sorted(frequency_diffs, key=lambda x: format_normalized_line(x[0])):
            print(f"  {format_normalized_line(norm_line)}")
            print(f"    {args.log1}: {count1}x")
            print(f"    {args.log2}: {count2}x")
            if args.show_examples:
                print(f"    Example from log1: {log1_examples[norm_line][0]}")
                print(f"    Example from log2: {log2_examples[norm_line][0]}")
        print()
    
    if not only_in_log1 and not only_in_log2 and not frequency_diffs:
        print("✓ Logs are alpha-equivalent (same logical content)")
    
    return 0 if not only_in_log1 and not only_in_log2 else 1


if __name__ == "__main__":
    sys.exit(main())
