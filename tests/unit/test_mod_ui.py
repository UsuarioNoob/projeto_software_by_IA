"""Testes da integração entre o pipeline RAG e a interface Chainlit."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

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
from severino_bot.mod_embedding import ResultadoBusca
from severino_bot.mod_orquestrator import ResultadoResposta
from severino_bot import mod_ui


class SessaoFalsa:
    """Armazena dados como ``cl.user_session`` sem exigir contexto Chainlit."""

    def __init__(self) -> None:
        self.dados: dict[str, Any] = {}

    def get(self, chave: str, padrao: Any = None) -> Any:
        return self.dados.get(chave, padrao)

    def set(self, chave: str, valor: Any) -> None:
        self.dados[chave] = valor


@pytest.fixture
def chainlit_falso(mocker: pytest.MockFixture) -> SimpleNamespace:
    mensagens: list[str] = []
    chamadas_assincronas: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []

    class MensagemFalsa:
        def __init__(self, content: str) -> None:
            self.content = content

        async def send(self) -> None:
            mensagens.append(self.content)

    def make_async(funcao: Any) -> Any:
        async def executar(*args: Any, **kwargs: Any) -> Any:
            chamadas_assincronas.append((funcao, args, kwargs))
            return funcao(*args, **kwargs)

        return executar

    sessao = SessaoFalsa()
    mocker.patch.object(mod_ui.cl, "Message", MensagemFalsa)
    mocker.patch.object(mod_ui.cl, "make_async", side_effect=make_async)
    mocker.patch.object(mod_ui.cl, "user_session", sessao)
    return SimpleNamespace(
        mensagens=mensagens,
        chamadas_assincronas=chamadas_assincronas,
        sessao=sessao,
    )


@pytest.mark.asyncio
async def test_preparar_aplicacao_carrega_base_uma_unica_vez(
    mocker: pytest.MockFixture,
) -> None:
    settings = mocker.Mock(log_level="INFO")
    preparacao = mocker.Mock(quantidade_chunks=12, reindexado=True)
    mocker.patch.object(mod_ui, "carregar_configuracao", return_value=settings)
    configurar = mocker.patch.object(mod_ui, "configurar_logging")
    preparar = mocker.patch.object(
        mod_ui, "preparar_base_vetorial", return_value=preparacao
    )

    await mod_ui.preparar_aplicacao()

    configurar.assert_called_once_with("INFO")
    preparar.assert_called_once_with(settings)
    assert mod_ui._SETTINGS_APLICACAO is settings
    assert mod_ui._PREPARACAO_APLICACAO is preparacao


@pytest.mark.asyncio
async def test_inicializar_chat_reutiliza_base_preparada(
    mocker: pytest.MockFixture,
    chainlit_falso: SimpleNamespace,
) -> None:
    settings = mocker.Mock()
    preparacao = mocker.Mock(quantidade_chunks=12, reindexado=True)
    mocker.patch.object(mod_ui, "_SETTINGS_APLICACAO", settings)
    mocker.patch.object(mod_ui, "_PREPARACAO_APLICACAO", preparacao)

    await mod_ui.inicializar_chat()

    assert chainlit_falso.sessao.get(mod_ui.CHAVE_SETTINGS) is settings
    assert chainlit_falso.sessao.get(mod_ui.CHAVE_PREPARACAO) is preparacao
    assert "12 trechos" in chainlit_falso.mensagens[-1]
    assert "atualizada" in chainlit_falso.mensagens[-1]


@pytest.mark.asyncio
async def test_preparar_aplicacao_propaga_falha_de_configuracao(
    mocker: pytest.MockFixture,
) -> None:
    mocker.patch.object(
        mod_ui,
        "carregar_configuracao",
        side_effect=ValueError("configuração inválida"),
    )

    with pytest.raises(ValueError, match="configuração inválida"):
        await mod_ui.preparar_aplicacao()

    assert mod_ui._SETTINGS_APLICACAO is None
    assert mod_ui._PREPARACAO_APLICACAO is None


@pytest.mark.asyncio
async def test_processar_mensagem_exibe_somente_resposta_sem_fontes_automaticas(
    mocker: pytest.MockFixture,
    chainlit_falso: SimpleNamespace,
) -> None:
    settings = mocker.Mock()
    preparacao = mocker.Mock()
    chainlit_falso.sessao.set(mod_ui.CHAVE_SETTINGS, settings)
    chainlit_falso.sessao.set(mod_ui.CHAVE_PREPARACAO, preparacao)
    resultado = ResultadoResposta(
        resposta="Resposta fundamentada.",
        contexto="contexto",
        fontes=(
            ResultadoBusca(
                chunk_id="ato-360",
                texto="Conteúdo",
                metadata={
                    "tipo": "Provimento",
                    "numero": "360/2026",
                    "assunto": "Férias de servidores",
                    "link_web": "https://example.test/360",
                },
                distancia=0.125,
            ),
        ),
    )
    responder = mocker.patch.object(
        mod_ui, "responder_pergunta", return_value=resultado
    )

    await mod_ui.processar_mensagem(SimpleNamespace(content="  Qual ato?  "))

    responder.assert_called_once_with("Qual ato?", preparacao, settings)
    assert chainlit_falso.chamadas_assincronas[0][0] is mod_ui.responder_pergunta
    enviada = chainlit_falso.mensagens[-1]
    assert enviada == "Resposta fundamentada."
    assert "Documentos relacionados" not in enviada
    assert "360/2026" not in enviada
    assert "https://example.test/360" not in enviada


@pytest.mark.asyncio
async def test_processar_mensagem_fora_do_escopo_nao_exibe_fontes(
    mocker: pytest.MockFixture,
    chainlit_falso: SimpleNamespace,
) -> None:
    chainlit_falso.sessao.set(mod_ui.CHAVE_SETTINGS, mocker.Mock())
    chainlit_falso.sessao.set(mod_ui.CHAVE_PREPARACAO, mocker.Mock())
    resultado = ResultadoResposta(
        resposta=(
            "Não encontrei essa informação na base de atos normativos disponível. "
            "Posso ajudar com assunto, ementa e situação dos documentos."
        ),
        contexto="",
        fontes=(),
    )
    mocker.patch.object(mod_ui, "responder_pergunta", return_value=resultado)

    await mod_ui.processar_mensagem(
        SimpleNamespace(content="Qual é a receita de bolo de chocolate?")
    )

    enviada = chainlit_falso.mensagens[-1]
    assert "não encontrei essa informação" in enviada.casefold()
    assert "Documentos relacionados" not in enviada
    assert "http" not in enviada


@pytest.mark.asyncio
async def test_processar_mensagem_sem_estado_orienta_reiniciar(
    chainlit_falso: SimpleNamespace,
) -> None:
    await mod_ui.processar_mensagem(SimpleNamespace(content="Pergunta"))

    assert "não está disponível" in chainlit_falso.mensagens[-1].casefold()
    assert "reinicie a aplicação" in chainlit_falso.mensagens[-1].casefold()


@pytest.mark.asyncio
async def test_inicializar_chat_sem_startup_exibe_indisponibilidade(
    mocker: pytest.MockFixture,
    chainlit_falso: SimpleNamespace,
) -> None:
    mocker.patch.object(mod_ui, "_SETTINGS_APLICACAO", None)
    mocker.patch.object(mod_ui, "_PREPARACAO_APLICACAO", None)

    await mod_ui.inicializar_chat()

    assert chainlit_falso.sessao.get(mod_ui.CHAVE_PREPARACAO) is None
    assert "não está disponível" in chainlit_falso.mensagens[-1].casefold()


@pytest.mark.asyncio
async def test_processar_mensagem_vazia_nao_chama_pipeline(
    mocker: pytest.MockFixture,
    chainlit_falso: SimpleNamespace,
) -> None:
    chainlit_falso.sessao.set(mod_ui.CHAVE_SETTINGS, mocker.Mock())
    chainlit_falso.sessao.set(mod_ui.CHAVE_PREPARACAO, mocker.Mock())
    responder = mocker.patch.object(mod_ui, "responder_pergunta")

    await mod_ui.processar_mensagem(SimpleNamespace(content="   "))

    responder.assert_not_called()
    assert "pergunta" in chainlit_falso.mensagens[-1].casefold()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("erro", "trecho_esperado"),
    [
        (LLMAuthenticationError("detalhe-interno-auth"), "credencial"),
        (LLMRateLimitError("detalhe-interno-rate"), "limite"),
        (LLMConnectionError("detalhe-interno-conexao"), "conectar"),
        (LLMServiceError("detalhe-interno-servico"), "indisponível"),
        (LLMResponseError("detalhe-interno-payload"), "resposta inválida"),
        (VectorStoreError("detalhe-interno-vetor"), "base documental"),
    ],
)
async def test_processar_mensagem_traduz_erros_para_usuario(
    erro: Exception,
    trecho_esperado: str,
    mocker: pytest.MockFixture,
    chainlit_falso: SimpleNamespace,
) -> None:
    chainlit_falso.sessao.set(mod_ui.CHAVE_SETTINGS, mocker.Mock())
    chainlit_falso.sessao.set(mod_ui.CHAVE_PREPARACAO, mocker.Mock())
    mocker.patch.object(mod_ui, "responder_pergunta", side_effect=erro)

    await mod_ui.processar_mensagem(SimpleNamespace(content="Pergunta"))

    assert trecho_esperado in chainlit_falso.mensagens[-1].casefold()
    assert str(erro) not in chainlit_falso.mensagens[-1]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "erro",
    [
        FileNotFoundError("docs"),
        DocumentLoadError("documento"),
        SchemaValidationError("schema"),
        VectorStoreError("vetor"),
    ],
)
async def test_preparar_aplicacao_propaga_erros_da_base(
    erro: Exception,
    mocker: pytest.MockFixture,
) -> None:
    settings = mocker.Mock(log_level="INFO")
    mocker.patch.object(mod_ui, "carregar_configuracao", return_value=settings)
    mocker.patch.object(mod_ui, "configurar_logging")
    mocker.patch.object(mod_ui, "preparar_base_vetorial", side_effect=erro)

    with pytest.raises(type(erro), match=str(erro)):
        await mod_ui.preparar_aplicacao()

    assert mod_ui._SETTINGS_APLICACAO is None
    assert mod_ui._PREPARACAO_APLICACAO is None


def test_iniciar_interface_registra_handlers_uma_unica_vez(
    mocker: pytest.MockFixture,
) -> None:
    mocker.patch.object(mod_ui, "_HANDLERS_REGISTRADOS", False)
    on_app_startup = mocker.patch.object(
        mod_ui.cl, "on_app_startup", side_effect=lambda f: f
    )
    on_start = mocker.patch.object(mod_ui.cl, "on_chat_start", side_effect=lambda f: f)
    on_message = mocker.patch.object(mod_ui.cl, "on_message", side_effect=lambda f: f)

    mod_ui.iniciar_interface()
    mod_ui.iniciar_interface()

    on_app_startup.assert_called_once_with(mod_ui.preparar_aplicacao)
    on_start.assert_called_once()
    on_message.assert_called_once()