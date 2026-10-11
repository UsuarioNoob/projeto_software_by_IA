"""Fixtures compartilhadas dos testes do Severino BOT."""

from __future__ import annotations

from collections.abc import Iterator
import os
from pathlib import Path
from typing import Protocol

import pandas as pd
import pytest
from llama_index.core.schema import TextNode

from severino_bot.mod_docs import criar_chunks


class EmbeddingDeterministico(Protocol):
    chamadas: int

    def get_text_embedding_batch(self, textos: list[str]) -> list[list[float]]:
        """Gera vetores determinísticos sem acessar modelos externos."""

    def get_query_embedding(self, texto: str) -> list[float]:
        """Gera um vetor determinístico para uma consulta."""


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


@pytest.fixture
def chroma_temporario(tmp_path: Path) -> Path:
    """Diretório isolado para testes locais de persistência vetorial."""
    return tmp_path / "chroma"


@pytest.fixture
def chunks_validos(
    documentos_validos: list[dict[str, object]],
) -> list[TextNode]:
    """Chunks reais do pipeline documental usados pelo vector store."""
    return criar_chunks(documentos_validos, chunk_size=512, chunk_overlap=64)


@pytest.fixture
def embedding_deterministico() -> EmbeddingDeterministico:
    """Embedding local, estável e observável para testes unitários."""

    class ModeloEmbeddingDeterministico:
        def __init__(self) -> None:
            self.chamadas = 0

        def get_text_embedding_batch(self, textos: list[str]) -> list[list[float]]:
            self.chamadas += 1
            return [
                [
                    float(len(texto)),
                    float(sum(ord(caractere) for caractere in texto) % 997),
                    float(indice + 1),
                ]
                for indice, texto in enumerate(textos)
            ]

        def get_query_embedding(self, texto: str) -> list[float]:
            self.chamadas += 1
            return [
                float(len(texto)),
                float(sum(ord(caractere) for caractere in texto) % 997),
                1.0,
            ]

    return ModeloEmbeddingDeterministico()
