import sys
import io
import contextlib
import multiprocessing
import time
from typing import Dict, Any, Optional

class PythonCodeExecutor:
    """
    A safe(r) local Python code executor for educational purposes.
    
    """
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        
        # Deny-list of dangerous modules
        self.banned_imports = [
            'os', 'sys', 'subprocess', 'shutil', 'net', 'socket', 'urllib', 
            'requests', 'http', 'pickle', 'importlib', 'inspect'
        ]
        
        # Deny-list of dangerous builtins
        self.banned_builtins = [
            'open', 'exec', 'eval', '__import__', 'input', 'exit', 'quit'
        ]

    def _execute_in_process(self, code: str, result_queue: multiprocessing.Queue):
        """
        Worker function to execute code in a separate process.
        """
        # Capture stdout/stderr
        output_buffer = io.StringIO()
        
        # Restricted environment
        safe_globals = {
            "__builtins__": {
                name: getattr(__builtins__, name)
                for name in dir(__builtins__)
                if name not in self.banned_builtins
            }
        }
        
        # Custom importer to block banned modules
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in self.banned_imports:
                raise ImportError(f"Import of '{name}' is restricted for safety.")
            return __import__(name, globals, locals, fromlist, level)
        
        safe_globals["__builtins__"]["__import__"] = safe_import
        
        try:
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                exec(code, safe_globals)
            
            result_queue.put({
                "success": True,
                "output": output_buffer.getvalue()
            })
        except Exception as e:
            result_queue.put({
                "success": False,
                "output": output_buffer.getvalue(),
                "error": str(e),
                "error_type": type(e).__name__
            })

    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute the provided Python code with timeout and restrictions.
        
        Args:
            code: The Python code string to execute.
            
        Returns:
            Dict containing 'success', 'output', and optional 'error'.
        """
        # Basic static analysis for obvious violations
        for banned in self.banned_imports:
            if f"import {banned}" in code or f"from {banned}" in code:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Security Violation: Import of '{banned}' is not allowed."
                }
        
        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=self._execute_in_process, 
            args=(code, result_queue)
        )
        
        start_time = time.time()
        process.start()
        process.join(self.timeout)
        
        if process.is_alive():
            process.terminate()
            process.join()
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {self.timeout} seconds."
            }
        
        if not result_queue.empty():
            return result_queue.get()
        else:
            return {
                "success": False,
                "output": "",
                "error": "Process terminated unexpectedly."
            }

# Async wrapper for the agent
async def execute_code_async(code: str) -> str:
    """
    Executes Python code and returns the result as a JSON string.
    """
    import json
    import asyncio
    
    executor = PythonCodeExecutor()
    
    # Run in thread pool to avoid blocking async loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, executor.execute, code)
    
    return json.dumps(result)
