import ast
import os
import shutil
import subprocess
import json
from typing import Optional, Dict, Any


class AutopoiesisEngine:
    def __init__(self):
        self.self_healing_count = 0
    
    def _send_to_mimo(self, code: str, error_log: str) -> Optional[str]:
        """Send code and error log to MiMo API for repair (mock implementation)."""
        # This is a mock implementation
        # In real usage, this would call the actual MiMo API
        try:
            # Simple mock repair: remove the problematic line if it exists
            lines = code.split('\n')
            if len(lines) > 1:
                lines.pop(1)  # Remove second line as mock repair
                return '\n'.join(lines)
            return code
        except Exception:
            return None
    
    def _validate_syntax(self, code: str) -> bool:
        """Validate Python code syntax using ast.parse."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def heal(self, loop_script: str, error_log: str) -> str:
        """
        Send loop_script and error_log to MiMo for repair.
        Validate syntax of returned code and return repaired code.
        """
        repaired_code = self._send_to_mimo(loop_script, error_log)
        
        if repaired_code is None:
            return loop_script
        
        if not self._validate_syntax(repaired_code):
            # If syntax is invalid, try to fix basic issues
            try:
                # Attempt to fix common syntax errors
                fixed_code = self._attempt_syntax_fix(repaired_code)
                if self._validate_syntax(fixed_code):
                    return fixed_code
            except:
                pass
            return loop_script
        
        self.self_healing_count += 1
        return repaired_code
    
    def _attempt_syntax_fix(self, code: str) -> str:
        """Attempt to fix common syntax errors."""
        # Simple fixes for common issues
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix missing parentheses
            if line.count('(') > line.count(')'):
                line = line + ')'
            elif line.count(')') > line.count('('):
                line = '(' + line
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def apply_patch(self, loop_script_path: str, patched_code: str) -> bool:
        """
        Write repaired code to loop_script_path.
        Create backup at loop_script_path + '.bak'.
        """
        try:
            # Create backup
            backup_path = loop_script_path + '.bak'
            if os.path.exists(loop_script_path):
                shutil.copy2(loop_script_path, backup_path)
            
            # Write repaired code
            with open(loop_script_path, 'w', encoding='utf-8') as f:
                f.write(patched_code)
            
            return True
        except Exception as e:
            print(f"Error applying patch: {e}")
            return False
    
    def restart_loop(self, loop_script_path: str, queue_path: str, 
                     failed_module: str) -> None:
        """
        Set failed_module in queue_path to PENDING/iterations=0.
        Start loop_script_path as subprocess.
        """
        try:
            # Update queue file
            if os.path.exists(queue_path):
                with open(queue_path, 'r', encoding='utf-8') as f:
                    try:
                        queue_data = json.load(f)
                    except json.JSONDecodeError:
                        queue_data = {}
                
                # Update module status
                if 'modules' not in queue_data:
                    queue_data['modules'] = {}
                
                queue_data['modules'][failed_module] = {
                    'status': 'PENDING',
                    'iterations': 0
                }
                
                # Save updated queue
                with open(queue_path, 'w', encoding='utf-8') as f:
                    json.dump(queue_data, f, indent=2)
            
            # Start the loop script as subprocess
            if os.path.exists(loop_script_path):
                subprocess.Popen(
                    ['python', loop_script_path],
                    cwd=os.path.dirname(os.path.abspath(loop_script_path))
                )
        except Exception as e:
            print(f"Error restarting loop: {e}")