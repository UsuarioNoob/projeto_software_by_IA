# Fluxos do Sistema

## Inicialização

```text
chainlit run main.py
  |
  v
registrar handlers
  |
  v
on_app_startup()
  |
  v
preparar_base_vetorial()
  |
  +--> carregar configuração
  |
  +--> conectar ao ChromaDB
  |
  +--> calcular e comparar fingerprint
  |
  +--> reindexar ou reutilizar índice
  |
  v
base pronta
  |
  v
servidor anuncia a URL e disponibiliza a interface
```

Uma falha na preparação interrompe o startup. O chat não deve ser disponibilizado
sem uma base vetorial operacional.

## Nova conversa

```text
on_chat_start()
  |
  +--> reutilizar configuração global
  |
  +--> reutilizar ChromaDB e modelo de embedding preparados
  |
  v
habilitar interação da sessão
```

## Consulta

```text
Usuário
  |
  v
mod_ui
  |
  v
responder_pergunta()
  |
  v
buscar_chunks()
  |
  v
montar_contexto()
  |
  v
openrouter()
  |
  v
Resposta
```

## Reindexação

```text
Fingerprint atual
  |
  v
Comparar anterior
  |
  +--> Igual      -> reutilizar
  |
  +--> Diferente  -> reconstruir índice
```
