"""Testes TDD-SEARCH-001 a TDD-SEARCH-007 para retrieval semântico."""

from __future__ import annotations

from pathlib import Path

from llama_index.core.schema import TextNode
import pytest

from severino_bot.exceptions import EmptyVectorStoreError
from severino_bot.mod_embedding import (
    VectorStore,
    _termos_relevantes,
    buscar_chunks,
    conectar_vector_store,
    indexar_chunks,
)


def test_termos_relevantes_removem_palavras_genericas() -> None:
    assert _termos_relevantes(
        "Me informa tudo o que você sabe sobre férias"
    ) == ("ferias",)


class EmbeddingSemanticoControlado:
    """Modelo local com espaços semânticos previsíveis para os testes."""

    def get_text_embedding_batch(self, textos: list[str]) -> list[list[float]]:
        return [self._vetor(texto) for texto in textos]

    def get_query_embedding(self, texto: str) -> list[float]:
        return self._vetor(texto)

    @staticmethod
    def _vetor(texto: str) -> list[float]:
        normalizado = texto.casefold()
        return [
            1.0 if "cartório" in normalizado or "cartorio" in normalizado else 0.0,
            1.0 if "motocicleta" in normalizado else 0.0,
            1.0 if "banco de dados" in normalizado else 0.0,
        ]


@pytest.fixture
def store_semantico(chroma_temporario: Path) -> tuple[VectorStore, EmbeddingSemanticoControlado]:
    modelo = EmbeddingSemanticoControlado()
    chunks = [
        TextNode(
            id_="chunk-cartorios",
            text="Normas para atendimento acolhedor em cartórios.",
            metadata={"numero": "360/2026", "tipo": "Provimento"},
        ),
        TextNode(
            id_="chunk-motocicletas",
            text="Regras de circulação para motocicletas.",
            metadata={"numero": "101/2026", "tipo": "Portaria"},
        ),
        TextNode(
            id_="chunk-bancos",
            text="Política de manutenção de banco de dados.",
            metadata={"numero": "202/2026", "tipo": "Resolução"},
        ),
    ]
    store = conectar_vector_store(chroma_temporario, "retrieval_semantico")
    indexar_chunks(store, chunks, modelo)
    return store, modelo


def test_pergunta_vazia_gera_erro(
    store_semantico: tuple[VectorStore, EmbeddingSemanticoControlado],
) -> None:
    store, modelo = store_semantico

    with pytest.raises(ValueError, match="pergunta"):
        buscar_chunks(store, "   ", modelo, top_k=2)


@pytest.mark.parametrize("top_k", [0, -1])
def test_top_k_nao_positivo_gera_erro(
    store_semantico: tuple[VectorStore, EmbeddingSemanticoControlado],
    top_k: int,
) -> None:
    store, modelo = store_semantico

    with pytest.raises(ValueError, match="top_k"):
        buscar_chunks(store, "cartórios", modelo, top_k=top_k)


def test_quantidade_retornada_respeita_top_k(
    store_semantico: tuple[VectorStore, EmbeddingSemanticoControlado],
) -> None:
    store, modelo = store_semantico

    resultados = buscar_chunks(store, "cartórios", modelo, top_k=2)

    assert len(resultados) <= 2


def test_pergunta_sobre_cartorios_ranqueia_documento_correto_primeiro(
    store_semantico: tuple[VectorStore, EmbeddingSemanticoControlado],
) -> None:
    store, modelo = store_semantico

    resultados = buscar_chunks(
        store,
        "Como deve funcionar o atendimento nos cartórios?",
        modelo,
        top_k=3,
    )

    assert resultados[0].chunk_id == "chunk-cartorios"
    assert "cartórios" in resultados[0].texto


def test_colecao_vazia_gera_erro_explicito(
    chroma_temporario: Path,
) -> None:
    store = conectar_vector_store(chroma_temporario, "retrieval_vazio")
    modelo = EmbeddingSemanticoControlado()

    with pytest.raises(EmptyVectorStoreError, match="vazia"):
        buscar_chunks(store, "cartórios", modelo, top_k=2)


def test_resultados_respeitam_ordem_de_relevancia(
    store_semantico: tuple[VectorStore, EmbeddingSemanticoControlado],
) -> None:
    store, modelo = store_semantico

    resultados = buscar_chunks(store, "motocicleta", modelo, top_k=3)

    assert resultados[0].chunk_id == "chunk-motocicletas"
    assert [resultado.distancia for resultado in resultados] == sorted(
        resultado.distancia for resultado in resultados
    )


def test_metadata_original_permanece_acessivel(
    store_semantico: tuple[VectorStore, EmbeddingSemanticoControlado],
) -> None:
    store, modelo = store_semantico

    [resultado] = buscar_chunks(store, "cartórios", modelo, top_k=1)

    assert resultado.metadata == {
        "numero": "360/2026",
        "tipo": "Provimento",
    }


def test_busca_textual_retorna_todos_documentos_por_assunto_e_ementa(
    chroma_temporario: Path,
) -> None:
    modelo = EmbeddingSemanticoControlado()
    chunks = [
        TextNode(
            id_="ferias-assunto",
            text="Ato sobre afastamento.",
            metadata={
                "documento_id": "doc-1",
                "numero": "1/2026",
                "assunto": "Férias de servidores",
                "ementa": "Disciplina o período anual.",
            },
        ),
        TextNode(
            id_="ferias-ementa",
            text="Outro ato sobre afastamento.",
            metadata={
                "documento_id": "doc-2",
                "numero": "2/2026",
                "assunto": "Gestão de pessoas",
                "ementa": "Regulamenta férias e substituições.",
            },
        ),
        TextNode(
            id_="sem-ferias",
            text="Ato sem relação direta.",
            metadata={
                "documento_id": "doc-3",
                "numero": "3/2026",
                "assunto": "Compras",
                "ementa": "Regulamenta aquisições.",
            },
        ),
    ]
    store = conectar_vector_store(chroma_temporario, "retrieval_lexical")
    indexar_chunks(store, chunks, modelo)

    resultados = buscar_chunks(
        store,
        "Me informa tudo o que você sabe sobre férias",
        modelo,
        top_k=1,
    )

    assert [resultado.metadata["numero"] for resultado in resultados[:2]] == [
        "1/2026",
        "2/2026",
    ]