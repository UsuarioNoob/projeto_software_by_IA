# Fluxos do Sistema

## Inicialização

```text
main()
  |
  v
preparar_base_vetorial()
  |
  +--> calcular fingerprint
  |
  +--> comparar com fingerprint salvo
  |
  +--> reindexar ou reutilizar
  |
  v
iniciar_interface()
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
