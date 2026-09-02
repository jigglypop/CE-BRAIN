@echo off
rem Claude Code hook wrapper. stdin JSON passes through to lib\safety_screen.py via the policy-allowed Python.
call "%~dp0python.cmd" python "%~dp0lib\safety_screen.py"
exit /b %errorlevel%
