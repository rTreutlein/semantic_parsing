import openai
from typing import List

class OpenAIClient:
    def __init__(self, api_key: str):
        openai.api_key = api_key

    def generate(self, prompt: str) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Error in generating response: {e}")
            return ""
