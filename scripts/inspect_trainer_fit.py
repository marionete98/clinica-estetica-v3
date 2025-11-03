import inspect
from agentlightning.trainer import Trainer
print('Trainer.__init__:', inspect.signature(Trainer.__init__))
print('Trainer.fit:', inspect.signature(Trainer.fit))
try:
    src = inspect.getsource(Trainer.fit)
    print('Trainer.fit source (first 1200 chars):\n', src[:1200])
except Exception as e:
    print('Could not get source for Trainer.fit:', e)
