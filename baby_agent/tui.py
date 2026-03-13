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
from textual.worker import Worker
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from baby_agent.agent import BabyAgent


class MessageDisplay(Static):
    """消息显示组件"""

    def __init__(self, role: str, content: str = "", **kwargs):
        self.role = role
        self.message_content = content
        super().__init__(**kwargs)
        self.add_class(f"{role}-message")

    def compose(self) -> ComposeResult:
        if self.role == "user":
            yield Label(Text(f"You: {self.message_content}", style="bold cyan"))
        elif self.role == "assistant":
            self.assistant_label = Label(Text(f"Agent: {self.message_content}", style="bold green"))
            yield self.assistant_label
        elif self.role == "tool_call":
            yield Label(Text(f"🔧 Tool Call: {self.message_content}", style="bold yellow"))
        elif self.role == "tool_result":
            yield Label(Text(f"📋 Result: {self.message_content[:500]}{'...' if len(self.message_content) > 500 else ''}", style="dim"))
        elif self.role == "system":
            yield Label(Text(f"ℹ️  {self.message_content}", style="italic dim"))
        elif self.role == "error":
            yield Label(Text(f"❌ Error: {self.message_content}", style="bold red"))

    def update_content(self, content: str):
        """更新消息内容（用于流式输出）"""
        self.message_content = content
        if self.role == "assistant" and hasattr(self, 'assistant_label'):
            self.assistant_label.update(Text(f"Agent: {content}", style="bold green"))


class StreamingMessageDisplay(Static):
    """支持流式输出的消息显示组件"""

    def __init__(self, **kwargs):
        self.message_content = ""
        super().__init__(**kwargs)
        self.add_class("agent-message")

    def compose(self) -> ComposeResult:
        self.label = Label(Text("Agent: ", style="bold green"))
        yield self.label

    def append_text(self, text: str):
        """追加文本内容"""
        self.message_content += text
        self.label.update(Text(f"Agent: {self.message_content}", style="bold green"))

    def set_content(self, content: str):
        """设置完整内容"""
        self.message_content = content
        self.label.update(Text(f"Agent: {content}", style="bold green"))


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
        """处理 ReACT 模式（带 tool call），支持流式输出"""
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
            # 使用流式 API 处理整个对话
            await self._stream_with_tools(messages, chat_history)
        except Exception as e:
            chat_history.mount(MessageDisplay("error", f"Error: {e}"))

    async def _stream_with_tools(self, messages: list, chat_history: VerticalScroll):
        """流式处理对话，支持 tool calls"""
        import json

        # 创建流式显示组件
        streaming_display = StreamingMessageDisplay()
        await chat_history.mount(streaming_display)

        # 用于收集完整响应
        full_content = ""
        tool_calls_data = []
        current_tool_call = None
        has_tool_calls = False

        # 第一次流式调用
        stream = self.agent.openai_client.stream_chat_completion(
            messages=messages,
            tools=self.agent.all_tools_schema
        )

        for chunk in stream:
            if hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta

                # 处理普通内容
                if hasattr(delta, 'content') and delta.content:
                    content = delta.content
                    full_content += content
                    streaming_display.append_text(content)
                    await asyncio.sleep(0.001)

                # 处理 tool calls
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    has_tool_calls = True
                    for tc in delta.tool_calls:
                        if tc.index is not None:
                            # 确保列表足够长
                            while len(tool_calls_data) <= tc.index:
                                tool_calls_data.append({"id": "", "function": {"name": "", "arguments": ""}})

                            current_tool_call = tool_calls_data[tc.index]

                            if tc.id:
                                current_tool_call["id"] = tc.id
                            if tc.function and tc.function.name:
                                current_tool_call["function"]["name"] = tc.function.name
                            if tc.function and tc.function.arguments:
                                current_tool_call["function"]["arguments"] += tc.function.arguments

        # 如果有 tool calls，执行它们并继续流式输出
        if has_tool_calls and tool_calls_data:
            # 清除流式显示（因为 tool call 不需要流式显示）
            streaming_display.set_content("(使用工具中...)")

            # 显示 tool calls
            for tc in tool_calls_data:
                func_name = tc["function"]["name"]
                func_args = tc["function"]["arguments"]
                chat_history.mount(MessageDisplay("tool_call", f"{func_name}({func_args})"))

            # 添加助手消息到历史
            messages.append({
                "role": "assistant",
                "content": full_content,
                "tool_calls": [{
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"]
                    }
                } for tc in tool_calls_data]
            })

            # 执行工具调用
            for tc in tool_calls_data:
                function_name = tc["function"]["name"]
                try:
                    function_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    function_args = {}

                # 执行工具
                if function_name in self.agent.tool_executors:
                    result = self.agent.tool_executors[function_name](function_name, function_args)
                else:
                    result = f"Error: Tool '{function_name}' not found"

                chat_history.mount(MessageDisplay("tool_result", str(result)))

                # 添加工具结果到消息历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result)
                })

            # 移除临时的"使用工具中..."消息，创建新的流式显示
            await streaming_display.remove()
            await self._stream_response(messages, chat_history)
        else:
            # 没有 tool calls，流式输出已经完成
            pass

    async def _stream_response(self, messages: list, chat_history: VerticalScroll):
        """流式输出 AI 响应（第二次调用，在 tool call 之后）"""
        # 创建流式显示组件
        streaming_display = StreamingMessageDisplay()
        await chat_history.mount(streaming_display)

        try:
            # 使用流式 API
            stream = self.agent.openai_client.stream_chat_completion(
                messages=messages,
                tools=self.agent.all_tools_schema
            )

            full_content = ""
            for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        full_content += content
                        streaming_display.append_text(content)
                        # 小延迟让 UI 有更新的机会
                        await asyncio.sleep(0.001)

            # 如果没有获取到任何内容，显示提示
            if not full_content:
                streaming_display.set_content("(No response)")

        except Exception as e:
            streaming_display.set_content(f"Error during streaming: {e}")


def main():
    """TUI 入口函数"""
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "openrouter/hunter-alpha"
    app = BabyAgentTUI(model=model)
    app.run()


if __name__ == "__main__":
    main()
