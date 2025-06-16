#!/usr/bin/env python3
"""
Script to fix line breaks in Scheme-like code.
Ensures that each line starting with an open parenthesis has its matching
closing parenthesis on the same line.
"""

import sys
import os
import argparse

def count_parens(text):
    """Count the balance of parentheses in text."""
    count = 0
    for char in text:
        if char == '(':
            count += 1
        elif char == ')':
            count -= 1
    return count

def fix_linebreaks(content):
    """Fix line breaks in Scheme-like code."""
    lines = content.split('\n')
    result = []
    current_line = ""
    paren_balance = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            if current_line and paren_balance == 0:
                result.append(current_line.strip())
                current_line = ""
            continue
        
        # If we're starting a new expression (line starts with '(')
        if stripped.startswith('(') and paren_balance == 0:
            # Save any previous complete expression
            if current_line:
                result.append(current_line.strip())
            current_line = stripped
            paren_balance = count_parens(stripped)
        else:
            # Continue building the current expression
            if current_line:
                current_line += " " + stripped
            else:
                current_line = stripped
            paren_balance += count_parens(stripped)
        
        # If parentheses are balanced, we have a complete expression
        if paren_balance == 0 and current_line:
            result.append(current_line.strip())
            current_line = ""
    
    # Add any remaining content
    if current_line:
        result.append(current_line.strip())
    
    return '\n'.join(result)

def main():
    parser = argparse.ArgumentParser(description='Fix line breaks in Scheme-like code')
    parser.add_argument('input_file', help='Input file to process')
    parser.add_argument('-o', '--output', help='Output file (default: overwrite input)')
    parser.add_argument('--backup', action='store_true', help='Create backup of original file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Read input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fix line breaks
    fixed_content = fix_linebreaks(content)
    
    # Determine output file
    output_file = args.output if args.output else args.input_file
    
    # Create backup if requested
    if args.backup and output_file == args.input_file:
        backup_file = args.input_file + '.bak'
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Backup created: {backup_file}")
        except Exception as e:
            print(f"Warning: Could not create backup: {e}", file=sys.stderr)
    
    # Write output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Fixed file written to: {output_file}")
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
