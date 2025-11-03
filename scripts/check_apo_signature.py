"""Check APO signature"""
from agentlightning import APO
import inspect

print("APO signature:")
print(inspect.signature(APO.__init__))
print("\nAPO docstring:")
print(APO.__doc__)
