@echo off
rem Claude Code hook wrapper for lib\model_gate.py via the policy-allowed Python.
call "%~dp0python.cmd" python "%~dp0lib\model_gate.py"
exit /b %errorlevel%
