import inspect
from agentlightning.trainer import Trainer
print('has dev:', hasattr(Trainer, 'dev'))
if hasattr(Trainer, 'dev'):
    print('dev signature:', inspect.signature(Trainer.dev))
    try:
        import inspect as _inspect
        print('dev source (first 800):')
        print(_inspect.getsource(Trainer.dev)[:800])
    except Exception as e:
        print('no source:', e)
