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
import os


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


def show_context(lines, target_line_num, context_size=3):
    """Show lines around a target line number with context."""
    start = max(0, target_line_num - context_size - 1)
    end = min(len(lines), target_line_num + context_size)
    
    for i in range(start, end):
        marker = ">>> " if i == target_line_num - 1 else "    "
        print(f"{marker}{i+1:4d}: {lines[i].rstrip()}")


def interactive_diff_mode(log1_lines, log2_lines, log1_path, log2_path, only_in_log1, only_in_log2, frequency_diffs, log1_examples, log2_examples, log1_counts, log2_counts):
    """Interactive mode to step through differences one by one."""
    
    # Read original file contents for context
    with open(log1_path, 'r', encoding='utf-8') as f:
        log1_raw_lines = f.readlines()
    with open(log2_path, 'r', encoding='utf-8') as f:
        log2_raw_lines = f.readlines()
    
    # Create mappings from normalized forms to line numbers
    log1_line_nums = {}
    log2_line_nums = {}
    
    for norm, line_num, orig in log1_lines:
        if norm not in log1_line_nums:
            log1_line_nums[norm] = []
        log1_line_nums[norm].append(line_num)
    
    for norm, line_num, orig in log2_lines:
        if norm not in log2_line_nums:
            log2_line_nums[norm] = []
        log2_line_nums[norm].append(line_num)
    
    # Collect all differences, ordered by first appearance in files
    all_diffs = []
    
    # Add lines only in log1, ordered by first appearance in log1
    log1_only_with_line_nums = []
    for norm_line in only_in_log1:
        first_line_num = log1_line_nums[norm_line][0]
        log1_only_with_line_nums.append((first_line_num, norm_line))
    
    # Sort by line number and add to all_diffs
    for _, norm_line in sorted(log1_only_with_line_nums):
        all_diffs.append(('only_in_log1', norm_line))
    
    # Add lines only in log2, ordered by first appearance in log2
    log2_only_with_line_nums = []
    for norm_line in only_in_log2:
        first_line_num = log2_line_nums[norm_line][0]
        log2_only_with_line_nums.append((first_line_num, norm_line))
    
    # Sort by line number and add to all_diffs
    for _, norm_line in sorted(log2_only_with_line_nums):
        all_diffs.append(('only_in_log2', norm_line))
    
    # Add frequency differences, ordered by first appearance in log1
    freq_diff_with_line_nums = []
    for norm_line, count1, count2 in frequency_diffs:
        first_line_num = log1_line_nums[norm_line][0]
        freq_diff_with_line_nums.append((first_line_num, norm_line, count1, count2))
    
    # Sort by line number and add to all_diffs
    for _, norm_line, count1, count2 in sorted(freq_diff_with_line_nums):
        all_diffs.append(('frequency_diff', norm_line, count1, count2))
    
    if not all_diffs:
        print("✓ Logs are alpha-equivalent (same logical content)")
        return
    
    print(f"\nFound {len(all_diffs)} differences. Use 'n' for next, 'p' for previous, 'q' to quit, 'h' for help.")
    print("=" * 80)
    
    current_idx = 0
    
    while True:
        if current_idx < 0:
            current_idx = 0
        elif current_idx >= len(all_diffs):
            current_idx = len(all_diffs) - 1
        
        diff = all_diffs[current_idx]
        diff_type = diff[0]
        
        print(f"\nDifference {current_idx + 1} of {len(all_diffs)}")
        print("-" * 40)
        
        if diff_type == 'only_in_log1':
            norm_line = diff[1]
            count = log1_counts[norm_line]
            count_str = f" (appears {count}x)" if count > 1 else ""
            
            print(f"ONLY IN {log1_path}{count_str}")
            print(f"Normalized: {format_normalized_line(norm_line)}")
            print(f"Original:   {log1_examples[norm_line][0]}")
            
            if norm_line in log1_line_nums:
                print(f"\nContext in {log1_path}:")
                show_context(log1_raw_lines, log1_line_nums[norm_line][0])
        
        elif diff_type == 'only_in_log2':
            norm_line = diff[1]
            count = log2_counts[norm_line]
            count_str = f" (appears {count}x)" if count > 1 else ""
            
            print(f"ONLY IN {log2_path}{count_str}")
            print(f"Normalized: {format_normalized_line(norm_line)}")
            print(f"Original:   {log2_examples[norm_line][0]}")
            
            if norm_line in log2_line_nums:
                print(f"\nContext in {log2_path}:")
                show_context(log2_raw_lines, log2_line_nums[norm_line][0])
        
        elif diff_type == 'frequency_diff':
            norm_line, count1, count2 = diff[1], diff[2], diff[3]
            
            print(f"FREQUENCY DIFFERENCE")
            print(f"Normalized: {format_normalized_line(norm_line)}")
            print(f"{log1_path}: {count1}x")
            print(f"{log2_path}: {count2}x")
            print(f"Original from log1: {log1_examples[norm_line][0]}")
            print(f"Original from log2: {log2_examples[norm_line][0]}")
            
            if norm_line in log1_line_nums:
                print(f"\nContext in {log1_path} (first occurrence):")
                show_context(log1_raw_lines, log1_line_nums[norm_line][0])
            
            if norm_line in log2_line_nums:
                print(f"\nContext in {log2_path} (first occurrence):")
                show_context(log2_raw_lines, log2_line_nums[norm_line][0])
        
        print("\n" + "=" * 80)
        
        try:
            command = input("Command (n=next, p=previous, q=quit, h=help): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
        
        if command in ['n', 'next', '']:
            current_idx += 1
            if current_idx >= len(all_diffs):
                print("Reached end of differences.")
                current_idx = len(all_diffs) - 1
        elif command in ['p', 'prev', 'previous']:
            current_idx -= 1
            if current_idx < 0:
                print("At beginning of differences.")
                current_idx = 0
        elif command in ['q', 'quit', 'exit']:
            break
        elif command in ['h', 'help']:
            print("\nCommands:")
            print("  n, next    - Go to next difference")
            print("  p, prev    - Go to previous difference")
            print("  q, quit    - Exit interactive mode")
            print("  h, help    - Show this help")
            print("  <enter>    - Same as next")
        else:
            print(f"Unknown command: {command}. Type 'h' for help.")


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
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Interactive mode to step through differences")
    
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
    
    # Check for frequency differences in common lines
    frequency_diffs = []
    for norm_line in log1_normalized & log2_normalized:
        if log1_counts[norm_line] != log2_counts[norm_line]:
            frequency_diffs.append((norm_line, log1_counts[norm_line], log2_counts[norm_line]))
    
    # Report results
    print(f"Log 1: {len(log1_lines)} lines ({len(log1_normalized)} unique alpha-equivalent forms)")
    print(f"Log 2: {len(log2_lines)} lines ({len(log2_normalized)} unique alpha-equivalent forms)")
    print(f"Common alpha-equivalent forms: {len(log1_normalized & log2_normalized)}")
    
    if args.interactive:
        interactive_diff_mode(log1_lines, log2_lines, args.log1, args.log2, 
                            only_in_log1, only_in_log2, frequency_diffs,
                            log1_examples, log2_examples, log1_counts, log2_counts)
    else:
        # Original non-interactive output
        print()
        
        if only_in_log1:
            print(f"Alpha-equivalent forms only in {args.log1} ({len(only_in_log1)}):")
            print("-" * 50)
            for norm_line in sorted(only_in_log1, key=lambda x: format_normalized_line(x)):
                count = log1_counts[norm_line]
                count_str = f" (appears {count}x)" if count > 1 else ""
                print(f"  Normalized: {format_normalized_line(norm_line)}{count_str}")
                
                # Always show at least one original example
                examples = list(set(log1_examples[norm_line]))[:3]  # Show up to 3 unique examples
                for i, example in enumerate(examples):
                    if i == 0:
                        print(f"  Original:   {example}")
                    else:
                        print(f"              {example}")
                if len(set(log1_examples[norm_line])) > 3:
                    print(f"              ... and {len(set(log1_examples[norm_line])) - 3} more variants")
                print()
            print()
        
        if only_in_log2:
            print(f"Alpha-equivalent forms only in {args.log2} ({len(only_in_log2)}):")
            print("-" * 50)
            for norm_line in sorted(only_in_log2, key=lambda x: format_normalized_line(x)):
                count = log2_counts[norm_line]
                count_str = f" (appears {count}x)" if count > 1 else ""
                print(f"  Normalized: {format_normalized_line(norm_line)}{count_str}")
                
                # Always show at least one original example
                examples = list(set(log2_examples[norm_line]))[:3]  # Show up to 3 unique examples
                for i, example in enumerate(examples):
                    if i == 0:
                        print(f"  Original:   {example}")
                    else:
                        print(f"              {example}")
                if len(set(log2_examples[norm_line])) > 3:
                    print(f"              ... and {len(set(log2_examples[norm_line])) - 3} more variants")
                print()
            print()
        
        if frequency_diffs:
            print(f"Alpha-equivalent forms with different frequencies ({len(frequency_diffs)}):")
            print("-" * 50)
            for norm_line, count1, count2 in sorted(frequency_diffs, key=lambda x: format_normalized_line(x[0])):
                print(f"  Normalized: {format_normalized_line(norm_line)}")
                print(f"    {args.log1}: {count1}x")
                print(f"    {args.log2}: {count2}x")
                print(f"    Original from log1: {log1_examples[norm_line][0]}")
                print(f"    Original from log2: {log2_examples[norm_line][0]}")
                print()
            print()
        
        if not only_in_log1 and not only_in_log2 and not frequency_diffs:
            print("✓ Logs are alpha-equivalent (same logical content)")
    
    return 0 if not only_in_log1 and not only_in_log2 else 1


if __name__ == "__main__":
    sys.exit(main())
