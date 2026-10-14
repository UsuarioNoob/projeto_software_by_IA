# Resultado do RAG por Assunto e Ementa

## Objetivo

Melhorar respostas para perguntas temáticas amplas, por exemplo:

> Me informe tudo o que você sabe sobre férias.

Quando existirem documentos relacionados, o sistema não deve responder apenas que não possui
informação. Ele deve recuperar as ocorrências existentes na base, produzir uma síntese baseada
nelas e apresentar somente a resposta objetiva solicitada.

## Campos pesquisados

A recuperação deve considerar prioritariamente:

- `Assunto`;
- `Ementa`.

Esses campos participam tanto do texto vetorizado quanto dos metadados persistidos no ChromaDB.

## Estratégia de recuperação

O retrieval é híbrido:

1. normaliza a pergunta, removendo diferenças de caixa, acentuação e pontuação;
2. remove termos genéricos da solicitação, preservando o tema pesquisado;
3. pontua e ordena as correspondências textuais em `Assunto` e `Ementa` pela quantidade de termos
   temáticos cobertos;
4. executa também a busca semântica configurada por `TOP_K`;
5. prioriza as correspondências textuais e acrescenta os resultados semânticos;
6. remove repetições de chunks pertencentes ao mesmo documento.

Correspondências textuais diretas não ficam limitadas ao `TOP_K`, pois pedidos como “tudo sobre”
devem considerar todos os documentos explicitamente relacionados ao tema. O `TOP_K` é aplicado à
parcela semântica, que é executada mesmo quando existem correspondências textuais. Essa combinação
fornece contexto mais amplo ao modelo sem alterar a interface, que continua sem lista automática de
fontes.

## Formato da resposta

A resposta deve:

- usar exclusivamente o contexto recuperado da base documental;
- sintetizar as informações encontradas em `Assunto` e `Ementa`;
- para pedidos amplos, considerar todos os documentos recuperados;
- não exibir uma seção automática de fontes ou `Documentos relacionados`;
- mencionar tipo, número, assunto ou URL somente quando esses dados forem necessários para responder
  diretamente à pergunta do usuário.

## Ausência de resultados

A mensagem de contexto insuficiente deve ser usada quando:

- a recuperação não fornecer conteúdo documental;
- a pergunta for aleatória ou estiver fora do escopo dos atos normativos;
- os trechos recuperados por proximidade vetorial não sustentarem a resposta solicitada.

Como uma busca vetorial sempre pode retornar os vizinhos mais próximos, mesmo quando são
irrelevantes, o LLM deve validar se o contexto realmente responde à pergunta. Quando não responder,
ele deve retornar o sinal interno `[SEM_INFORMACAO_RELEVANTE]`.

O sinal interno não deve ser exibido ao usuário. O orquestrador deve substituí-lo por uma resposta
curta e remover o contexto:

```text
Não encontrei essa informação na base de atos normativos disponível. Posso ajudar com informações
presentes nos documentos indexados, como tipo e número do ato, assunto, ementa, situação, data e
número do diário e link para o documento.
```

Nesse cenário, o sistema não deve resumir os vizinhos vetoriais, listar documentos sem relação com
a pergunta, recorrer a conhecimento externo ou inventar dados para substituir conteúdo ausente.

## Reindexação

Como `Assunto`, `Ementa` e `documento_id` passaram a integrar os metadados, o formato interno do
índice foi versionado. Na primeira inicialização após esta melhoria, o fingerprint será diferente
e a base vetorial será reconstruída automaticamente.

Arquivos temporários do Excel iniciados por `~$` não participam do carregamento nem do fingerprint,
pois não representam documentos da base e podem estar bloqueados enquanto uma planilha está aberta.

## Inicialização da aplicação

A configuração, a conexão com o ChromaDB, a validação do fingerprint e uma eventual reindexação
devem ocorrer no evento `on_app_startup` do Chainlit.

O servidor somente deve concluir sua inicialização, anunciar a URL e abrir a interface após a base
vetorial estar pronta. O evento `on_chat_start` não deve preparar novamente o ChromaDB; ele apenas
associa à sessão o estado global já validado.

Se a preparação da base falhar, a exceção deve interromper o startup. O sistema não deve apresentar
um chat aparentemente disponível sem uma base vetorial operacional.

Essa preparação ocorre uma vez por processo da aplicação. Novas conversas e novos usuários devem
reutilizar a mesma conexão e o mesmo modelo de embedding preparados no startup.

## Critérios de aceite

1. Uma pergunta contendo “férias” recupera registros em que o termo esteja no `Assunto`.
2. A mesma pergunta recupera registros em que o termo esteja na `Ementa`.
3. Todas as correspondências textuais diretas são retornadas, ainda que superem o `TOP_K`.
4. Chunks pertencentes ao mesmo documento não geram itens duplicados na lista.
5. A interface não acrescenta lista automática de documentos, fontes ou URLs à resposta.
6. A síntese continua limitada ao conteúdo recuperado da base.
7. O índice anterior é invalidado e reconstruído automaticamente.
8. A interface somente fica disponível após o ChromaDB estar preparado.
9. Abrir uma nova conversa não repete a preparação ou a reindexação da base.
10. Uma pergunta aleatória ou fora do escopo recebe apenas a mensagem curta de indisponibilidade.
11. Resultados vetoriais sem relação real não são apresentados ao usuário.
12. A resposta fora do escopo esclarece resumidamente quais informações existem na base.
13. A busca semântica é executada e combinada com a textual mesmo quando existem correspondências
    diretas em `Assunto` ou `Ementa`.