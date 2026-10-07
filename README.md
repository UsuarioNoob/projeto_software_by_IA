# Severino BOT

Aplicação RAG (Retrieval-Augmented Generation) para consultas em linguagem natural sobre atos normativos armazenados em arquivos estruturados.

## Tecnologias

- Python 3.12
- Chainlit
- LlamaIndex
- ChromaDB persistente
- Hugging Face Embeddings
- OpenRouter
- Pandas
- pytest

## Estrutura

```text
docs/                   documentos que serão indexados
data/                   estado local do pipeline
chroma_db/              banco vetorial local, gerado em execução
src/severino_bot/       código da aplicação
tests/                  testes automatizados
sdd/                    especificação de design
tdd/                    especificação de testes
main.py                 entrada da aplicação
```

## Preparação no Windows

```powershell
py -3.12 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Preencha `OPENROUTER_API_KEY` no arquivo `.env`. Nunca envie esse arquivo ao GitHub.

## Testes

```powershell
python -m pytest -v
python -m pytest --cov=src/severino_bot --cov-report=term-missing
```

## Execução

Após a implementação completa e a configuração do `.env`:

```powershell
chainlit run main.py
```

## Especificações

As decisões e requisitos estão documentados em `sdd/`; a estratégia e os casos de teste estão documentados em `tdd/`.
