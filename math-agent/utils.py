import requests
import random
import re
import os
import asyncio
from typing import Tuple, Optional, List
from functools import partial

models = [
    "emma2-9b-it",
    "llama-3.1-8b-instant",
    "llama-3.2-11b-vision-preview",
    "llama-3.2-1b-preview",
    "llama-3.2-3b-preview",
    "llama-3.2-90b-vision-preview",
    "llama-3.3-70b-specdec",
    "llama-3.3-70b-versatile",
    "llama-guard-3-8b",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768"
]

def _get_completion_sync(api_key: str, prompt: str) -> Optional[dict]:
    model = random.choice(models)
    
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    return None

async def _get_completion(api_key: str, prompt: str) -> Optional[dict]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_get_completion_sync, api_key, prompt))

async def ask_groq(prompt: str) -> str:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    response = await _get_completion(GROQ_API_KEY, prompt)
    if response:
        return response["choices"][0]["message"]["content"]
    raise Exception("Failed to get response from Groq API")

def extract_python_code(text: str) -> List[str]:
    pattern = r"```python\s*(.*?)\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

async def get_code_from_groq(question: str, max_attempts: int = 5) -> Tuple[str, List[str]]:
    context = f'''
    Write python code to answer the user's question:
    {question}.
    Make sure it's executable and prints answer and avoids third party libraries. Also, code should not have any functions and just plain python code which executes when run. 
    '''
    for attempt in range(max_attempts):
        try:
            response = await ask_groq(context)
            code_blocks = extract_python_code(response)
            if code_blocks:
                return response, code_blocks
        except Exception as e:
            if attempt == max_attempts - 1:
                raise Exception(f"Failed to get code after {max_attempts} attempts: {str(e)}")
            continue
    
    raise Exception(f"No code blocks found after {max_attempts} attempts")