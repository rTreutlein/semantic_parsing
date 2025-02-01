with open('data3/learn_english_extended.txt', 'r') as file:
    lines = file.read().splitlines()

entries = {}
entry = None

for line in lines:
    if not line.startswith('-') and line.strip():
        entry = line.strip()
        entries[entry] = []
    elif line.startswith('-'):
        definition = line.lstrip('-').strip()
        entries[entry].append(definition)

with open('data3/learn_english_implications.txt', 'w') as file:
    for entry, definitions in entries.items():
        if definitions:
            file.write(f"{entry} implies {' or '.join(definitions)}\n")

