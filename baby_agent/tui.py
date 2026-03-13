"""
Baby Agent TUI - 基于 Textual 的文本用户界面
"""

import asyncio
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Input,
    Button,
    Static,
    RichLog,
    Label,
    TabbedContent,
    TabPane,
    DataTable,
    Tree,
)
from textual.reactive import reactive
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from baby_agent.agent import BabyAgent


class MessageDisplay(Static):
    """消息显示组件"""

    def __init__(self, role: str, content: str, **kwargs):
        self.role = role
        self.message_content = content
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        if self.role == "user":
            yield Label(Text(f"You: {self.message_content}", style="bold cyan"))
        elif self.role == "assistant":
            yield Label(Text(f"Agent: {self.message_content}", style="bold green"))
        elif self.role == "tool_call":
            yield Label(Text(f"🔧 Tool Call: {self.message_content}", style="bold yellow"))
        elif self.role == "tool_result":
            yield Label(Text(f"📋 Result: {self.message_content[:500]}{'...' if len(self.message_content) > 500 else ''}", style="dim"))
        elif self.role == "system":
            yield Label(Text(f"ℹ️  {self.message_content}", style="italic dim"))
        elif self.role == "error":
            yield Label(Text(f"❌ Error: {self.message_content}", style="bold red"))


class BabyAgentTUI(App):
    """Baby Agent TUI 应用"""

    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 100%;
        height: 100%;
        padding: 0 1;
    }

    #chat-container {
        width: 70%;
        height: 100%;
        border: solid $primary;
    }

    #sidebar {
        width: 30%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #chat-history {
        width: 100%;
        height: 85%;
        padding: 1;
        overflow-y: auto;
    }

    #input-container {
        width: 100%;
        height: 15%;
        padding: 1;
        border-top: solid $primary;
    }

    #message-input {
        width: 85%;
    }

    #send-button {
        width: 15%;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }

    .message {
        margin: 1 0;
        padding: 1;
    }

    .user-message {
        background: $surface-darken-1;
    }

    .agent-message {
        background: $surface-darken-2;
    }

    #tools-table {
        height: 40%;
    }

    #info-panel {
        height: 60%;
        border: solid $primary;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("enter", "send_message", "Send"),
        ("ctrl+l", "clear_chat", "Clear"),
    ]

    def __init__(self, model: str = "openrouter/hunter-alpha"):
        super().__init__()
        self.agent = BabyAgent(model=model)
        self.is_processing = False

    def compose(self) -> ComposeResult:
        """构建 UI"""
        yield Header(show_clock=True)

        with Horizontal(id="main-container"):
            # 左侧聊天区域
            with Vertical(id="chat-container"):
                with VerticalScroll(id="chat-history"):
                    yield MessageDisplay("system", "Welcome to Baby Agent TUI! Type your message and press Enter or click Send.")

                with Horizontal(id="input-container"):
                    yield Input(placeholder="Type your message here...", id="message-input")
                    yield Button("Send", id="send-button", variant="primary")

            # 右侧边栏
            with Vertical(id="sidebar"):
                yield Label(Text("Tools", style="bold underline"))

                # 工具列表
                tools_table = DataTable(id="tools-table")
                tools_table.add_columns("Tool Name", "Description")
                for tool in self.agent.all_tools_schema:
                    func = tool["function"]
                    tools_table.add_row(func["name"], func["description"][:30] + "...")
                yield tools_table

                # 信息面板
                with Vertical(id="info-panel"):
                    yield Label(Text("Status", style="bold underline"))
                    yield Label(f"Mode: {self.agent.mode}")
                    yield Label(f"Model: {self.agent.model}")
                    yield Label(f"Tools: {len(self.agent.all_tools_schema)}")
                    yield Label("")
                    yield Label(Text("Shortcuts", style="bold underline"))
                    yield Label("Enter - Send message")
                    yield Label("Ctrl+L - Clear chat")
                    yield Label("Q - Quit")

        # 状态栏
        yield Label("Ready | Press 'q' to quit", id="status-bar")
        yield Footer()

    async def on_mount(self):
        """应用挂载时的初始化"""
        self.query_one("#message-input", Input).focus()
        self.update_status("Ready")

    def update_status(self, status: str):
        """更新状态栏"""
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(f"{status} | Mode: {self.agent.mode} | Tools: {len(self.agent.all_tools_schema)}")

    async def action_send_message(self):
        """发送消息动作"""
        await self.handle_send()

    async def action_clear_chat(self):
        """清空聊天记录"""
        chat_history = self.query_one("#chat-history", VerticalScroll)
        chat_history.remove_children()
        chat_history.mount(MessageDisplay("system", "Chat cleared."))

    async def on_button_pressed(self, event: Button.Pressed):
        """按钮点击事件"""
        if event.button.id == "send-button":
            await self.handle_send()

    async def on_input_submitted(self, event: Input.Submitted):
        """输入框提交事件"""
        if event.input.id == "message-input":
            await self.handle_send()

    async def handle_send(self):
        """处理发送消息"""
        if self.is_processing:
            return

        input_widget = self.query_one("#message-input", Input)
        message = input_widget.value.strip()

        if not message:
            return

        # 清空输入框
        input_widget.value = ""

        # 显示用户消息
        chat_history = self.query_one("#chat-history", VerticalScroll)
        chat_history.mount(MessageDisplay("user", message))

        # 处理特殊命令
        if message.lower() == "exit":
            self.exit()
            return
        elif message.lower() == "help":
            chat_history.mount(MessageDisplay("system", "Available commands: exit, help, clear, mode:plan, mode:react"))
            return
        elif message.lower() == "clear":
            await self.action_clear_chat()
            return
        elif message.lower().startswith("mode:"):
            new_mode = message.split(":", 1)[1].strip()
            if new_mode in ["plan", "react"]:
                self.agent.mode = new_mode
                self.update_status(f"Mode changed to {new_mode}")
                chat_history.mount(MessageDisplay("system", f"Mode switched to {new_mode}"))
            else:
                chat_history.mount(MessageDisplay("error", "Invalid mode. Use 'mode:plan' or 'mode:react'"))
            return

        # 处理消息
        await self.process_message(message)

    async def process_message(self, message: str):
        """处理用户消息"""
        self.is_processing = True
        self.update_status("Processing...")

        chat_history = self.query_one("#chat-history", VerticalScroll)

        try:
            if self.agent.mode == "plan":
                await self.process_plan_mode(message, chat_history)
            else:
                await self.process_react_mode(message, chat_history)
        except Exception as e:
            chat_history.mount(MessageDisplay("error", str(e)))
        finally:
            self.is_processing = False
            self.update_status("Ready")

    async def process_plan_mode(self, message: str, chat_history: VerticalScroll):
        """处理计划模式"""
        if message.lower().startswith("add task"):
            task = message[8:].strip()
            if not hasattr(self.agent, "plan_tasks"):
                self.agent.plan_tasks = []
            self.agent.plan_tasks.append(task)
            chat_history.mount(MessageDisplay("system", f"Added task: {task}"))
        elif message.lower().startswith("list tasks"):
            if hasattr(self.agent, "plan_tasks") and self.agent.plan_tasks:
                tasks_text = "\n".join([f"{i+1}. {task}" for i, task in enumerate(self.agent.plan_tasks)])
                chat_history.mount(MessageDisplay("system", f"Current tasks:\n{tasks_text}"))
            else:
                chat_history.mount(MessageDisplay("system", "No tasks in plan"))
        elif message.lower().startswith("execute plan"):
            if hasattr(self.agent, "plan_tasks") and self.agent.plan_tasks:
                chat_history.mount(MessageDisplay("system", "Executing plan..."))
                for i, task in enumerate(self.agent.plan_tasks, 1):
                    chat_history.mount(MessageDisplay("system", f"Task {i}: {task}"))
                chat_history.mount(MessageDisplay("system", "Plan execution completed"))
            else:
                chat_history.mount(MessageDisplay("system", "No tasks to execute"))
        else:
            chat_history.mount(MessageDisplay("system", "Plan mode commands: add task <task>, list tasks, execute plan"))

    async def process_react_mode(self, message: str, chat_history: VerticalScroll):
        """处理 ReACT 模式（带 tool call）"""
        if not self.agent.openai_client:
            chat_history.mount(MessageDisplay("error", "OpenAI client not initialized. Please set OPENAI_API_KEY."))
            return

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
            {"role": "user", "content": message}
        ]

        try:
            # 第一次调用，获取 tool calls
            response = self.agent.openai_client.chat_completion(
                messages=messages,
                tools=self.agent.all_tools_schema
            )
            msg = response.choices[0].message

            # 检查是否有 tool calls
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                # 显示 tool calls
                for tool_call in msg.tool_calls:
                    import json
                    func_name = tool_call.function.name
                    func_args = tool_call.function.arguments
                    chat_history.mount(MessageDisplay("tool_call", f"{func_name}({func_args})"))

                # 添加助手消息到历史
                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [{
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in msg.tool_calls]
                })

                # 执行工具调用
                for tool_call in msg.tool_calls:
                    import json
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # 执行工具
                    if function_name in self.agent.tool_executors:
                        result = self.agent.tool_executors[function_name](function_name, function_args)
                    else:
                        result = f"Error: Tool '{function_name}' not found"

                    chat_history.mount(MessageDisplay("tool_result", str(result)))

                    # 添加工具结果到消息历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })

                # 第二次调用，获取最终响应
                final_response = self.agent.openai_client.chat_completion(
                    messages=messages,
                    tools=self.agent.all_tools_schema
                )
                final_content = final_response.choices[0].message.content
                if final_content:
                    chat_history.mount(MessageDisplay("assistant", final_content))
            else:
                # 没有 tool calls，直接显示响应
                if msg.content:
                    chat_history.mount(MessageDisplay("assistant", msg.content))

        except Exception as e:
            chat_history.mount(MessageDisplay("error", f"Error: {e}"))


def main():
    """TUI 入口函数"""
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "openrouter/hunter-alpha"
    app = BabyAgentTUI(model=model)
    app.run()


if __name__ == "__main__":
    main()
