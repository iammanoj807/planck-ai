"""
Code Executor Tool

This module run Python code in a safe(ish) local environment.
It uses the `exec` function, which captures stdout.
WARNING: This is a risky tool if not sandboxed. In this demo, it runs on the host machine.
"""
import sys
import io
import traceback
from typing import Dict, Any
import json
from contextlib import redirect_stdout, redirect_stderr


def code_executor_tool(code: str) -> str:
    """
    Executes Python code and returns the standard output.
    
    Args:
        code (str): valid Python code snippet.
        
    Returns:
        str: Captured stdout or traceback if an error occurs.
    """
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    # Restricted globals - only safe builtins
    safe_builtins = {
        'print': print,
        'len': len,
        'range': range,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'sorted': sorted,
        'reversed': reversed,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'type': type,
        'isinstance': isinstance,
        'True': True,
        'False': False,
        'None': None,
    }
    
    # Add safe math functions
    import math
    safe_builtins['math'] = math
    
    # Execution context
    exec_globals = {'__builtins__': safe_builtins}
    exec_locals = {}
    
    result = {
        "code": code,
        "stdout": "",
        "stderr": "",
        "result": None,
        "error": None,
        "success": False
    }
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Try to evaluate as expression first
            try:
                exec_result = eval(code, exec_globals, exec_locals)
                result["result"] = str(exec_result) if exec_result is not None else None
            except SyntaxError:
                # If not an expression, execute as statements
                exec(code, exec_globals, exec_locals)
                
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()
        result["success"] = True
        
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        result["stderr"] = traceback.format_exc()
        
    return json.dumps(result, indent=2)


# Tool definition for LangChain
CODE_EXECUTOR_TOOL_DEF = {
    "name": "code_executor",
    "description": "Execute Python code and return the output. Use this for calculations, data processing, or generating code examples. The code runs in a sandboxed environment with limited access.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute"
            }
        },
        "required": ["code"]
    }
}
