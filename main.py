import sys
from extract import extract_sentences_and_paragraphs
from filterWithLLM import filter_sentences
from rate_complexity import analyze_sentence, calculate_complexity_score, calculate_corpus_statistics, normalize_measures

def main(file_path):
    # Extract sentences and paragraphs
    sentences, sentence_to_paragraph = extract_sentences_and_paragraphs(file_path)
    print(f"Extracted {len(sentences)} sentences")
    
    # Filter sentences
    filtered_sentences = filter_sentences(sentences)
    print(f"{len(filtered_sentences)} sentences after filtering")
    
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
    
    # Print sorted sentences with their paragraphs
    for sentence in sorted_sentences:
        print(f"Sentence: {sentence}")
        print(f"Paragraph: {sentence_to_paragraph[sentence]}")
        print("---")

if len(sys.argv) != 2:
    print("Usage: python main.py <file_path>")
    sys.exit(1)

file_path = sys.argv[1]
print(f"Processing file: {file_path}")
main(file_path)
