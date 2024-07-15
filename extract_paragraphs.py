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
    have_seen_example = False

    for element in content.children:
        if element.name == 'p':
            if have_seen_example:
                paragraphs.append(current_paragraph.strip() + "\n" + element.get_text() + " ")
                current_paragraph = ""
            else:
                if current_paragraph:
                    paragraphs.append(current_paragraph.strip())
                current_paragraph = element.get_text() + " "
        elif element.name == 'div' and 'example' in element.get('class', []):
            current_paragraph += element.get_text() + " "
            have_seen_example = True

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
