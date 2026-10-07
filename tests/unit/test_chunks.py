"""Testes TDD-CHUNK-001 a TDD-CHUNK-007 para criação de chunks."""

from __future__ import annotations

from llama_index.core.schema import TextNode
import pytest

from severino_bot.mod_docs import criar_chunks


def test_registro_valido_gera_ao_menos_um_chunk(
    documento_valido: dict[str, object],
) -> None:
    chunks = criar_chunks([documento_valido], chunk_size=512, chunk_overlap=64)

    assert chunks
    assert all(isinstance(chunk, TextNode) for chunk in chunks)


def test_texto_do_chunk_contem_campos_indexaveis(
    documento_valido: dict[str, object],
) -> None:
    [chunk] = criar_chunks([documento_valido], chunk_size=512, chunk_overlap=64)

    assert "Tipo: Provimento" in chunk.text
    assert "Número: 360/2026" in chunk.text
    assert "Assunto: Cartório Acolhedor" in chunk.text
    assert "Ementa: Institui diretrizes para atendimento acolhedor." in chunk.text
    assert "Situação: Vigente" in chunk.text


def test_chunk_possui_metadata_minima(
    documento_valido: dict[str, object],
) -> None:
    [chunk] = criar_chunks([documento_valido], chunk_size=512, chunk_overlap=64)

    assert chunk.metadata == {
        "tipo": "Provimento",
        "numero": "360/2026",
        "situacao": "Vigente",
        "data_diario": "2026-01-15",
        "numero_diario": 1234,
        "link_web": "https://example.test/provimento-360-2026",
    }


def test_ids_dos_chunks_sao_unicos_e_deterministicos(
    documentos_validos: list[dict[str, object]],
) -> None:
    primeira_execucao = criar_chunks(
        documentos_validos,
        chunk_size=512,
        chunk_overlap=64,
    )
    segunda_execucao = criar_chunks(
        documentos_validos,
        chunk_size=512,
        chunk_overlap=64,
    )

    ids_primeira = [chunk.node_id for chunk in primeira_execucao]
    ids_segunda = [chunk.node_id for chunk in segunda_execucao]

    assert len(ids_primeira) == len(set(ids_primeira))
    assert ids_primeira == ids_segunda


def test_texto_maior_que_chunk_size_gera_multiplos_chunks(
    documento_valido: dict[str, object],
) -> None:
    registro_longo = {
        **documento_valido,
        "Ementa": " ".join(f"termo{i}" for i in range(300)),
    }

    chunks = criar_chunks([registro_longo], chunk_size=64, chunk_overlap=12)

    assert len(chunks) > 1


def test_chunk_overlap_e_respeitado(
    documento_valido: dict[str, object],
) -> None:
    registro_longo = {
        **documento_valido,
        "Ementa": " ".join(f"palavra{i}" for i in range(300)),
    }

    chunks = criar_chunks([registro_longo], chunk_size=64, chunk_overlap=12)
    palavras_primeiro = chunks[0].text.split()
    palavras_segundo = chunks[1].text.split()

    maior_sobreposicao = max(
        (
            tamanho
            for tamanho in range(
                1,
                min(len(palavras_primeiro), len(palavras_segundo)) + 1,
            )
            if palavras_primeiro[-tamanho:] == palavras_segundo[:tamanho]
        ),
        default=0,
    )
    assert maior_sobreposicao > 0


def test_valores_nulos_nao_geram_excecao_ou_texto_none(
    documento_valido: dict[str, object],
) -> None:
    registro_com_nulos = {
        **documento_valido,
        "Assunto": None,
        "Ementa": None,
        "Data do Diário": None,
        "Link web": None,
    }

    chunks = criar_chunks([registro_com_nulos], chunk_size=512, chunk_overlap=64)

    assert chunks
    assert "Assunto: " in chunks[0].text
    assert "Ementa: " in chunks[0].text
    assert "None" not in chunks[0].text
    assert chunks[0].metadata["data_diario"] == ""
    assert chunks[0].metadata["link_web"] == ""


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap", "mensagem"),
    [
        (0, 0, "chunk_size"),
        (64, -1, "chunk_overlap"),
        (64, 64, "menor que chunk_size"),
    ],
)
def test_parametros_de_chunking_invalidos_geram_erro(
    documento_valido: dict[str, object],
    chunk_size: int,
    chunk_overlap: int,
    mensagem: str,
) -> None:
    with pytest.raises(ValueError, match=mensagem):
        criar_chunks(
            [documento_valido],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )