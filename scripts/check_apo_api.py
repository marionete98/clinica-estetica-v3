"""Check APO API structure"""
import agentlightning
print(f"Agent Lightning version: {agentlightning.__version__}")
print(f"\nAvailable modules: {dir(agentlightning)}")

try:
    from agentlightning.algorithm import apo
    print(f"\nAPO module contents: {dir(apo)}")
except Exception as e:
    print(f"\nError importing APO: {e}")

try:
    from agentlightning import Trainer
    print(f"\nTrainer available: Yes")
except Exception as e:
    print(f"\nTrainer import error: {e}")
