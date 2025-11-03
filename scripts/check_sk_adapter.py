"""Verificar a assinatura do SKChatCompletionAdapter."""
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
import inspect

print("SKChatCompletionAdapter.__init__ signature:")
print(inspect.signature(SKChatCompletionAdapter.__init__))
print("\n")

print("Verificando se tem capabilities():")
if hasattr(SKChatCompletionAdapter, 'capabilities'):
    print("✅ Tem método capabilities")
else:
    print("❌ Não tem método capabilities")

print("\nVerificando model_capabilities:")
sig = inspect.signature(SKChatCompletionAdapter.__init__)
for param in sig.parameters:
    print(f"  - {param}: {sig.parameters[param].annotation}")
