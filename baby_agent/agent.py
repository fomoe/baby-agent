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
        self.all_tools_schema = []  # 存储所有工具的 schema
        self.tool_executors = {}  # 存储工具执行函数
        self.initialize_tools()
        self.initialize_skills()
        self.initialize_openai()

    def initialize_tools(self):
        from baby_agent.tools.file_tools import FileTools
        from baby_agent.tools.shell_tools import ShellTools

        # 初始化文件工具
        file_tools = FileTools()
        self.tools['file'] = file_tools
        self.all_tools_schema.extend(file_tools.TOOLS_SCHEMA)
        # 注册文件工具执行器
        for tool in file_tools.TOOLS_SCHEMA:
            tool_name = tool["function"]["name"]
            self.tool_executors[tool_name] = file_tools.execute_tool

        # 初始化 shell 工具
        shell_tools = ShellTools()
        self.tools['shell'] = shell_tools
        self.all_tools_schema.extend(shell_tools.TOOLS_SCHEMA)
        # 注册 shell 工具执行器
        for tool in shell_tools.TOOLS_SCHEMA:
            tool_name = tool["function"]["name"]
            self.tool_executors[tool_name] = shell_tools.execute_tool

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
        print("- Directly type your request, AI will automatically use file/shell tools when needed")
        print("- Example: 'Read the content of main.py'")
        print("- Example: 'List files in current directory'")
        print("- Example: 'Run ls -la command'")

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
        """使用 OpenAI tool call 处理 ReACT 模式"""
        if not self.openai_client:
            print("Baby Agent: OpenAI integration is not available. Please set OPENAI_API_KEY environment variable.")
            return

        print("Processing in ReACT mode with tool call...")

        # 构建系统提示
        system_prompt = """You are Baby Agent, a helpful assistant with access to file and shell tools.

You have access to the following tools:
- file_read: Read file content
- file_write: Write content to a file
- file_edit: Edit file content by replacing strings
- file_ls: List directory contents
- file_grep: Search for patterns in files
- shell_run: Execute shell commands

When you need to use a tool, you will be automatically invoked with the appropriate function call.
After receiving tool results, provide a helpful response to the user."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        try:
            # 使用 chat_with_tools 方法处理带工具的对话
            response = self.openai_client.chat_with_tools(
                messages=messages,
                tools=self.all_tools_schema,
                tool_executors=self.tool_executors
            )
            print(f"Baby Agent: {response}")
        except Exception as e:
            print(f"❌ Error during processing: {e}")
