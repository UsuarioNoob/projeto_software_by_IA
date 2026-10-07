# Componentes

## `main.py`
Responsável pelo bootstrap da aplicação.

## `config.py`
Responsável pela configuração externa.

## `mod_docs.py`
Responsável por:

- leitura de arquivos;
- normalização;
- criação de documentos;
- chunking.

## `mod_embedding.py`
Responsável por:

- criação do modelo de embedding;
- conexão ao ChromaDB;
- indexação;
- carregamento do índice;
- retrieval.

## `mod_orquestrator.py`
Responsável por:

- casos de uso;
- fingerprint;
- preparação da base;
- montagem do contexto;
- fluxo da pergunta.

## `mod_api_ia.py`
Responsável pela integração HTTP com o LLM.

## `mod_ui.py`
Responsável exclusivamente pela interface Chainlit.
