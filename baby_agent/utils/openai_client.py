import os
from typing import Optional, List, Dict, Any
from openai import OpenAI

class OpenAIClient:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=api_key)
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> str:
        """生成对话响应"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"
    
    def generate_response(self, prompt: str) -> str:
        """生成简单响应"""
        messages = [
            {"role": "system", "content": "You are Baby Agent, a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        return self.chat_completion(messages)
