@echo off
REM Run a script with the pinned CE-BRAIN research environment (env\uv.lock).
REM One BLAS / OpenMP thread per process unless already set (results do not depend on the thread count).
setlocal
if not defined OPENBLAS_NUM_THREADS set OPENBLAS_NUM_THREADS=1
if not defined OMP_NUM_THREADS set OMP_NUM_THREADS=1
if not defined MKL_NUM_THREADS set MKL_NUM_THREADS=1
"%~dp0.venv\Scripts\python.exe" %*
