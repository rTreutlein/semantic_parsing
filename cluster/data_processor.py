import json

def process_jsonl(file_path):
    entailment_pairs = []
    
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            if data['gold_label'] == 'entailment':
                entailment_pairs.append((data['sentence1'], data['sentence2']))
    
    return entailment_pairs
