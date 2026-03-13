import os
import sys
from typing import Optional, Dict, Any
from baby_agent.utils.openai_client import OpenAIClient

class BabyAgent:
    def __init__(self, model="openrouter/hunter-alpha"):
        self.mode = "react"  # 默认模式为ReACT模式
        self.tools = {}
        self.skills = {}
        self.openai_client = None
        self.model = model
        self.initialize_tools()
        self.initialize_skills()
        self.initialize_openai()
    
    def initialize_tools(self):
        from baby_agent.tools.file_tools import FileTools
        from baby_agent.tools.shell_tools import ShellTools
        
        self.tools['file'] = FileTools()
        self.tools['shell'] = ShellTools()
    
    def initialize_skills(self):
        # 技能系统初始化
        pass
    
    def initialize_openai(self):
        try:
            self.openai_client = OpenAIClient(model=self.model)
            print(f"OpenAI client initialized successfully with model: {self.model}")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            print("Continuing without OpenAI integration")
            self.openai_client = None
    
    def run(self):
        print("Baby Agent initialized. Type 'exit' to quit.")
        print(f"Current mode: {self.mode}")
        print("Type 'help' for available commands")
        
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if user_input.lower().startswith('mode:'):
                    new_mode = user_input.split(':', 1)[1].strip()
                    if new_mode in ['plan', 'react']:
                        self.mode = new_mode
                        print(f"✅ Switched to {self.mode} mode")
                    else:
                        print("❌ Invalid mode. Available modes: plan, react")
                    continue
                
                self.process_input(user_input)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again or type 'help' for assistance")
    
    def show_help(self):
        """显示帮助信息"""
        print("Available commands:")
        print("- exit: Quit the agent")
        print("- help: Show this help message")
        print("- mode: <plan|react>: Switch between modes")
        print("\nPlan mode commands:")
        print("- add task <task>: Add a task to the plan")
        print("- list tasks: List all tasks in the plan")
        print("- execute plan: Execute all tasks in the plan")
        print("\nReACT mode commands:")
        print("- read file <path>: Read a file")
        print("- write file <path> with content <content>: Write to a file")
        print("- run command <command>: Run a shell command")
        print("- Any other input: Chat with the agent")
    
    def process_input(self, user_input: str):
        if self.mode == "plan":
            self.process_plan_mode(user_input)
        else:
            self.process_react_mode(user_input)
    
    def process_plan_mode(self, user_input: str):
        print("Processing in plan mode...")
        if user_input.lower().startswith('add task'):
            # 添加任务到计划
            task = user_input[8:].strip()
            if not hasattr(self, 'plan_tasks'):
                self.plan_tasks = []
            self.plan_tasks.append(task)
            print(f"Added task: {task}")
            print(f"Current plan: {self.plan_tasks}")
        elif user_input.lower().startswith('list tasks'):
            # 列出计划中的任务
            if hasattr(self, 'plan_tasks') and self.plan_tasks:
                print("Current plan tasks:")
                for i, task in enumerate(self.plan_tasks, 1):
                    print(f"{i}. {task}")
            else:
                print("No tasks in plan")
        elif user_input.lower().startswith('execute plan'):
            # 执行计划
            if hasattr(self, 'plan_tasks') and self.plan_tasks:
                print("Executing plan...")
                for i, task in enumerate(self.plan_tasks, 1):
                    print(f"Executing task {i}: {task}")
                    # 这里可以添加任务执行逻辑
                print("Plan execution completed")
            else:
                print("No tasks in plan to execute")
        else:
            print("Plan mode commands:")
            print("- add task <task>: Add a task to the plan")
            print("- list tasks: List all tasks in the plan")
            print("- execute plan: Execute all tasks in the plan")
    
    def process_react_mode(self, user_input: str):
        print("Processing in ReACT mode...")
        if self.openai_client:
            # 简单的ReACT模式实现
            # 1. 生成推理
            reasoning = self.openai_client.generate_response(f"Analyze this user request and think about how to respond: {user_input}")
            print(f"[Reasoning]: {reasoning}")
            
            # 2. 检查是否需要使用工具
            # 这里可以根据推理结果决定是否使用工具
            # 为了演示，我们添加一些简单的工具使用逻辑
            if 'read file' in user_input.lower():
                # 提取文件路径
                import re
                match = re.search(r'read file (.+)', user_input.lower())
                if match:
                    file_path = match.group(1).strip()
                    result = self.tools['file'].read(file_path)
                    print(f"[Action]: Reading file {file_path}")
                    print(f"[Observation]: {result}")
            elif 'write file' in user_input.lower():
                # 提取文件路径和内容
                import re
                match = re.search(r'write file (.+) with content (.+)', user_input.lower())
                if match:
                    file_path = match.group(1).strip()
                    content = match.group(2).strip()
                    result = self.tools['file'].write(file_path, content)
                    print(f"[Action]: Writing to file {file_path}")
                    print(f"[Observation]: {result}")
            elif 'run command' in user_input.lower():
                # 提取命令
                import re
                match = re.search(r'run command (.+)', user_input.lower())
                if match:
                    command = match.group(1).strip()
                    result = self.tools['shell'].run(command)
                    print(f"[Action]: Running command: {command}")
                    print(f"[Observation]: stdout: {result['stdout']}")
                    if result['stderr']:
                        print(f"[Observation]: stderr: {result['stderr']}")
            
            # 3. 生成最终响应（使用流式）
            print("Baby Agent: ", end="", flush=True)
            for chunk in self.openai_client.stream_generate_response(f"Based on the reasoning and observations, provide a final response to the user: {user_input}"):
                print(chunk, end="", flush=True)
            print()
        else:
            print("Baby Agent: OpenAI integration is not available. Please set OPENAI_API_KEY environment variable.")
