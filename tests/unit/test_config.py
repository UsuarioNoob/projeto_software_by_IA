"""Testes unitários da configuração externa."""

from pathlib import Path

import pytest

from severino_bot.config import PROJECT_ROOT, carregar_configuracao


def test_carregar_configuracao_com_valores_padrao() -> None:
    settings = carregar_configuracao(env_file=Path("arquivo-inexistente.env"))

    assert settings.documents_dir == PROJECT_ROOT / "docs"
    assert settings.chroma_dir == PROJECT_ROOT / "chroma_db"
    assert settings.chunk_size == 512
    assert settings.chunk_overlap == 64
    assert settings.top_k == 5
    assert settings.openrouter_api_key is None


def test_carregar_configuracao_rejeita_overlap_igual_ao_chunk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHUNK_SIZE", "100")
    monkeypatch.setenv("CHUNK_OVERLAP", "100")

    with pytest.raises(ValueError, match="CHUNK_OVERLAP"):
        carregar_configuracao(env_file=Path("arquivo-inexistente.env"))


def test_carregar_configuracao_rejeita_top_k_nao_positivo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TOP_K", "0")

    with pytest.raises(ValueError, match="TOP_K"):
        carregar_configuracao(env_file=Path("arquivo-inexistente.env"))
