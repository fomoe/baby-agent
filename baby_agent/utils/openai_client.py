import os
from typing import Optional, List, Dict, Any
from openai import OpenAI

class OpenAIClient:
    def __init__(self, model="openrouter/hunter-alpha"):
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_API_BASE_URL')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = None) -> str:
        """生成对话响应"""
        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"
    
    def stream_chat_completion(self, messages: List[Dict[str, str]], model: str = None):
        """流式生成对话响应"""
        try:
            stream = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=0.7,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {e}"
    
    def generate_response(self, prompt: str) -> str:
        """生成简单响应"""
        messages = [
            {"role": "system", "content": "You are Baby Agent, a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        return self.chat_completion(messages)
    
    def stream_generate_response(self, prompt: str):
        """流式生成简单响应"""
        messages = [
            {"role": "system", "content": "You are Baby Agent, a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        return self.stream_chat_completion(messages)
