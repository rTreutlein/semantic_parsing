import spacy
import os
import re

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_paragraphs(text):
    # Split text into paragraphs based on double newlines
    paragraphs = re.split(r'\n\s*\n', text)
    # Remove any leading/trailing whitespace from paragraphs
    return [p.strip() for p in paragraphs if p.strip()]

def extract_sentences_from_paragraph(paragraph):
    doc = nlp(paragraph)
    sentences = [sent.text.strip() for sent in doc.sents]
    return [sent for sent in sentences if is_proper_sentence(sent)]

def extract_sentences_and_paragraphs(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    paragraphs = extract_paragraphs(text)
    sentence_to_paragraph = {}
    all_sentences = []

    for paragraph in paragraphs:
        sentences = extract_sentences_from_paragraph(paragraph)
        all_sentences.extend(sentences)
        for sentence in sentences:
            sentence_to_paragraph[sentence] = paragraph

    print(f"Text length: {len(text)}")
    print(f"Sentences length: {len(''.join(all_sentences))}")
    
    return all_sentences, sentence_to_paragraph

def is_proper_sentence(text):
    doc = nlp(text)
    has_subject = any(token.dep_ == "nsubj" for token in doc)
    has_verb = any(token.pos_ == "VERB" for token in doc)
    special = any(token.text == "{" for token in doc)
    return has_subject and has_verb and not special

def main():
    input_directory = 'physics_articles'
    
    if not os.path.exists('extracted_sentences'):
        os.makedirs('extracted_sentences')
    
    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        sentences, sentence_to_paragraph = extract_sentences_and_paragraphs(file_path)

        output_file_path = os.path.join('extracted_sentences', filename)
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for sentence in sentences:
                output_file.write(sentence + '\n')
        
        print(f"Extracted sentences from: {filename}")

    return sentences, sentence_to_paragraph

if __name__ == "__main__":
    main()
