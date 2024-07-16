import requests
from bs4 import BeautifulSoup
import re
import os

# Function to get the list of all physics-related articles
def get_all_articles(url,subcats=True):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    articles = [] 

    if subcats:
        subcategories = soup.find_all("div", id="mw-subcategories")
        if subcategories:
            for link in subcategories[0].find_all("a"):
                if link.has_attr('href'):
                    tmp = get_all_articles("https://simple.wikipedia.org" + link['href'], False)
                    articles = articles + tmp

    pages = soup.find_all("div", id="mw-pages")
    if pages:
        for link in pages[0].find_all("a"):
            articles.append(link['href'])
    
    return articles

# Function to download the content of each article
def download_article(article_url):
    url = "https://simple.wikipedia.org" + article_url
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    title = soup.find('h1').text
    content = soup.find('div', {'class': 'mw-parser-output'})
    
    # Clean the text
    text = ''
    for element in content.find_all(['p','li']):
        text += element.text + '\n'
    
    return title, text

# Main function to download all articles
def main():
    articles = get_all_articles("https://simple.wikipedia.org/wiki/Category:Physics")
    
    if not os.path.exists('physics_articles'):
        os.makedirs('physics_articles')
    
    for article in articles:
        title, text = download_article(article)
        filename = re.sub(r'[\\/*?:"<>|]', "", title) + '.txt'
        filepath = os.path.join('physics_articles', filename)
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(text)
        
        print(f"Downloaded: {title}")

if __name__ == "__main__":
    main()
