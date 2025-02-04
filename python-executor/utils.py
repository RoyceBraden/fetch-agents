import sys
from io import StringIO

def execute_code(code):
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        exec(code)
        result = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    return result