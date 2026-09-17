import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")
token = os.getenv("GEMINI_API_KEY")
api_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {"model": "gemini-3.6-flash", "messages": [{"role": "user", "content": "hello"}]}

response = requests.post(api_url, headers=headers, json=payload)
print(response.status_code)
print(response.text)
