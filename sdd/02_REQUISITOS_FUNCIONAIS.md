# Requisitos Funcionais

## RF-001 — Carregamento documental
O sistema deve carregar automaticamente os arquivos válidos presentes na pasta `docs/`.

## RF-002 — Formatos suportados
O sistema deve suportar:

- CSV
- XLS
- XLSX
- XLSM
- JSON
- Parquet

## RF-003 — Consolidação
O sistema deve consolidar múltiplas fontes em uma coleção lógica única.

## RF-004 — Criação de chunks
Os registros devem ser convertidos em documentos e fragmentados conforme a configuração definida.

## RF-005 — Geração de embeddings
Cada chunk deve possuir representação vetorial.

## RF-006 — Persistência vetorial
Os embeddings devem ser persistidos no ChromaDB.

## RF-007 — Detecção de alteração
O sistema deve detectar alteração nos documentos e parâmetros relevantes da indexação.

## RF-008 — Reindexação
O sistema deve reconstruir o índice quando o fingerprint mudar.

## RF-009 — Reutilização
O sistema não deve reindexar quando o fingerprint permanecer igual.

## RF-010 — Consulta
O usuário deve poder enviar uma pergunta em linguagem natural.

## RF-011 — Retrieval
O sistema deve recuperar os chunks semanticamente mais relevantes.

## RF-012 — Construção de contexto
Os resultados recuperados devem formar um contexto estruturado.

## RF-013 — Consulta ao LLM
O contexto e a pergunta devem ser enviados ao modelo de linguagem.

## RF-014 — Controle de alucinação
O LLM deve ser instruído a responder apenas com base no contexto fornecido.

## RF-015 — Tratamento de falhas
Falhas de rede, índice, schema ou LLM devem ser tratadas.

## RF-016 — Exibição
A resposta deve ser apresentada na interface Chainlit.
