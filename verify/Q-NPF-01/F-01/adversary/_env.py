import sys
print(sys.version)
try:
    import numpy; print("numpy", numpy.__version__)
except Exception as e: print("numpy MISSING", e)
try:
    import sympy; print("sympy", sympy.__version__)
except Exception as e: print("sympy MISSING", e)
