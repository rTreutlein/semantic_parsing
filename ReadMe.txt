Project Overview:

1. Scraping:
   - scraping/download_wikipedia_articles.py: Downloads articles from Wikipedia
   - scraping/extract_lojban_paragraphs.py: Extracts Lojban paragraphs from downloaded content

2. Processing:
   - processing/extract_sentences.py: Extracts individual sentences from paragraphs
   - processing/filter_sentences_llm.py: Filters sentences using a language model
   - processing/sentence_complexity.py: Analyzes and rates sentence complexity
   - processing/filter_predicate_logic.py: Filters predicate logic expressions

3. Main Execution:
   - main.py: Orchestrates the process, including sorting sentences by complexity

4. Conversion:
   - convert_to_predicate_logic.py: Converts natural language to predicate logic

5. Utilities:
   - utils/prompts.py: Contains prompt templates for language models
   - utils/ragclass.py: Implements the RAG (Retrieval-Augmented Generation) class

6. Other:
   - requirements.txt: Lists all Python dependencies for the project
   - .gitignore: Specifies intentionally untracked files to ignore

Note: For testing random functionalities, create separate test files as needed.
