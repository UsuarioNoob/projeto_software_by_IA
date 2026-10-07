# Regras de Negócio

## RN-001
Somente arquivos suportados devem participar da base.

## RN-002
Documentos inválidos não devem ser silenciosamente aceitos como parte de uma base válida.

## RN-003
A resposta deve utilizar apenas conhecimento recuperado da base documental.

## RN-004
Na ausência de contexto suficiente, o sistema deve informar que não encontrou informação suficiente.

## RN-005
A indexação deve ser invalidada quando mudarem:

- documentos;
- modelo de embedding;
- chunk size;
- chunk overlap;
- versão do schema.

## RN-006
O mesmo modelo de embedding deve ser usado na indexação e consulta.

## RN-007
O fingerprint só deve ser salvo após indexação bem-sucedida.
