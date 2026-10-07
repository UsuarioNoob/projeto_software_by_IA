"""Exceções de domínio e de integração do Severino BOT."""


class SeverinoBotError(Exception):
    """Erro base da aplicação."""


class SchemaValidationError(SeverinoBotError):
    """O documento não atende ao schema obrigatório."""


class DocumentLoadError(SeverinoBotError):
    """Um documento relevante não pôde ser carregado."""


class VectorStoreError(SeverinoBotError):
    """Falha de indexação, persistência ou consulta vetorial."""


class EmptyVectorStoreError(VectorStoreError):
    """A consulta foi solicitada sem documentos indexados."""


class LLMError(SeverinoBotError):
    """Erro base na integração com o modelo de linguagem."""


class LLMAuthenticationError(LLMError):
    """Credencial ausente ou rejeitada pelo provedor."""


class LLMRateLimitError(LLMError):
    """O limite de requisições do provedor foi atingido."""


class LLMConnectionError(LLMError):
    """Não foi possível conectar ao provedor no tempo esperado."""


class LLMServiceError(LLMError):
    """O provedor respondeu com falha de serviço."""


class LLMResponseError(LLMError):
    """A resposta do provedor não possui o contrato esperado."""
