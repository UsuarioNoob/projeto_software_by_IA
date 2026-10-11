"""Testes TDD-HASH-001 a TDD-HASH-010 e controle de reindexação."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Protocol

import pandas as pd
import pytest

from severino_bot.config import Settings
from severino_bot.exceptions import VectorStoreError
from severino_bot.mod_orquestrator import (
    calcular_fingerprint,
    carregar_fingerprint,
    preparar_base_vetorial,
)


class ModeloEmbedding(Protocol):
    chamadas: int

    def get_text_embedding_batch(self, textos: list[str]) -> list[list[float]]:
        """Gera embeddings de documentos."""

    def get_query_embedding(self, texto: str) -> list[float]:
        """Gera embedding de consulta."""


def _calcular(
    documentos: Path,
    *,
    modelo: str = "modelo-a",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    schema_version: str = "1",
) -> str:
    return calcular_fingerprint(
        documentos,
        modelo_embedding=modelo,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        schema_version=schema_version,
    )


def _settings(tmp_path: Path, documentos: Path) -> Settings:
    return Settings(
        documents_dir=documentos,
        chroma_dir=tmp_path / "chroma",
        chroma_collection="fingerprint_teste",
        fingerprint_file=tmp_path / "data" / "fingerprint.json",
        embedding_model="modelo-a",
        chunk_size=512,
        chunk_overlap=64,
        top_k=5,
        openrouter_api_key=None,
        openrouter_model="modelo-llm",
        openrouter_base_url="https://example.test/api/v1",
        request_timeout_seconds=30,
        schema_version="1",
        log_level="INFO",
    )


def _salvar_csv_valido(
    caminho: Path,
    documento: dict[str, object],
    *,
    numero: str | None = None,
) -> None:
    registro = dict(documento)
    if numero is not None:
        registro["Número do Documento"] = numero
    pd.DataFrame([registro]).to_csv(caminho, index=False)


def test_mesmos_arquivos_produzem_mesmo_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    (documentos / "atos.csv").write_bytes(b"conteudo-estavel")

    assert _calcular(documentos) == _calcular(documentos)


def test_conteudo_alterado_muda_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    arquivo = documentos / "atos.csv"
    arquivo.write_bytes(b"conteudo-a")
    anterior = _calcular(documentos)

    arquivo.write_bytes(b"conteudo-b")

    assert _calcular(documentos) != anterior


def test_arquivo_adicionado_muda_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    (documentos / "a.csv").write_bytes(b"a")
    anterior = _calcular(documentos)

    (documentos / "b.json").write_bytes(b"b")

    assert _calcular(documentos) != anterior


def test_arquivo_removido_muda_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    (documentos / "a.csv").write_bytes(b"a")
    removido = documentos / "b.xlsx"
    removido.write_bytes(b"b")
    anterior = _calcular(documentos)

    removido.unlink()

    assert _calcular(documentos) != anterior


def test_arquivo_renomeado_muda_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    original = documentos / "original.csv"
    original.write_bytes(b"mesmo-conteudo")
    anterior = _calcular(documentos)

    original.rename(documentos / "renomeado.csv")

    assert _calcular(documentos) != anterior


def test_ordem_de_criacao_dos_arquivos_nao_altera_fingerprint(tmp_path: Path) -> None:
    primeira = tmp_path / "primeira"
    segunda = tmp_path / "segunda"
    primeira.mkdir()
    segunda.mkdir()
    (primeira / "a.csv").write_bytes(b"a")
    (primeira / "b.json").write_bytes(b"b")
    (segunda / "b.json").write_bytes(b"b")
    (segunda / "a.csv").write_bytes(b"a")

    assert _calcular(primeira) == _calcular(segunda)


def test_mudanca_do_modelo_invalida_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()

    assert _calcular(documentos, modelo="modelo-a") != _calcular(
        documentos,
        modelo="modelo-b",
    )


def test_mudanca_do_chunk_size_invalida_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()

    assert _calcular(documentos, chunk_size=512) != _calcular(
        documentos,
        chunk_size=256,
    )


def test_mudanca_do_chunk_overlap_invalida_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()

    assert _calcular(documentos, chunk_overlap=64) != _calcular(
        documentos,
        chunk_overlap=32,
    )


def test_mudanca_da_versao_do_schema_invalida_fingerprint(tmp_path: Path) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()

    assert _calcular(documentos, schema_version="1") != _calcular(
        documentos,
        schema_version="2",
    )


def test_primeira_preparacao_indexa_e_salva_fingerprint(
    tmp_path: Path,
    documento_valido: dict[str, object],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    _salvar_csv_valido(documentos / "atos.csv", documento_valido)
    settings = _settings(tmp_path, documentos)

    resultado = preparar_base_vetorial(settings, embedding_deterministico)

    assert resultado.reindexado is True
    assert resultado.quantidade_chunks == 1
    assert resultado.store.colecao.count() == 1
    assert carregar_fingerprint(settings.fingerprint_file) == resultado.fingerprint


def test_fingerprint_igual_reutiliza_indice_sem_regenerar_embeddings(
    tmp_path: Path,
    documento_valido: dict[str, object],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    _salvar_csv_valido(documentos / "atos.csv", documento_valido)
    settings = _settings(tmp_path, documentos)
    preparar_base_vetorial(settings, embedding_deterministico)
    chamadas_anteriores = embedding_deterministico.chamadas

    resultado = preparar_base_vetorial(settings, embedding_deterministico)

    assert resultado.reindexado is False
    assert embedding_deterministico.chamadas == chamadas_anteriores
    assert resultado.store.colecao.count() == 1


def test_mudanca_documental_reconstroi_indice_e_atualiza_fingerprint(
    tmp_path: Path,
    documento_valido: dict[str, object],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    arquivo = documentos / "atos.csv"
    _salvar_csv_valido(arquivo, documento_valido)
    settings = _settings(tmp_path, documentos)
    primeiro = preparar_base_vetorial(settings, embedding_deterministico)

    _salvar_csv_valido(arquivo, documento_valido, numero="999/2026")
    segundo = preparar_base_vetorial(settings, embedding_deterministico)

    assert segundo.reindexado is True
    assert segundo.fingerprint != primeiro.fingerprint
    assert segundo.store.colecao.count() == 1
    [metadata] = segundo.store.colecao.get(include=["metadatas"])["metadatas"] or []
    assert metadata["numero"] == "999/2026"


def test_falha_de_indexacao_nao_salva_novo_fingerprint(
    tmp_path: Path,
    documento_valido: dict[str, object],
    embedding_deterministico: ModeloEmbedding,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    arquivo = documentos / "atos.csv"
    _salvar_csv_valido(arquivo, documento_valido)
    settings = _settings(tmp_path, documentos)
    anterior = preparar_base_vetorial(settings, embedding_deterministico).fingerprint
    _salvar_csv_valido(arquivo, documento_valido, numero="999/2026")

    def falhar_indexacao(*_: object, **__: object) -> int:
        raise VectorStoreError("falha simulada")

    monkeypatch.setattr(
        "severino_bot.mod_orquestrator.indexar_chunks",
        falhar_indexacao,
    )

    with pytest.raises(VectorStoreError, match="falha simulada"):
        preparar_base_vetorial(settings, embedding_deterministico)

    assert carregar_fingerprint(settings.fingerprint_file) == anterior
    conteudo = json.loads(settings.fingerprint_file.read_text(encoding="utf-8"))
    assert conteudo["fingerprint"] == anterior


def test_fingerprint_corrompido_forca_reindexacao(
    tmp_path: Path,
    documento_valido: dict[str, object],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    _salvar_csv_valido(documentos / "atos.csv", documento_valido)
    settings = _settings(tmp_path, documentos)
    preparar_base_vetorial(settings, embedding_deterministico)
    settings.fingerprint_file.write_text("{invalido", encoding="utf-8")

    resultado = preparar_base_vetorial(settings, embedding_deterministico)

    assert resultado.reindexado is True
    assert carregar_fingerprint(settings.fingerprint_file) == resultado.fingerprint


def test_mudanca_de_parametro_forca_reindexacao(
    tmp_path: Path,
    documento_valido: dict[str, object],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    documentos = tmp_path / "docs"
    documentos.mkdir()
    _salvar_csv_valido(documentos / "atos.csv", documento_valido)
    settings = _settings(tmp_path, documentos)
    primeiro = preparar_base_vetorial(settings, embedding_deterministico)

    alterado = replace(settings, chunk_size=256, chunk_overlap=32)
    segundo = preparar_base_vetorial(alterado, embedding_deterministico)

    assert segundo.reindexado is True
    assert segundo.fingerprint != primeiro.fingerprint