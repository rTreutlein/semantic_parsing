import sys
from extract import extract_sentences
from filterWithLLM import filter_sentences
from rate_complexity import analyze_sentence, calculate_complexity_score, calculate_corpus_statistics, normalize_measures

def main(file_path):
    # Extract sentences
    sentences = extract_sentences(file_path)
    
    # Filter sentences
    filtered_sentences = filter_sentences(sentences)
    
    # Define weights for complexity measures
    weights = {
        'num_words': 0.5,
        'num_clauses': 0.1,
        'parse_tree_depth': 0.1,
        'num_logical_connectives': 0.1,
        'num_quantifiers': 0.1,
        'num_modifiers': 0.1,
    }
    
    # Calculate corpus statistics
    means, std_devs, sentence_to_measures = calculate_corpus_statistics(filtered_sentences)
    
    # Sort by complexity
    sorted_sentences = sorted(
        filtered_sentences,
        key=lambda s: calculate_complexity_score(
            normalize_measures(sentence_to_measures[s], means, std_devs),
            weights
        ),
        reverse=True
    )
    
    # Print sorted sentences
    for sentence in sorted_sentences:
        print(sentence)

if len(sys.argv) != 2:
    print("Usage: python main.py <file_path>")
    sys.exit(1)

file_path = sys.argv[1]
print(f"Processing file: {file_path}")
main(file_path)
