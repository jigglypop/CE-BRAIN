@echo off
rem Claude Code hook wrapper for libio_budget.py via the policy-allowed Python.
call "%~dp0python.cmd" python "%~dp0libio_budget.py"
exit /b %errorlevel%
