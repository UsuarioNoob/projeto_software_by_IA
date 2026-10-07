"""Fixtures compartilhadas dos testes do Severino BOT."""

from __future__ import annotations

from collections.abc import Iterator
import os
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def limpar_variaveis_severino(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Impede que configurações reais da máquina contaminem os testes."""
    prefixes = (
        "OPENROUTER_",
        "DOCUMENTS_DIR",
        "CHROMA_",
        "FINGERPRINT_FILE",
        "EMBEDDING_MODEL",
        "CHUNK_",
        "TOP_K",
        "REQUEST_TIMEOUT_SECONDS",
        "SCHEMA_VERSION",
        "LOG_LEVEL",
    )
    for name in tuple(os.environ):
        if name.startswith(prefixes):
            monkeypatch.delenv(name, raising=False)
    yield


@pytest.fixture
def documento_valido() -> dict[str, object]:
    """Registro mínimo que atende ao contrato documental do SDD."""
    return {
        "Tipo": "Provimento",
        "Número do Documento": "360/2026",
        "Assunto": "Cartório Acolhedor",
        "Ementa": "Institui diretrizes para atendimento acolhedor.",
        "Situação": "Vigente",
        "Data do Diário": "2026-01-15",
        "Número Diário": 1234,
        "Link web": "https://example.test/provimento-360-2026",
    }


@pytest.fixture
def documentos_validos(documento_valido: dict[str, object]) -> list[dict[str, object]]:
    """Dois registros distinguíveis para testes de consolidação."""
    segundo = {
        **documento_valido,
        "Número do Documento": "361/2026",
        "Assunto": "Atendimento digital",
        "Link web": "https://example.test/provimento-361-2026",
    }
    return [documento_valido, segundo]


@pytest.fixture
def pasta_documentos(tmp_path: Path) -> Path:
    """Diretório temporário reservado a arquivos documentais."""
    path = tmp_path / "docs"
    path.mkdir()
    return path


@pytest.fixture
def dataframe_valido(documentos_validos: list[dict[str, object]]) -> pd.DataFrame:
    """DataFrame baseado no schema oficial de entrada."""
    return pd.DataFrame(documentos_validos)
