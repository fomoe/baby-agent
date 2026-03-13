import os
import glob
from typing import List, Optional

class FileTools:
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
