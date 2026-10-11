"""Testes TDD-RAG-001 a TDD-RAG-007 para o fluxo RAG."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from severino_bot.config import Settings
from severino_bot.exceptions import LLMServiceError, VectorStoreError
from severino_bot.mod_embedding import ResultadoBusca
from severino_bot.mod_orquestrator import (
    MENSAGEM_CONTEXTO_INSUFICIENTE,
    ResultadoPreparacao,
    _resposta_sem_informacao_relevante,
    montar_contexto,
    responder_pergunta,
)


def _settings(tmp_path: Path, *, top_k: int = 4) -> Settings:
    return Settings(
        documents_dir=tmp_path / "docs",
        chroma_dir=tmp_path / "chroma",
        chroma_collection="orquestracao_teste",
        fingerprint_file=tmp_path / "data" / "fingerprint.json",
        embedding_model="embedding-teste",
        chunk_size=512,
        chunk_overlap=64,
        top_k=top_k,
        openrouter_api_key="token-teste",
        openrouter_model="openai/modelo-teste",
        openrouter_base_url="https://openrouter.example/api/v1",
        request_timeout_seconds=19,
        schema_version="1",
        log_level="INFO",
    )


def _resultados() -> list[ResultadoBusca]:
    return [
        ResultadoBusca(
            chunk_id="chunk-primeiro",
            texto="Texto do primeiro ato.",
            metadata={
                "tipo": "Provimento",
                "numero": "360/2026",
                "link_web": "https://example.test/360",
            },
            distancia=0.1,
        ),
        ResultadoBusca(
            chunk_id="chunk-segundo",
            texto="Texto do segundo ato.",
            metadata={
                "tipo": "Portaria",
                "numero": "101/2026",
                "link_web": "https://example.test/101",
            },
            distancia=0.3,
        ),
    ]


def _preparacao(mocker: pytest.MockFixture) -> ResultadoPreparacao:
    return ResultadoPreparacao(
        store=mocker.Mock(),
        modelo_embedding=mocker.Mock(),
        fingerprint="fingerprint-teste",
        quantidade_chunks=2,
        reindexado=False,
    )


def test_fluxo_nominal_busca_monta_contexto_e_consulta_openrouter(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path)
    preparacao = _preparacao(mocker)
    resultados = _resultados()
    buscar = mocker.patch(
        "severino_bot.mod_orquestrator.buscar_chunks",
        return_value=resultados,
    )
    consultar = mocker.patch(
        "severino_bot.mod_orquestrator.consultar_openrouter",
        return_value="Resposta fundamentada.",
    )
    session = mocker.Mock()

    resposta = responder_pergunta(
        "Qual ato se aplica?",
        preparacao,
        settings,
        session=session,
    )

    buscar.assert_called_once_with(
        preparacao.store,
        "Qual ato se aplica?",
        preparacao.modelo_embedding,
        top_k=4,
    )
    consultar.assert_called_once()
    assert consultar.call_args.kwargs["contexto"] == montar_contexto(resultados)
    assert consultar.call_args.kwargs["session"] is session
    assert resposta.resposta == "Resposta fundamentada."
    assert resposta.fontes == tuple(resultados)


def test_top_k_e_propagado_corretamente(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path, top_k=7)
    preparacao = _preparacao(mocker)
    buscar = mocker.patch(
        "severino_bot.mod_orquestrator.buscar_chunks",
        return_value=_resultados(),
    )
    mocker.patch(
        "severino_bot.mod_orquestrator.consultar_openrouter",
        return_value="Resposta.",
    )

    responder_pergunta("Pergunta", preparacao, settings)

    assert buscar.call_args.kwargs["top_k"] == 7


def test_sem_documentos_recuperados_llm_nao_e_chamado(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path)
    preparacao = _preparacao(mocker)
    mocker.patch("severino_bot.mod_orquestrator.buscar_chunks", return_value=[])
    consultar = mocker.patch("severino_bot.mod_orquestrator.consultar_openrouter")

    resposta = responder_pergunta("Pergunta sem resultado", preparacao, settings)

    consultar.assert_not_called()
    assert resposta.resposta == MENSAGEM_CONTEXTO_INSUFICIENTE
    assert resposta.contexto == ""
    assert resposta.fontes == ()


def test_falha_no_retrieval_impede_chamada_ao_llm(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path)
    preparacao = _preparacao(mocker)
    mocker.patch(
        "severino_bot.mod_orquestrator.buscar_chunks",
        side_effect=VectorStoreError("falha no retrieval"),
    )
    consultar = mocker.patch("severino_bot.mod_orquestrator.consultar_openrouter")

    with pytest.raises(VectorStoreError, match="falha no retrieval"):
        responder_pergunta("Pergunta", preparacao, settings)

    consultar.assert_not_called()


def test_falha_do_llm_permanece_com_erro_apropriado(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path)
    preparacao = _preparacao(mocker)
    mocker.patch(
        "severino_bot.mod_orquestrator.buscar_chunks",
        return_value=_resultados(),
    )
    mocker.patch(
        "severino_bot.mod_orquestrator.consultar_openrouter",
        side_effect=LLMServiceError("serviço indisponível"),
    )

    with pytest.raises(LLMServiceError, match="serviço indisponível"):
        responder_pergunta("Pergunta", preparacao, settings)


def test_contexto_preserva_ordem_texto_distancia_e_metadata() -> None:
    resultados = _resultados()

    contexto = montar_contexto(resultados)

    assert contexto.index("chunk-primeiro") < contexto.index("chunk-segundo")
    assert contexto.index("Texto do primeiro ato.") < contexto.index(
        "Texto do segundo ato."
    )
    assert "Distância: 0.100000" in contexto
    assert "tipo: Provimento" in contexto
    assert "numero: 360/2026" in contexto
    assert "link_web: https://example.test/360" in contexto


def test_montar_contexto_vazio_retorna_texto_vazio() -> None:
    assert montar_contexto([]) == ""


def test_resposta_sem_base_suficiente_e_explicita(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path)
    preparacao = _preparacao(mocker)
    mocker.patch("severino_bot.mod_orquestrator.buscar_chunks", return_value=[])
    mocker.patch("severino_bot.mod_orquestrator.consultar_openrouter")

    resposta = responder_pergunta("Pergunta", preparacao, settings)

    assert "não encontrei essa informação" in resposta.resposta.casefold()
    assert "tipo e número do ato" in resposta.resposta.casefold()
    assert resposta.fontes == ()


def test_pergunta_fora_do_escopo_remove_contexto_e_fontes(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path)
    preparacao = _preparacao(mocker)
    mocker.patch(
        "severino_bot.mod_orquestrator.buscar_chunks",
        return_value=_resultados(),
    )
    mocker.patch(
        "severino_bot.mod_orquestrator.consultar_openrouter",
        return_value="[SEM_INFORMACAO_RELEVANTE]",
    )

    resposta = responder_pergunta(
        "Qual é a receita de bolo de chocolate?",
        preparacao,
        settings,
    )

    assert resposta.resposta == MENSAGEM_CONTEXTO_INSUFICIENTE
    assert resposta.contexto == ""
    assert resposta.fontes == ()


@pytest.mark.parametrize(
    "resposta",
    [
        "[SEM_INFORMACAO_RELEVANTE]",
        "Aviso: [sem_informacao_relevante]",
        "Não encontrei informação suficiente nos documentos fornecidos.",
    ],
)
def test_reconhece_resposta_sem_informacao_relevante(resposta: str) -> None:
    assert _resposta_sem_informacao_relevante(resposta) is True


def test_configuracoes_do_openrouter_sao_propagadas(
    tmp_path: Path,
    mocker: pytest.MockFixture,
) -> None:
    settings = _settings(tmp_path)
    preparacao = _preparacao(mocker)
    mocker.patch(
        "severino_bot.mod_orquestrator.buscar_chunks",
        return_value=_resultados(),
    )
    consultar = mocker.patch(
        "severino_bot.mod_orquestrator.consultar_openrouter",
        return_value="Resposta.",
    )

    responder_pergunta("Pergunta", preparacao, settings)

    kwargs: dict[str, Any] = consultar.call_args.kwargs
    assert kwargs["api_key"] == "token-teste"
    assert kwargs["modelo"] == "openai/modelo-teste"
    assert kwargs["base_url"] == "https://openrouter.example/api/v1"
    assert kwargs["timeout_seconds"] == 19