# Visão Geral do Sistema

## Nome

Severino BOT

## Tipo

Aplicação RAG — Retrieval-Augmented Generation.

## Objetivo

Permitir consultas em linguagem natural sobre atos normativos armazenados em arquivos estruturados.

## Tecnologias principais

- Python
- Chainlit
- LlamaIndex
- ChromaDB
- HuggingFace Embeddings
- OpenRouter
- Pandas

## Escopo

O sistema deve:

1. carregar documentos;
2. normalizar registros;
3. criar chunks;
4. gerar embeddings;
5. persistir vetores;
6. receber perguntas;
7. recuperar contexto relevante;
8. montar prompt RAG;
9. consultar LLM;
10. apresentar resposta ao usuário.

## Fora do escopo atual

- autenticação;
- autorização;
- upload pela interface;
- histórico persistente de conversação;
- API REST própria;
- monitoramento avançado;
- administração do banco vetorial pela interface.
