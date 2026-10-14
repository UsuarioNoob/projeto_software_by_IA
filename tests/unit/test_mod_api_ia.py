"""Testes TDD-LLM-001 a TDD-LLM-017 para integração com OpenRouter."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from severino_bot.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    LLMServiceError,
)
from severino_bot.mod_api_ia import consultar_openrouter, normalizar_token


def _resposta_mock(
    mocker: pytest.MockFixture,
    *,
    status_code: int = 200,
    payload: Any = None,
) -> Any:
    resposta = mocker.Mock()
    resposta.status_code = status_code
    resposta.json.return_value = (
        {"choices": [{"message": {"content": "Resposta fundamentada."}}]}
        if payload is None
        else payload
    )
    return resposta


def _consultar(session: Any, **alteracoes: object) -> str:
    parametros: dict[str, object] = {
        "pergunta": "Qual é a regra aplicável?",
        "contexto": "Tipo: Provimento\nNúmero: 360/2026\nEmenta: Regra aplicável.",
        "api_key": "token-teste",
        "modelo": "openai/modelo-teste",
        "base_url": "https://openrouter.example/api/v1",
        "timeout_seconds": 17,
        "session": session,
    }
    parametros.update(alteracoes)
    return consultar_openrouter(**parametros)  # type: ignore[arg-type]


def test_token_none_gera_erro_de_autenticacao() -> None:
    with pytest.raises(LLMAuthenticationError, match="credencial"):
        normalizar_token(None)


def test_token_vazio_gera_erro_de_autenticacao() -> None:
    with pytest.raises(LLMAuthenticationError, match="credencial"):
        normalizar_token("   ")


def test_token_simples_recebe_prefixo_bearer() -> None:
    assert normalizar_token("token-teste") == "Bearer token-teste"


def test_token_bearer_nao_e_duplicado() -> None:
    assert normalizar_token("Bearer token-teste") == "Bearer token-teste"


def test_payload_contem_modelo_e_mensagens(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker)

    _consultar(session)

    payload = session.post.call_args.kwargs["json"]
    assert payload["model"] == "openai/modelo-teste"
    assert [mensagem["role"] for mensagem in payload["messages"]] == [
        "system",
        "user",
    ]
    assert "Qual é a regra aplicável?" in payload["messages"][1]["content"]
    assert "Provimento" in payload["messages"][1]["content"]


def test_prompt_instrui_resposta_exclusiva_com_base_no_contexto(
    mocker: pytest.MockFixture,
) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker)

    _consultar(session)

    mensagem_sistema = session.post.call_args.kwargs["json"]["messages"][0]["content"]
    assert "apenas" in mensagem_sistema.casefold()
    assert "contexto" in mensagem_sistema.casefold()
    assert "informação suficiente" in mensagem_sistema.casefold()
    assert "assunto" in mensagem_sistema.casefold()
    assert "ementa" in mensagem_sistema.casefold()
    assert "[sem_informacao_relevante]" in mensagem_sistema.casefold()
    assert "não liste documentos irrelevantes" in mensagem_sistema.casefold()
    assert "não acrescente uma seção" in mensagem_sistema.casefold()
    assert "documentos relacionados" in mensagem_sistema.casefold()
    assert "automaticamente todos os documentos" in mensagem_sistema.casefold()


def test_requisicao_possui_timeout(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker)

    _consultar(session)

    assert session.post.call_args.kwargs["timeout"] == 17


def test_requisicao_envia_headers_e_endpoint_corretos(
    mocker: pytest.MockFixture,
) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker)

    _consultar(session, api_key="Bearer token-teste")

    assert session.post.call_args.args[0] == (
        "https://openrouter.example/api/v1/chat/completions"
    )
    headers = session.post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer token-teste"
    assert headers["Content-Type"] == "application/json"


def test_http_200_extrai_message_content(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(
        mocker,
        payload={"choices": [{"message": {"content": "Conteúdo retornado."}}]},
    )

    assert _consultar(session) == "Conteúdo retornado."


def test_http_401_gera_erro_de_autenticacao(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker, status_code=401)

    with pytest.raises(LLMAuthenticationError, match="autenticação"):
        _consultar(session)


def test_http_429_gera_erro_de_rate_limit(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker, status_code=429)

    with pytest.raises(LLMRateLimitError, match="limite"):
        _consultar(session)


def test_http_500_gera_erro_de_servico(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker, status_code=500)

    with pytest.raises(LLMServiceError, match="500"):
        _consultar(session)


def test_timeout_gera_erro_de_conexao(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.side_effect = requests.Timeout("tempo excedido")

    with pytest.raises(LLMConnectionError, match="tempo"):
        _consultar(session)


def test_connection_error_e_tratado(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.side_effect = requests.ConnectionError("sem conexão")

    with pytest.raises(LLMConnectionError, match="conectar"):
        _consultar(session)


def test_json_invalido_gera_erro_de_resposta(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    resposta = _resposta_mock(mocker)
    resposta.json.side_effect = ValueError("json inválido")
    session.post.return_value = resposta

    with pytest.raises(LLMResponseError, match="JSON"):
        _consultar(session)


def test_choices_ausente_gera_erro_de_resposta(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker, payload={"id": "resposta"})

    with pytest.raises(LLMResponseError, match="choices"):
        _consultar(session)


def test_choices_vazio_gera_erro_de_resposta(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(mocker, payload={"choices": []})

    with pytest.raises(LLMResponseError, match="choices"):
        _consultar(session)


def test_message_ausente_gera_erro_de_resposta(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(
        mocker,
        payload={"choices": [{"finish_reason": "stop"}]},
    )

    with pytest.raises(LLMResponseError, match="message"):
        _consultar(session)


def test_content_ausente_gera_erro_de_resposta(mocker: pytest.MockFixture) -> None:
    session = mocker.Mock()
    session.post.return_value = _resposta_mock(
        mocker,
        payload={"choices": [{"message": {"role": "assistant"}}]},
    )

    with pytest.raises(LLMResponseError, match="content"):
        _consultar(session)