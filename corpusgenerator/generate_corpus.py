import os
import json
from typing import List, Dict
import openai

# Load configuration
import config

# Set up OpenAI API key
openai.api_key = config.OPENAI_API_KEY

def generate_initial_topics(num_topics: int = 5) -> List[str]:
    """
    Generate initial topics for the corpus using GPT.
    """
    prompt = f"Generate {num_topics} diverse and interesting topics for a small corpus of text:"
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.7,
    )
    topics = response.choices[0].text.strip().split('\n')
    return [topic.strip() for topic in topics if topic.strip()]

def generate_content(topic: str, word_count: int = 200) -> str:
    """
    Generate content for a given topic using GPT.
    """
    prompt = f"Write a {word_count}-word paragraph about the following topic:\n\n{topic}\n\nParagraph:"
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=word_count,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

def generate_corpus(num_topics: int = 5, word_count: int = 200) -> Dict[str, str]:
    """
    Generate a small corpus of text using GPT.
    """
    topics = generate_initial_topics(num_topics)
    corpus = {}
    for topic in topics:
        content = generate_content(topic, word_count)
        corpus[topic] = content
    return corpus

def save_corpus(corpus: Dict[str, str], filename: str = "corpus.json"):
    """
    Save the generated corpus to a JSON file.
    """
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)
    with open(filepath, "w") as f:
        json.dump(corpus, f, indent=2)
    print(f"Corpus saved to {filepath}")

if __name__ == "__main__":
    corpus = generate_corpus()
    save_corpus(corpus)
    print("Corpus generation complete.")
