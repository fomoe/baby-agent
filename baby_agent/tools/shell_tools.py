import subprocess
from typing import Dict, Any

class ShellTools:
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
