import os
import glob
from typing import List, Optional, Dict, Any

class FileTools:
    """文件操作工具类 - 支持 OpenAI tool call"""

    # OpenAI tool schema
    TOOLS_SCHEMA = [
        {
            "type": "function",
            "function": {
                "name": "file_read",
                "description": "读取文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要读取的文件路径"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "file_write",
                "description": "写入文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要写入的文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的文件内容"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "file_edit",
                "description": "编辑文件内容，替换指定字符串",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要编辑的文件路径"
                        },
                        "old_string": {
                            "type": "string",
                            "description": "要被替换的旧字符串"
                        },
                        "new_string": {
                            "type": "string",
                            "description": "用于替换的新字符串"
                        }
                    },
                    "required": ["file_path", "old_string", "new_string"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "file_ls",
                "description": "列出目录内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "要列出的目录路径，默认为当前目录",
                            "default": "."
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "file_grep",
                "description": "在文件中搜索指定模式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "要搜索的模式或字符串"
                        },
                        "path": {
                            "type": "string",
                            "description": "搜索的目录路径，默认为当前目录",
                            "default": "."
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "文件匹配模式，例如 '*.py'，默认为所有文件",
                            "default": "*"
                        }
                    },
                    "required": ["pattern"]
                }
            }
        }
    ]

    def read(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def write(self, file_path: str, content: str) -> str:
        """写入文件内容"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def edit(self, file_path: str, old_string: str, new_string: str) -> str:
        """编辑文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_string not in content:
                return f"Old string not found in {file_path}"

            new_content = content.replace(old_string, new_string)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"Successfully edited {file_path}"
        except Exception as e:
            return f"Error editing file: {e}"

    def ls(self, directory: str = '.') -> List[str]:
        """列出目录内容"""
        try:
            entries = os.listdir(directory)
            return entries
        except Exception as e:
            return [f"Error listing directory: {e}"]

    def grep(self, pattern: str, path: str = '.', file_pattern: str = '*') -> List[str]:
        """搜索文件内容"""
        results = []
        try:
            for file_path in glob.glob(os.path.join(path, '**', file_pattern), recursive=True):
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                if pattern in line:
                                    results.append(f"{file_path}:{line_num}: {line.strip()}")
                    except:
                        pass
            return results
        except Exception as e:
            return [f"Error searching files: {e}"]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """根据工具名称执行对应的文件操作"""
        if tool_name == "file_read":
            return self.read(arguments.get("file_path", ""))
        elif tool_name == "file_write":
            return self.write(arguments.get("file_path", ""), arguments.get("content", ""))
        elif tool_name == "file_edit":
            return self.edit(
                arguments.get("file_path", ""),
                arguments.get("old_string", ""),
                arguments.get("new_string", "")
            )
        elif tool_name == "file_ls":
            result = self.ls(arguments.get("directory", "."))
            return "\n".join(result) if isinstance(result, list) else str(result)
        elif tool_name == "file_grep":
            result = self.grep(
                arguments.get("pattern", ""),
                arguments.get("path", "."),
                arguments.get("file_pattern", "*")
            )
            return "\n".join(result) if isinstance(result, list) else str(result)
        else:
            return f"Unknown file tool: {tool_name}"
