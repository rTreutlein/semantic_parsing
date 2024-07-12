import re
import sys

def find_closing_paren(s, start):
    count = 0
    for i in range(start, len(s)):
        if s[i] == '(':
            count += 1
        elif s[i] == ')':
            count -= 1
            if count == 0:
                return i
    return -1


def extract_matches(s):
    # Find the start of the pattern
    start = s.find("(implies")
    if start == -1:
        return None, None  # Pattern not found

    # Find the end of the pattern
    end = find_closing_paren(s,start)
    if end == -1:
        return None, None  # Closing parenthesis not found

    # Extract the content between the arrows and the closing parenthesis
    content = s[start+3:end].strip()

    # Split the content into two matches
    matches = []
    paren_count = 0
    current_match = ""

    for char in content:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1

        current_match += char

        if paren_count == 0 and current_match.strip():
            matches.append(current_match.strip())
            current_match = ""

    # Check if we found exactly two matches
    if len(matches) == 2:
        return matches[0], matches[1]
    else:
        return None, None

def extract_predicates(expression):
    return re.findall(r'\((\w+)\s+', expression)

def check_predicates(input_string):
    
    left_side , right_side =  extract_matches(input_string)

    # Extract predicates from both sides
    left_predicates = set(extract_predicates(left_side))
    right_predicates = set(extract_predicates(right_side))

    # Check if all right-side predicates are in left-side predicates
    contained_predicates = right_predicates.intersection(left_predicates)
    all_contained = contained_predicates == right_predicates

    return all_contained, contained_predicates

def process_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                all_contained, _ = check_predicates(line)
                if not all_contained:
                    print(line)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python filter_pl.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    process_file(input_file)


