@echo off
rem Build both optional native extensions with cargo (no venv, no uv, no pip) and
rem drop the resulting modules next to their Python packages.
call "%~dp0python.cmd" python "%~dp0build_native.py" %*
exit /b %errorlevel%
