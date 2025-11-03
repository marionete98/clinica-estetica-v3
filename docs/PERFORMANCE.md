# Benchmarks de Performance

Para aferir a performance da nova arquitetura execute:

```bash
PYENV_VERSION=3.12.10 PYTHONPATH=. python scripts/benchmark_refactor.py
```

### Resultados de 16/11/2025

| Cenário                            | Latência (ms) |
|-----------------------------------|---------------|
| Saudação                          | 50.25         |
| FAQ – preço depilação a laser     | 50.32         |
| Solicitação de agendamento        | 50.30         |
| Verificar horários disponíveis    | 50.36         |

- **Stack:** Stub (dependências LLM indisponíveis no ambiente local)
- **Média:** 50.31 ms
- **Desvio Padrão:** 0.04 ms
- **Min/Max:** 50.25 ms / 50.36 ms

> Para ambientes com todas as dependências instaladas o script utilizará automaticamente o `AgentOrchestrator` real, preservando o mesmo relatório de métricas.【6fcbe4†L1-L10】
