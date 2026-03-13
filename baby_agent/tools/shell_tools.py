import subprocess
from typing import Dict, Any

class ShellTools:
    """Shell命令工具类 - 支持 OpenAI tool call"""

    # OpenAI tool schema
    TOOLS_SCHEMA = [
        {
            "type": "function",
            "function": {
                "name": "shell_run",
                "description": "执行系统shell命令，支持运行各种系统命令如ls、cat、grep、python等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的shell命令"
                        },
                        "cwd": {
                            "type": "string",
                            "description": "命令执行的工作目录，默认为当前目录",
                            "default": "."
                        }
                    },
                    "required": ["command"]
                }
            }
        }
    ]

    def run(self, command: str, cwd: str = '.') -> Dict[str, Any]:
        """执行系统shell命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': 'Command timed out after 60 seconds',
                'returncode': 1
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': f'Error executing command: {e}',
                'returncode': 1
            }

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """根据工具名称执行对应的shell操作"""
        if tool_name == "shell_run":
            result = self.run(
                arguments.get("command", ""),
                arguments.get("cwd", ".")
            )
            output = []
            if result['stdout']:
                output.append(f"stdout:\n{result['stdout']}")
            if result['stderr']:
                output.append(f"stderr:\n{result['stderr']}")
            output.append(f"returncode: {result['returncode']}")
            return "\n".join(output)
        else:
            return f"Unknown shell tool: {tool_name}"
