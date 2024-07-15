import spacy
import os

# Download the necessary NLTK data files
nlp = spacy.load("en_core_web_sm")

def extract_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        
    doc = nlp(text)

     # Extract sentences
    sentences = [sent.text.replace('\n', '').strip() for sent in doc.sents]
    sentences = [sent for sent in sentences if is_proper_sentence(sent)]

    #output text and sentences length
    print(f"Text length: {len(text)}")
    print(f"Sentences length: {len(''.join(sentences))}")
    
    return sentences

def is_proper_sentence(text):
    doc = nlp(text)
    # Check if the text starts with a capital letter
    #if not text[0].isupper():
        #return False
    # Check if the text contains at least one subject and one verb
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
        sentences = extract_sentences(file_path)

        output_file_path = os.path.join('extracted_sentences', filename)
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for sentence in sentences:
                output_file.write(sentence + '\n')
        
        print(f"Extracted sentences from: {filename}")

#if __name__ == "__main__":
    #main()
