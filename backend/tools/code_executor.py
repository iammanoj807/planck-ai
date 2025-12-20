"""
Code Executor Tool

This module run code in a safe(ish) local environment.
Supported languages: Python, JavaScript, Java, C, C++, C#, Go, Rust, TypeScript.

WARNING: This is a risky tool if not sandboxed. In this demo, it runs on the host machine.
Python runs in-process (restricted).
Others run via subprocess.
"""
import sys
import io
import traceback
import json
import subprocess
import tempfile
import os
import re
from typing import Dict, Any, Optional
from contextlib import redirect_stdout, redirect_stderr


def code_executor_tool(code: str, language: str = "python") -> str:
    """
    Executes code in the specified language and returns the standard output.
    
    Args:
        code (str): Source code to execute.
        language (str): python, javascript, java, c, cpp, csharp, go, rust, typescript
        
    Returns:
        str: Captured stdout/stderr or error message.
    """
    language = language.lower()
    
    result = {
        "code": code,
        "language": language,
        "stdout": "",
        "stderr": "",
        "result": None,
        "error": None,
        "success": False
    }

    try:
        if language == "python":
            return _execute_python(code, result)
        elif language in ["javascript", "js", "node"]:
            return _execute_javascript(code, result)
        elif language == "typescript":
            return _execute_typescript(code, result)
        elif language == "java":
            return _execute_java(code, result)
        elif language == "c":
            return _execute_c(code, result)
        elif language in ["cpp", "c++"]:
            return _execute_cpp(code, result)
        elif language in ["csharp", "c#"]:
            return _execute_csharp(code, result)
        elif language == "go":
            return _execute_go(code, result)
        elif language == "rust":
            return _execute_rust(code, result)
        else:
            return json.dumps({"error": f"Unsupported language: {language}"})

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        result["stderr"] = traceback.format_exc()
        return json.dumps(result, indent=2)


def _execute_python(code: str, result: Dict[str, Any]) -> str:
    """Executes Python code in-process using exec()."""
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    safe_builtins = {
        'print': print, 'len': len, 'range': range, 'str': str, 'int': int,
        'float': float, 'bool': bool, 'list': list, 'dict': dict, 'tuple': tuple,
        'set': set, 'sum': sum, 'min': min, 'max': max, 'abs': abs,
        'round': round, 'sorted': sorted, 'reversed': reversed, 'enumerate': enumerate,
        'zip': zip, 'map': map, 'filter': filter, 'type': type,
        'isinstance': isinstance, 'True': True, 'False': False, 'None': None,
    }
    import math
    safe_builtins['math'] = math
    exec_globals = {'__builtins__': safe_builtins}
    exec_locals = {}
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                exec_result = eval(code, exec_globals, exec_locals)
                result["result"] = str(exec_result) if exec_result is not None else None
            except SyntaxError:
                exec(code, exec_globals, exec_locals)
                
        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()
        result["success"] = True
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        result["stderr"] = traceback.format_exc()
        
    return json.dumps(result, indent=2)


def _run_subprocess(cmd: list, cwd: str = None, timeout: int = 15) -> tuple[str, str, int]:
    """Helper to run subprocess and handle common errors."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Execution timed out", -1
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", -1


def _execute_javascript(code: str, result: Dict[str, Any]) -> str:
    with tempfile.NamedTemporaryFile(suffix=".js", mode="w+", delete=True) as temp:
        temp.write(code)
        temp.flush()
        stdout, stderr, rc = _run_subprocess(["node", temp.name])
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0
        if rc != 0: result["error"] = "Execution failed"
    return json.dumps(result, indent=2)


def _execute_typescript(code: str, result: Dict[str, Any]) -> str:
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w+", delete=True) as temp:
        temp.write(code)
        temp.flush()
        # npx ts-node, assumes installed
        stdout, stderr, rc = _run_subprocess(["npx", "ts-node", temp.name])
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0
        if rc != 0: result["error"] = "Execution failed (ensure ts-node is installed)"
    return json.dumps(result, indent=2)


def _execute_java(code: str, result: Dict[str, Any]) -> str:
    match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = match.group(1) if match else "Main"
    if "class " not in code:
         code = f"public class Main {{ public static void main(String[] args) {{ {code} }} }}"

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, f"{class_name}.java")
        with open(file_path, "w") as f: f.write(code)
            
        stdout, stderr, rc = _run_subprocess(["javac", f"{class_name}.java"], cwd=temp_dir)
        if rc != 0:
            result["stderr"] = stderr
            result["error"] = "Compilation Failed"
            return json.dumps(result, indent=2)
            
        stdout, stderr, rc = _run_subprocess(["java", "-cp", ".", class_name], cwd=temp_dir)
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0

    return json.dumps(result, indent=2)


def _execute_c(code: str, result: Dict[str, Any]) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        src = os.path.join(temp_dir, "prog.c")
        exe = os.path.join(temp_dir, "prog")
        with open(src, "w") as f: f.write(code)
        
        stdout, stderr, rc = _run_subprocess(["gcc", "prog.c", "-o", "prog"], cwd=temp_dir)
        if rc != 0:
            result["stderr"] = stderr
            result["error"] = "Compilation Failed"
            return json.dumps(result, indent=2)
            
        stdout, stderr, rc = _run_subprocess([exe], cwd=temp_dir)
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0
    return json.dumps(result, indent=2)


def _execute_cpp(code: str, result: Dict[str, Any]) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        src = os.path.join(temp_dir, "prog.cpp")
        exe = os.path.join(temp_dir, "prog")
        with open(src, "w") as f: f.write(code)
        
        stdout, stderr, rc = _run_subprocess(["g++", "prog.cpp", "-o", "prog"], cwd=temp_dir)
        if rc != 0:
            result["stderr"] = stderr
            result["error"] = "Compilation Failed"
            return json.dumps(result, indent=2)
            
        stdout, stderr, rc = _run_subprocess([exe], cwd=temp_dir)
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0
    return json.dumps(result, indent=2)


def _execute_go(code: str, result: Dict[str, Any]) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        src = os.path.join(temp_dir, "main.go")
        with open(src, "w") as f: 
            if "package main" not in code: code = "package main\n" + code
            f.write(code)
        
        stdout, stderr, rc = _run_subprocess(["go", "run", "main.go"], cwd=temp_dir)
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0
        if rc != 0: result["error"] = "Execution failed"
    return json.dumps(result, indent=2)


def _execute_rust(code: str, result: Dict[str, Any]) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        src = os.path.join(temp_dir, "main.rs")
        exe = os.path.join(temp_dir, "main")
        with open(src, "w") as f: f.write(code)
        
        stdout, stderr, rc = _run_subprocess(["rustc", "main.rs", "-o", "main"], cwd=temp_dir)
        if rc != 0:
            result["stderr"] = stderr
            result["error"] = "Compilation Failed"
            return json.dumps(result, indent=2)
            
        stdout, stderr, rc = _run_subprocess([exe], cwd=temp_dir)
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0
    return json.dumps(result, indent=2)


def _execute_csharp(code: str, result: Dict[str, Any]) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        src = os.path.join(temp_dir, "Program.cs")
        exe = os.path.join(temp_dir, "Program.exe")
        with open(src, "w") as f: f.write(code)
        
        # Use mcs (Mono Compiler)
        stdout, stderr, rc = _run_subprocess(["mcs", "Program.cs"], cwd=temp_dir)
        if rc != 0:
            result["stderr"] = stderr
            result["error"] = "Compilation Failed (Ensure mono-complete is installed)"
            return json.dumps(result, indent=2)
        
        # Run with mono
        stdout, stderr, rc = _run_subprocess(["mono", "Program.exe"], cwd=temp_dir)
        result["stdout"], result["stderr"] = stdout, stderr
        result["success"] = rc == 0
    return json.dumps(result, indent=2)


# Tool definition for LangChain
CODE_EXECUTOR_TOOL_DEF = {
    "name": "code_executor",
    "description": "Execute code in various languages to verify algorithms or perform logic.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The source code to execute"
            },
            "language": {
                "type": "string",
                "description": "Programming language to use",
                "enum": ["python", "javascript", "typescript", "java", "c", "cpp", "csharp", "go", "rust"],
                "default": "python"
            }
        },
        "required": ["code"]
    }
}
