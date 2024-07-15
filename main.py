import sys
import json
from extract import extract_sentences_and_paragraphs
from filterWithLLM import filter_sentences
from rate_complexity import analyze_sentence, calculate_complexity_score, calculate_corpus_statistics, normalize_measures

def save_sentence_to_paragraph(sentence_to_paragraph, output_file):
    """Save the sentence_to_paragraph dictionary to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sentence_to_paragraph, f, ensure_ascii=False, indent=2)
    print(f"Saved sentence_to_paragraph to {output_file}")

def save_ordered_sentences(ordered_sentences, output_file):
    """Save the ordered sentences to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ordered_sentences, f, ensure_ascii=False, indent=2)
    print(f"Saved ordered sentences to {output_file}")

def main(file_path):
    # Extract sentences and paragraphs
    sentences, sentence_to_paragraph = extract_sentences_and_paragraphs(file_path)
    print(f"Extracted {len(sentences)} sentences")
    
    # Save sentence_to_paragraph to file
    output_file = file_path + '_sentence_to_paragraph.json'
    save_sentence_to_paragraph(sentence_to_paragraph, output_file)
    
    # Filter sentences
    filtered_sentences = filter_sentences(sentences,6670)
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
    
    # Remove duplicates and sort by complexity
    unique_filtered_sentences = list(set(filtered_sentences))
    sorted_sentences = sorted(
        unique_filtered_sentences,
        key=lambda s: calculate_complexity_score(
            normalize_measures(sentence_to_measures[s], means, std_devs),
            weights
        ),
        reverse=True
    )
    
    # Save ordered sentences to file
    ordered_sentences_file = file_path + '_ordered_sentences.json'
    save_ordered_sentences(sorted_sentences, ordered_sentences_file)

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
