from langchain_core.tools import tool

@tool
def multiplication(a, b):
    """Multiplies two numbers."""
    print(f"Multiplying {a} and {b}")
    return a * b


tools = [multiplication]