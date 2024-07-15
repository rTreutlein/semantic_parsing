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
                current_paragraph = current_paragraph.strip() + "\n" + element.get_text() + " "
                have_seen_example = False
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

    # Clean up paragraphs to remove multiple consecutive linebreaks and whitespace-only lines
    cleaned_paragraphs = []
    for paragraph in paragraphs:
        # Replace multiple consecutive linebreaks with a single linebreak
        cleaned_paragraph = re.sub(r'\n{2,}', '\n', paragraph)
        # Split the paragraph into lines, filter out whitespace-only lines, and rejoin
        cleaned_lines = [line.strip() for line in cleaned_paragraph.split('\n') if line.strip()]
        cleaned_paragraphs.append(' '.join(cleaned_lines))

    return cleaned_paragraphs

def main():
    url = "https://la-lojban.github.io/uncll/romoi/xhtml_section_chunks/chapter-tour.html#section-bridi"
    paragraphs = extract_paragraphs(url)

    for i, paragraph in enumerate(paragraphs, 1):
        print(paragraph)
        print("\n")

if __name__ == "__main__":
    main()
