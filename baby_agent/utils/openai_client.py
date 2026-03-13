import os
import json
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

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None, tools: List[Dict] = None) -> Any:
        """生成对话响应，支持 tool call"""
        try:
            kwargs = {
                "model": model or self.model,
                "messages": messages,
                "temperature": 0.7,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            return response
        except Exception as e:
            raise e

    def stream_chat_completion(self, messages: List[Dict[str, str]], model: str = None, tools: List[Dict] = None):
        """流式生成对话响应，支持 tool call"""
        try:
            kwargs = {
                "model": model or self.model,
                "messages": messages,
                "temperature": 0.7,
                "stream": True,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            stream = self.client.chat.completions.create(**kwargs)
            for chunk in stream:
                yield chunk
        except Exception as e:
            yield f"Error: {e}"

    def generate_response(self, prompt: str, tools: List[Dict] = None) -> Any:
        """生成简单响应，支持 tool call"""
        messages = [
            {"role": "system", "content": "You are Baby Agent, a helpful assistant with access to file and shell tools."},
            {"role": "user", "content": prompt}
        ]
        return self.chat_completion(messages, tools=tools)

    def stream_generate_response(self, prompt: str, tools: List[Dict] = None):
        """流式生成简单响应，支持 tool call"""
        messages = [
            {"role": "system", "content": "You are Baby Agent, a helpful assistant with access to file and shell tools."},
            {"role": "user", "content": prompt}
        ]
        return self.stream_chat_completion(messages, tools=tools)

    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict], tool_executors: Dict[str, callable]) -> str:
        """
        支持 tool call 的完整对话流程

        Args:
            messages: 对话消息列表
            tools: OpenAI tool schema 列表
            tool_executors: 工具名称到执行函数的映射

        Returns:
            最终响应内容
        """
        # 第一次调用，让模型决定是否需要使用工具
        response = self.chat_completion(messages, tools=tools)
        message = response.choices[0].message

        # 检查是否有 tool_calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            # 添加助手的消息（包含 tool_calls）到对话历史
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [{
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls]
            })

            # 执行每个工具调用
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # 查找并执行对应的工具
                if function_name in tool_executors:
                    result = tool_executors[function_name](function_name, function_args)
                else:
                    result = f"Error: Tool '{function_name}' not found"

                # 添加工具结果到对话历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

            # 第二次调用，获取最终响应
            final_response = self.chat_completion(messages, tools=tools)
            return final_response.choices[0].message.content
        else:
            # 没有 tool calls，直接返回内容
            return message.content
