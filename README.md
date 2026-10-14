# Severino BOT

Assistente RAG (*Retrieval-Augmented Generation*) para consultas em linguagem natural sobre atos normativos armazenados em arquivos estruturados.

O Severino BOT carrega e valida os documentos, cria uma base vetorial persistente no ChromaDB, combina busca textual por **Assunto/Ementa** com busca semântica e utiliza um modelo acessado pelo OpenRouter para produzir respostas fundamentadas exclusivamente no conteúdo indexado.

## Principais recursos

- interface conversacional em português com Chainlit;
- leitura de arquivos CSV, Excel, JSON e Parquet;
- validação obrigatória do schema documental;
- normalização de valores, datas e metadados;
- chunking determinístico com LlamaIndex;
- embeddings multilíngues executados localmente;
- ChromaDB persistente;
- fingerprint dos documentos e parâmetros para reindexação automática;
- recuperação híbrida por correspondência textual e similaridade semântica;
- combinação de correspondências textuais e resultados semânticos sem duplicidade;
- uso interno dos documentos recuperados para fundamentar a resposta, sem exibir uma lista
  automática de fontes;
- respostas limitadas ao contexto documental recuperado;
- descarte de fontes irrelevantes quando a pergunta está fora do escopo;
- preparação completa da base antes de o Chainlit disponibilizar a interface;
- suíte automatizada com 114 testes e cobertura superior a 87%.

## Como funciona

### Inicialização e indexação

```text
Arquivos em docs/
        |
        v
Validação e normalização
        |
        v
Criação de chunks
        |
        v
Embeddings multilíngues
        |
        v
ChromaDB persistente
```

No startup, a aplicação calcula um fingerprint a partir dos arquivos e dos parâmetros que alteram semanticamente o índice. Quando nada mudou, a coleção existente é reutilizada. Se os documentos, o modelo de embedding, o chunking ou a versão do schema mudarem, a base é reconstruída automaticamente.

O Chainlit só anuncia a interface depois que essa preparação termina com sucesso.

### Consulta RAG

```text
Pergunta
   |
   v
busca textual em Assunto e Ementa
   |
   +--> correspondências textuais
   |
   `--> busca semântica (TOP_K)
             |
             v
     combinação sem duplicidades
             |
             v
       contexto documental
             |
             v
      OpenRouter / modelo LLM
             |
             v
        resposta objetiva
```

Correspondências textuais diretas são priorizadas e não ficam limitadas ao `TOP_K`. A busca semântica é executada em todas as consultas e acrescenta até o limite configurado, sem repetir documentos já encontrados textualmente. Isso amplia o contexto disponível ao modelo e evita que perguntas sejam bloqueadas por uma correspondência lexical excessivamente restrita.

Os documentos recuperados permanecem no contexto interno usado pelo modelo, mas a interface não
acrescenta a seção automática `Documentos relacionados`. Identificadores de atos aparecem somente
quando forem necessários para responder diretamente ao que o usuário perguntou.

Se o contexto não sustentar a resposta, o bot não utiliza conhecimento externo e não apresenta vizinhos vetoriais irrelevantes. Ele informa de forma curta que o conteúdo não foi encontrado na base disponível.

## Tecnologias

- Python 3.12+
- Chainlit
- ChromaDB
- LlamaIndex
- Hugging Face Embeddings
- OpenRouter
- Pandas
- pytest e pytest-cov

## Requisitos

- Python `>=3.12,<3.14`;
- acesso à internet na primeira execução para baixar o modelo de embedding;
- chave de API do OpenRouter para gerar as respostas;
- arquivos estruturados seguindo o contrato de dados descrito abaixo.

## Instalação

### Windows PowerShell

```powershell
git clone https://github.com/UsuarioNoob/projeto_software_by_IA.git
cd projeto_software_by_IA

py -3.12 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Para instalar também as dependências de desenvolvimento e testes:

```powershell
python -m pip install -r requirements-dev.txt
```

### Linux ou macOS

```bash
git clone https://github.com/UsuarioNoob/projeto_software_by_IA.git
cd projeto_software_by_IA

python3.12 -m venv env
source env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

## Configuração

Copie `.env.example` para `.env` e preencha pelo menos:

```env
OPENROUTER_API_KEY=sua_chave
```

Variáveis disponíveis:

| Variável | Valor padrão | Finalidade |
|---|---|---|
| `OPENROUTER_API_KEY` | vazio | Credencial utilizada nas consultas ao OpenRouter. |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Modelo de linguagem solicitado ao OpenRouter. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | URL-base da API. |
| `DOCUMENTS_DIR` | `docs` | Diretório dos documentos estruturados. |
| `CHROMA_DIR` | `chroma_db` | Diretório local do ChromaDB persistente. |
| `CHROMA_COLLECTION` | `severino_bot` | Nome da coleção vetorial. |
| `FINGERPRINT_FILE` | `data/fingerprint.json` | Estado usado para detectar necessidade de reindexação. |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Modelo local de embeddings. |
| `CHUNK_SIZE` | `512` | Tamanho máximo dos chunks. |
| `CHUNK_OVERLAP` | `64` | Sobreposição entre chunks. |
| `TOP_K` | `10` | Quantidade máxima da parcela semântica da busca. |
| `REQUEST_TIMEOUT_SECONDS` | `30` | Timeout das requisições ao OpenRouter. |
| `SCHEMA_VERSION` | `1` | Versão externa do contrato documental. |
| `LOG_LEVEL` | `INFO` | Nível de logging da aplicação. |

> Nunca publique o arquivo `.env` nem inclua chaves de API no código, em commits ou em capturas de tela.

## Preparação dos documentos

Coloque os arquivos no diretório `docs/`. Formatos aceitos:

- `.csv`;
- `.xls`, `.xlsx` e `.xlsm`;
- `.json`;
- `.parquet`.

Cada arquivo deve conter os seguintes campos obrigatórios:

| Campo | Uso principal |
|---|---|
| `Tipo` | Texto indexado e metadados. |
| `Número do Documento` | Identificação do ato. |
| `Assunto` | Recuperação textual e semântica. |
| `Ementa` | Recuperação textual e semântica. |
| `Situação` | Conteúdo e metadados. |
| `Data do Diário` | Metadados. |
| `Número Diário` | Metadados. |
| `Link web` | Link exibido nos documentos relacionados. |

Arquivos temporários do Excel iniciados por `~$` são ignorados. Se qualquer arquivo suportado possuir schema inválido, a preparação falha explicitamente e a interface não é disponibilizada.

Os documentos reais, o índice vetorial e o fingerprint são dados locais e estão protegidos pelo `.gitignore`.

## Execução

Com o ambiente virtual ativo, a configuração preenchida e os documentos em `docs/`:

```powershell
chainlit run main.py
```

Para recarregar automaticamente durante o desenvolvimento:

```powershell
chainlit run main.py -w
```

A primeira inicialização pode demorar devido ao download do modelo de embedding e à criação do índice. Inicializações posteriores reutilizam a coleção quando o fingerprint não mudou.

## Exemplos de uso

Perguntas relacionadas à base:

```text
O que existe sobre férias?
Quais atos tratam de licença?
Qual é a situação do documento 123/2026?
Mostre os atos relacionados ao assunto informado.
```

As respostas não exibem uma lista automática de fontes. Perguntas fora do conteúdo indexado recebem
uma resposta curta e também não apresentam documentos irrelevantes.

## Testes e qualidade

Executar toda a suíte:

```powershell
python -m pytest -v
```

Executar com cobertura:

```powershell
python -m pytest --cov=src/severino_bot --cov-report=term-missing
```

Resultado da validação final do projeto:

- **114 testes aprovados**;
- **87,33% de cobertura**;
- limite mínimo de cobertura configurado em **80%**;
- compilação dos módulos sem erros.

## Estrutura do repositório

```text
.
|-- .chainlit/              configuração da interface
|-- chroma_db/              banco vetorial local gerado em execução
|-- data/                   fingerprint local da indexação
|-- docs/                   documentos locais a serem indexados
|-- sdd/                    especificação e decisões de design
|-- src/severino_bot/       código-fonte da aplicação
|-- tdd/                    estratégia e especificação de testes
|-- tests/                  testes automatizados
|-- .env.example            modelo de configuração
|-- main.py                 ponto de entrada do Chainlit
|-- pyproject.toml          dependências e configuração do projeto
`-- README.md               documentação principal
```

## Módulos principais

| Módulo | Responsabilidade |
|---|---|
| `config.py` | Carregamento e validação das configurações externas. |
| `mod_docs.py` | Leitura, schema, normalização, texto indexável e chunks. |
| `mod_embedding.py` | Embeddings, ChromaDB, indexação e recuperação híbrida. |
| `mod_api_ia.py` | Cliente HTTP e contrato de resposta do OpenRouter. |
| `mod_orquestrator.py` | Fingerprint, preparação da base e fluxo RAG. |
| `mod_ui.py` | Ciclo de vida e mensagens da interface Chainlit. |

## Segurança e privacidade

- `.env`, documentos reais, ChromaDB e fingerprint não são versionados;
- a chave do OpenRouter permanece no servidor e não é enviada à interface;
- o bot não deve inventar dados ou complementar respostas com conhecimento externo;
- a aplicação falha antes de abrir o chat quando a base documental não pode ser preparada;
- HTML inseguro, MCP, compartilhamento de threads e persistência de variáveis de usuário permanecem desabilitados.

Antes de uma implantação institucional, recomenda-se adicionar autenticação, autorização, histórico persistente, política de retenção, backup e controles de acesso aos documentos.

## Limitações atuais

- não possui autenticação ou perfis de acesso;
- não persiste o histórico das conversas;
- não permite upload e administração da base pela interface;
- depende do OpenRouter para gerar a resposta final;
- a qualidade depende do conteúdo e da padronização dos documentos fornecidos;
- respostas de continuação não utilizam automaticamente as mensagens anteriores como memória do LLM.

## Documentação técnica

- [`sdd/00_INDEX.md`](sdd/00_INDEX.md): requisitos, arquitetura, contratos, fluxos e decisões;
- [`sdd/13_RESULTADOS_RAG.md`](sdd/13_RESULTADOS_RAG.md): recuperação por Assunto/Ementa e tratamento fora do escopo;
- [`tdd/00_INDEX.md`](tdd/00_INDEX.md): estratégia, casos de teste e rastreabilidade.

## Estado do projeto

O escopo local planejado está concluído e validado. Persistência de chats e autenticação foram mantidas fora do escopo atual e podem ser acrescentadas em uma futura implantação institucional.
