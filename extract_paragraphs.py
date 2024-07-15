import requests
from bs4 import BeautifulSoup
import re

def extract_paragraphs(url):
    # Fetch the webpage content
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the main content div
    content = soup.find('div', class_='section')

    paragraphs = []
    current_paragraph = ""

    for element in content.children:
        print(element)
        if element.name == 'p':
            if current_paragraph:
                paragraphs.append(current_paragraph.strip())
                current_paragraph = ""
            current_paragraph += element.get_text() + " "
        elif element.name in ['pre', 'blockquote']:
            # This is likely an example
            current_paragraph += element.get_text() + " "
        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # End the current paragraph if there's any
            if current_paragraph:
                paragraphs.append(current_paragraph.strip())
                current_paragraph = ""
            # Add the header as a separate paragraph
            paragraphs.append(element.get_text().strip())

    # Add the last paragraph if there's any
    if current_paragraph:
        paragraphs.append(current_paragraph.strip())

    # Remove any empty paragraphs
    paragraphs = [p for p in paragraphs if p]

    return paragraphs

def main():
    url = "https://la-lojban.github.io/uncll/romoi/xhtml_section_chunks/chapter-tour.html#section-bridi"
    paragraphs = extract_paragraphs(url)

    for i, paragraph in enumerate(paragraphs, 1):
        print(f"Paragraph {i}:")
        print(paragraph)
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()
