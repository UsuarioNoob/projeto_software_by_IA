"""Testes TDD-VEC-001 a TDD-VEC-007 para o armazenamento vetorial."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from llama_index.core.schema import TextNode
import pytest

from severino_bot.exceptions import VectorStoreError
from severino_bot.mod_embedding import conectar_vector_store, indexar_chunks


class ModeloEmbedding(Protocol):
    chamadas: int

    def get_text_embedding_batch(self, textos: list[str]) -> list[list[float]]:
        """Contrato mínimo usado pelo indexador."""

    def get_query_embedding(self, texto: str) -> list[float]:
        """Contrato mínimo usado pelo retrieval."""


def test_conectar_cria_ou_recupera_colecao(chroma_temporario: Path) -> None:
    primeiro = conectar_vector_store(chroma_temporario, "atos_teste")
    segundo = conectar_vector_store(chroma_temporario, "atos_teste")

    assert primeiro.colecao.name == "atos_teste"
    assert segundo.colecao.name == "atos_teste"
    assert segundo.colecao.count() == 0


def test_dados_persistem_apos_reconexao(
    chroma_temporario: Path,
    chunks_validos: list[TextNode],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    store = conectar_vector_store(chroma_temporario, "atos_persistentes")
    indexar_chunks(store, chunks_validos, embedding_deterministico)

    reconectado = conectar_vector_store(chroma_temporario, "atos_persistentes")

    assert reconectado.colecao.count() == len(chunks_validos)


def test_indexar_chunks_persiste_ids_textos_metadados_e_embeddings(
    chroma_temporario: Path,
    chunks_validos: list[TextNode],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    store = conectar_vector_store(chroma_temporario, "atos_indexados")

    quantidade = indexar_chunks(store, chunks_validos, embedding_deterministico)
    persistidos = store.colecao.get(include=["documents", "metadatas", "embeddings"])

    assert quantidade == len(chunks_validos)
    assert set(persistidos["ids"]) == {chunk.node_id for chunk in chunks_validos}
    assert set(persistidos["documents"] or []) == {chunk.text for chunk in chunks_validos}
    assert persistidos["embeddings"] is not None
    assert len(persistidos["embeddings"]) == len(chunks_validos)
    assert all(metadata and "numero" in metadata for metadata in persistidos["metadatas"] or [])


def test_recriar_falso_com_colecao_populada_nao_regenera_embeddings(
    chroma_temporario: Path,
    chunks_validos: list[TextNode],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    store = conectar_vector_store(chroma_temporario, "atos_reutilizados")
    indexar_chunks(store, chunks_validos, embedding_deterministico)
    chamadas_anteriores = embedding_deterministico.chamadas

    quantidade = indexar_chunks(
        store,
        chunks_validos,
        embedding_deterministico,
        recriar=False,
    )

    assert quantidade == len(chunks_validos)
    assert embedding_deterministico.chamadas == chamadas_anteriores


def test_recriar_verdadeiro_elimina_dados_antigos(
    chroma_temporario: Path,
    chunks_validos: list[TextNode],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    store = conectar_vector_store(chroma_temporario, "atos_recriados")
    indexar_chunks(store, chunks_validos, embedding_deterministico)
    chunk_novo = TextNode(
        id_="chunk-substituto",
        text="Tipo: Portaria\nNúmero: 999/2026\nAssunto: Substituição",
        metadata={"numero": "999/2026"},
    )

    quantidade = indexar_chunks(
        store,
        [chunk_novo],
        embedding_deterministico,
        recriar=True,
    )
    persistidos = store.colecao.get(include=[])

    assert quantidade == 1
    assert persistidos["ids"] == ["chunk-substituto"]


def test_colecoes_diferentes_permanecem_isoladas(
    chroma_temporario: Path,
    chunks_validos: list[TextNode],
    embedding_deterministico: ModeloEmbedding,
) -> None:
    primeira = conectar_vector_store(chroma_temporario, "colecao_primeira")
    segunda = conectar_vector_store(chroma_temporario, "colecao_segunda")

    indexar_chunks(primeira, chunks_validos[:1], embedding_deterministico)
    indexar_chunks(segunda, chunks_validos, embedding_deterministico)

    assert primeira.colecao.count() == 1
    assert segunda.colecao.count() == len(chunks_validos)
    assert primeira.colecao.get(include=[])["ids"] == [chunks_validos[0].node_id]
    assert set(segunda.colecao.get(include=[])["ids"]) == {
        chunk.node_id for chunk in chunks_validos
    }


def test_falha_de_persistencia_gera_erro_explicito(
    chroma_temporario: Path,
    chunks_validos: list[TextNode],
    embedding_deterministico: ModeloEmbedding,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = conectar_vector_store(chroma_temporario, "atos_com_falha")

    def falhar_ao_adicionar(**_: object) -> None:
        raise RuntimeError("disco indisponível")

    monkeypatch.setattr(store.colecao, "add", falhar_ao_adicionar)

    with pytest.raises(VectorStoreError, match="persistir.*atos_com_falha"):
        indexar_chunks(store, chunks_validos, embedding_deterministico)