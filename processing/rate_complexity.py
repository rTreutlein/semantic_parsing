import spacy
import numpy as np
import concurrent.futures

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def analyze_sentence(sentence):
    # Process the sentence using spaCy
    doc = nlp(sentence)
    
    # Number of words
    num_words = len(doc)
    
    # Syntactic parsing: Number of clauses (simple heuristic based on conjunctions and relative pronouns)
    num_clauses = sum(1 for token in doc if token.dep_ in ('cc', 'mark', 'relcl'))
    
    # Depth of parse tree
    parse_tree_depth = max(token.i - token.head.i for token in doc)
    
    # Part-of-Speech (POS) tagging: Variety of POS tags
    #pos_tags = [token.pos_ for token in doc]
    #pos_variety = len(set(pos_tags))
    
    # Dependency parsing: Number of dependencies
    #num_dependencies = len(list(doc.sents))
    
    # Presence of logical connectives
    logical_connectives = {'if', 'then', 'and', 'or', 'not'}
    num_logical_connectives = sum(1 for token in doc if token.text.lower() in logical_connectives)
    
    # Quantifiers and modifiers
    quantifiers = {'all', 'some', 'none', 'many', 'few', 'several', 'every'}
    modifiers = [token for token in doc if token.pos_ in ('ADJ', 'ADV')]
    num_quantifiers = sum(1 for token in doc if token.text.lower() in quantifiers)
    num_modifiers = len(modifiers)
    
    # Lexical diversity
    #lexical_diversity = len(set(token.text for token in doc)) / num_words
    
    # Compile results
    complexity_measures = {
        'num_words': num_words,
        'num_clauses': num_clauses,
        'parse_tree_depth': parse_tree_depth,
        #'pos_variety': pos_variety,
        #'num_dependencies': num_dependencies,
        'num_logical_connectives': num_logical_connectives,
        'num_quantifiers': num_quantifiers,
        'num_modifiers': num_modifiers,
        #'lexical_diversity': lexical_diversity
    }
    
    return sentence,complexity_measures

def calculate_corpus_statistics(corpus):
    # Function to analyze a single sentence
    def analyze(sentence):
        return analyze_sentence(sentence)
    
    # Use ThreadPoolExecutor to parallelize the analysis of sentences
    with concurrent.futures.ThreadPoolExecutor() as executor:
        corpus_measures = list(executor.map(analyze, corpus))

    # Create a map of sentence to its complexity measures
    sentence_to_measures = {sentence: measures for sentence, measures in corpus_measures}
    
    # Calculate mean and standard deviation for each complexity measure
    measures_keys = corpus_measures[0][1].keys()
    means = {key: np.mean([measure[key] for _,measure in corpus_measures]) for key in measures_keys}
    std_devs = {key: np.std([measure[key] for _,measure in corpus_measures]) for key in measures_keys}
    
    return means, std_devs, sentence_to_measures

def normalize_measures(measures, means, std_devs):
    # Normalize each measure
    normalized_measures = {key: (measures[key] - means[key]) / std_devs[key] if std_devs[key] != 0 else 0 for key in measures.keys()}
    return normalized_measures

def calculate_complexity_score(normalized_measures, weights):
    # Calculate the weighted sum of normalized complexity measures
    complexity_score = sum(normalized_measures[measure] * weight for measure, weight in weights.items())
    return complexity_score

# Define weights for each complexity measure based on domain knowledge or empirical analysis
weights = {
    'num_words': 0.5,                # Word count might be less important
    'num_clauses': 0.1,              # Clauses might be moderately important
    'parse_tree_depth': 0.1,         # Parse tree depth might be moderately important
    #'pos_variety': 0.05,             # POS variety might be less important
    #'num_dependencies': 0.1,         # Number of dependencies might be moderately important
    'num_logical_connectives': 0.1, # Logical connectives might be very important
    'num_quantifiers': 0.1,         # Quantifiers might be less important
    'num_modifiers': 0.1,           # Modifiers might be less important
    #'lexical_diversity': 0.1         # Lexical diversity might be moderately important
}

## Example corpus
#corpus = [
#    "The cat sat on the mat.",
#    "If all humans are mortal and Socrates is a human, then Socrates is mortal.",
#    "The quick brown fox jumps over the lazy dog."
#]
#
## Calculate corpus statistics
#means, std_devs, sentence_to_measures = calculate_corpus_statistics(corpus)
#
## Example usage for a single sentence
#sentence = "If all humans are mortal and Socrates is a human, then Socrates is mortal."
#complexity_measures = analyze_sentence(sentence)
#normalized_measures = normalize_measures(complexity_measures, means, std_devs)
#complexity_score = calculate_complexity_score(normalized_measures, weights)
#print(f"Complexity Score: {complexity_score}")
#
## Example for ordering sentences by complexity
#sentence_complexities = [(sentence, calculate_complexity_score(normalize_measures(sentence_to_measures[sentence], means, std_devs), weights)) for sentence in corpus]
#
## Sort sentences by complexity score
#sorted_sentences = sorted(sentence_complexities, key=lambda x: x[1], reverse=True)
#
#print("Sentences sorted by complexity:")
#for sentence, score in sorted_sentences:
#    print(f"Sentence: {sentence}, Complexity Score: {score}")

#import csv

# Define the path to your CSV file
#csv_file_path = 'output.txt'

# Read the sentences from the CSV file
#corpus = []
#fol = []
#with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
#    reader = csv.reader(csvfile,delimiter="|")
#    for row in reader:
#        corpus.append(row[0])  # Assuming the first column contains the sentences
#        fol.append(row[1])

#with open("data/llmfiltered.txt",'r') as file:
#with open("data/clustered.txt",'r') as file:
#corpus = file.readlines()

# Calculate corpus statistics
#means, std_devs,sentence_to_measures = calculate_corpus_statistics(corpus)

# Calculate complexity scores for each sentence
#sentence_complexities = [(calculate_complexity_score(normalize_measures(sentence_to_measures[sentence], means, std_devs), weights)) for sentence in corpus]

#all = set(zip(corpus,sentence_complexities))

# Sort sentences by complexity score
#sorted_sentences = sorted(all, key=lambda x: x[1])

#for sent in sorted_sentences:
    #print(f"Sentence: {sent[0]} {sent[1]}\n Complexity Score: {sent[2]}\n complexity_measures: {sentence_to_measures[sent[0]]}\n complexity_measures_norm: {normalize_measures(sentence_to_measures[sent[0]],means,std_devs)}")
    #print(f"Sentence: {sent[0]} \n Complexity Score: {sent[1]}\n complexity_measures: {sentence_to_measures[sent[0]]}\n complexity_measures_norm: {normalize_measures(sentence_to_measures[sent[0]],means,std_devs)}")
    #print(sent[0],end="")
