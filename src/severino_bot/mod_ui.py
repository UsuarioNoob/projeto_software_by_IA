"""Integração exclusiva entre o pipeline RAG e a interface Chainlit."""

from __future__ import annotations

import asyncio
import logging

import chainlit as cl

from severino_bot.config import Settings, carregar_configuracao, configurar_logging
from severino_bot.exceptions import (
    DocumentLoadError,
    LLMAuthenticationError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    LLMServiceError,
    SchemaValidationError,
    VectorStoreError,
)
from severino_bot.mod_orquestrator import (
    ResultadoPreparacao,
    preparar_base_vetorial,
    responder_pergunta,
)


LOGGER = logging.getLogger(__name__)

CHAVE_SETTINGS = "severino_settings"
CHAVE_PREPARACAO = "severino_preparacao"

MENSAGEM_SEM_ESTADO = (
    "O Severino BOT não está disponível nesta sessão. "
    "Reinicie a aplicação ou solicite ao administrador a verificação da base documental."
)
MENSAGEM_PERGUNTA_VAZIA = "Envie uma pergunta sobre os documentos disponíveis."

_HANDLERS_REGISTRADOS = False
_SETTINGS_APLICACAO: Settings | None = None
_PREPARACAO_APLICACAO: ResultadoPreparacao | None = None


async def _enviar(conteudo: str) -> None:
    """Envia uma mensagem textual pelo Chainlit."""
    await cl.Message(content=conteudo).send()


def _mensagem_erro_consulta(erro: Exception) -> str:
    """Traduz erros tipados para mensagens seguras e acionáveis ao usuário."""
    if isinstance(erro, LLMAuthenticationError):
        return (
            "Não foi possível autenticar no provedor de IA. "
            "Verifique a credencial do OpenRouter."
        )
    if isinstance(erro, LLMRateLimitError):
        return (
            "O limite de requisições do provedor foi atingido. "
            "Aguarde um momento e tente novamente."
        )
    if isinstance(erro, LLMConnectionError):
        return (
            "Não foi possível conectar ao provedor de IA. "
            "Verifique a conexão e tente novamente."
        )
    if isinstance(erro, LLMServiceError):
        return (
            "O serviço de IA está temporariamente indisponível. "
            "Tente novamente mais tarde."
        )
    if isinstance(erro, LLMResponseError):
        return (
            "O provedor de IA retornou uma resposta inválida. "
            "Tente reformular a pergunta."
        )
    return (
        "Não foi possível consultar a base documental neste momento. "
        "Tente novamente ou inicie uma nova conversa."
    )


async def preparar_aplicacao() -> None:
    """Prepara configuração e ChromaDB antes de disponibilizar o Chainlit."""
    global _SETTINGS_APLICACAO, _PREPARACAO_APLICACAO
    _SETTINGS_APLICACAO = None
    _PREPARACAO_APLICACAO = None
    try:
        settings = carregar_configuracao()
        configurar_logging(settings.log_level)
    except (ValueError, OSError):
        LOGGER.exception("Falha ao carregar a configuração da aplicação.")
        raise

    try:
        preparacao = await asyncio.to_thread(preparar_base_vetorial, settings)
    except (
        FileNotFoundError,
        NotADirectoryError,
        DocumentLoadError,
        SchemaValidationError,
        VectorStoreError,
    ):
        LOGGER.exception("Falha ao preparar a base documental.")
        raise
    except Exception:
        LOGGER.exception("Falha inesperada ao preparar a aplicação.")
        raise

    _SETTINGS_APLICACAO = settings
    _PREPARACAO_APLICACAO = preparacao
    LOGGER.info(
        "Aplicação pronta: base=%s chunks=%d",
        "reindexada" if preparacao.reindexado else "reutilizada",
        preparacao.quantidade_chunks,
    )


async def inicializar_chat() -> None:
    """Associa ao novo chat a base já preparada no startup da aplicação."""
    settings = _SETTINGS_APLICACAO
    preparacao = _PREPARACAO_APLICACAO
    if settings is None or preparacao is None:
        LOGGER.error("Chat iniciado sem a preparação global da aplicação.")
        cl.user_session.set(CHAVE_SETTINGS, None)
        cl.user_session.set(CHAVE_PREPARACAO, None)
        await _enviar(MENSAGEM_SEM_ESTADO)
        return

    cl.user_session.set(CHAVE_SETTINGS, settings)
    cl.user_session.set(CHAVE_PREPARACAO, preparacao)
    situacao = "atualizada" if preparacao.reindexado else "reutilizada"
    await _enviar(
        "Olá! Sou o **Severino BOT**. A base documental foi "
        f"{situacao} com **{preparacao.quantidade_chunks} trechos**. "
        "Envie sua pergunta sobre os atos normativos disponíveis."
    )


async def processar_mensagem(message: cl.Message) -> None:
    """Processa uma pergunta sem bloquear o event loop do Chainlit."""
    settings: Settings | None = cl.user_session.get(CHAVE_SETTINGS)
    preparacao: ResultadoPreparacao | None = cl.user_session.get(CHAVE_PREPARACAO)
    if settings is None or preparacao is None:
        await _enviar(MENSAGEM_SEM_ESTADO)
        return

    pergunta = str(message.content).strip()
    if not pergunta:
        await _enviar(MENSAGEM_PERGUNTA_VAZIA)
        return

    try:
        resultado = await cl.make_async(responder_pergunta)(
            pergunta,
            preparacao,
            settings,
        )
    except (
        LLMAuthenticationError,
        LLMRateLimitError,
        LLMConnectionError,
        LLMServiceError,
        LLMResponseError,
        VectorStoreError,
    ) as erro:
        LOGGER.exception("Falha controlada ao responder pergunta.")
        await _enviar(_mensagem_erro_consulta(erro))
        return
    except Exception:
        LOGGER.exception("Falha inesperada ao responder pergunta.")
        await _enviar(
            "Ocorreu uma falha inesperada ao processar sua pergunta. "
            "Tente novamente mais tarde."
        )
        return

    await _enviar(resultado.resposta)


def iniciar_interface() -> None:
    """Registra uma única vez os handlers públicos exigidos pelo Chainlit."""
    global _HANDLERS_REGISTRADOS
    if _HANDLERS_REGISTRADOS:
        return

    cl.on_app_startup(preparar_aplicacao)
    cl.on_chat_start(inicializar_chat)
    cl.on_message(processar_mensagem)
    _HANDLERS_REGISTRADOS = True
    LOGGER.info("Interface do Severino BOT carregada.")
