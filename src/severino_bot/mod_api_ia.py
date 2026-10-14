"""Cliente HTTP desacoplado para integração com o OpenRouter."""

from __future__ import annotations

import logging
from typing import Any, Protocol

import requests

from severino_bot.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    LLMServiceError,
)


LOGGER = logging.getLogger(__name__)
SINAL_CONTEXTO_INSUFICIENTE = "[SEM_INFORMACAO_RELEVANTE]"

PROMPT_SISTEMA = """Você é o assistente Severino BOT para consulta de atos normativos.
Responda apenas com base no contexto documental fornecido pelo sistema.
Não use conhecimento externo, não invente informações e não complete lacunas por suposição.
Considere especialmente os campos Assunto e Ementa para identificar conteúdo pertinente.
Sintetize somente as informações necessárias para responder diretamente à pergunta.
Não acrescente uma seção de fontes, referências ou "Documentos relacionados" e não liste
automaticamente todos os documentos recuperados. Mencione dados identificadores de um ato somente
quando forem necessários para responder ao que foi perguntado.
Antes de responder, verifique se o contexto realmente possui relação com a pergunta.
Se o contexto não contiver informação suficiente, se a pergunta for aleatória, estiver fora
do escopo dos atos normativos ou se os trechos recuperados não sustentarem a resposta,
responda somente com o sinal:
"[SEM_INFORMACAO_RELEVANTE]"
Não resuma, não cite e não liste documentos irrelevantes nesse caso.
Responda de forma clara, objetiva e em português."""


class RespostaHTTP(Protocol):
    """Contrato mínimo da resposta HTTP utilizado pelo cliente."""

    status_code: int

    def json(self) -> Any:
        """Decodifica o corpo JSON da resposta."""


class SessaoHTTP(Protocol):
    """Contrato injetável para sessões HTTP síncronas."""

    def post(self, url: str, **kwargs: Any) -> RespostaHTTP:
        """Executa uma requisição POST."""


def normalizar_token(api_key: str | None) -> str:
    """Valida a credencial e garante exatamente um prefixo ``Bearer``."""
    if api_key is None or not api_key.strip():
        raise LLMAuthenticationError("A credencial do OpenRouter não foi configurada.")

    token = api_key.strip()
    if token.casefold().startswith("bearer "):
        valor = token[7:].strip()
        if not valor:
            raise LLMAuthenticationError("A credencial do OpenRouter está vazia.")
        return f"Bearer {valor}"
    return f"Bearer {token}"


def _montar_mensagens(pergunta: str, contexto: str) -> list[dict[str, str]]:
    """Monta mensagens mantendo instruções e dados em papéis separados."""
    if not pergunta.strip():
        raise ValueError("A pergunta não pode ser vazia.")
    if not contexto.strip():
        raise ValueError("O contexto não pode ser vazio.")

    mensagem_usuario = (
        "CONTEXTO DOCUMENTAL:\n"
        f"{contexto.strip()}\n\n"
        "PERGUNTA DO USUÁRIO:\n"
        f"{pergunta.strip()}"
    )
    return [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user", "content": mensagem_usuario},
    ]


def _validar_status(status_code: int) -> None:
    """Traduz códigos HTTP para exceções de integração específicas."""
    if status_code in {401, 403}:
        raise LLMAuthenticationError(
            f"Falha de autenticação no OpenRouter (HTTP {status_code})."
        )
    if status_code == 429:
        raise LLMRateLimitError("O limite de requisições do OpenRouter foi atingido.")
    if status_code >= 400:
        raise LLMServiceError(f"O OpenRouter retornou erro HTTP {status_code}.")


def _extrair_conteudo(resposta: RespostaHTTP) -> str:
    """Valida e extrai ``choices[0].message.content`` da resposta."""
    try:
        payload = resposta.json()
    except (ValueError, requests.JSONDecodeError) as exc:
        raise LLMResponseError("O OpenRouter retornou JSON inválido.") from exc

    if not isinstance(payload, dict):
        raise LLMResponseError("A resposta JSON do OpenRouter deve ser um objeto.")

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMResponseError("A resposta do OpenRouter não contém choices válidos.")

    primeira = choices[0]
    if not isinstance(primeira, dict) or not isinstance(primeira.get("message"), dict):
        raise LLMResponseError("A resposta do OpenRouter não contém message válido.")

    content = primeira["message"].get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMResponseError("A resposta do OpenRouter não contém content válido.")
    return content.strip()


def consultar_openrouter(
    *,
    pergunta: str,
    contexto: str,
    api_key: str | None,
    modelo: str,
    base_url: str,
    timeout_seconds: int,
    session: SessaoHTTP | None = None,
) -> str:
    """Envia pergunta e contexto ao endpoint de chat completions do OpenRouter."""
    if not modelo.strip():
        raise ValueError("O modelo do OpenRouter não pode ser vazio.")
    if not base_url.strip():
        raise ValueError("A URL base do OpenRouter não pode ser vazia.")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds deve ser maior que zero.")

    autorizacao = normalizar_token(api_key)
    mensagens = _montar_mensagens(pergunta, contexto)
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    cliente = session or requests.Session()

    try:
        resposta = cliente.post(
            endpoint,
            headers={
                "Authorization": autorizacao,
                "Content-Type": "application/json",
            },
            json={
                "model": modelo.strip(),
                "messages": mensagens,
            },
            timeout=timeout_seconds,
        )
    except requests.Timeout as exc:
        raise LLMConnectionError(
            "O tempo limite da conexão com o OpenRouter foi excedido."
        ) from exc
    except requests.ConnectionError as exc:
        raise LLMConnectionError("Não foi possível conectar ao OpenRouter.") from exc
    except requests.RequestException as exc:
        raise LLMConnectionError("Falha HTTP ao acessar o OpenRouter.") from exc

    _validar_status(resposta.status_code)
    conteudo = _extrair_conteudo(resposta)
    LOGGER.info(
        "Consulta ao OpenRouter concluída: modelo=%s status=%d",
        modelo,
        resposta.status_code,
    )
    return conteudo
