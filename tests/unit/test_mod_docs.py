"""Testes TDD-DOC-001 a TDD-DOC-009 para carregamento documental."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from severino_bot.exceptions import DocumentLoadError, SchemaValidationError
from severino_bot.mod_docs import (
    CAMPOS_OBRIGATORIOS,
    _carregar_dataframe,
    _normalizar_valor,
    carregar_documentos,
)


def test_pasta_inexistente_gera_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        carregar_documentos(tmp_path / "inexistente")


def test_pasta_vazia_retorna_lista_vazia(pasta_documentos: Path) -> None:
    assert carregar_documentos(pasta_documentos) == []


def test_caminho_que_nao_e_diretorio_gera_erro(tmp_path: Path) -> None:
    arquivo = tmp_path / "documento.csv"
    arquivo.write_text("conteúdo", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="não é um diretório"):
        carregar_documentos(arquivo)


def test_carrega_csv_valido(
    pasta_documentos: Path,
    dataframe_valido: pd.DataFrame,
) -> None:
    dataframe_valido.to_csv(pasta_documentos / "atos.csv", index=False)

    registros = carregar_documentos(pasta_documentos)

    assert len(registros) == 2
    assert set(registros[0]) == set(CAMPOS_OBRIGATORIOS)
    assert registros[0]["Número do Documento"] == "360/2026"
    assert registros[0]["Número Diário"] == 1234


def test_carrega_xlsx_valido(
    pasta_documentos: Path,
    dataframe_valido: pd.DataFrame,
) -> None:
    dataframe_valido.to_excel(pasta_documentos / "atos.xlsx", index=False)

    registros = carregar_documentos(pasta_documentos)

    assert len(registros) == 2
    assert registros[1]["Assunto"] == "Atendimento digital"


def test_consolida_multiplos_formatos_suportados(
    pasta_documentos: Path,
    documento_valido: dict[str, object],
) -> None:
    pd.DataFrame([documento_valido]).to_csv(pasta_documentos / "a.csv", index=False)
    pd.DataFrame([{**documento_valido, "Número do Documento": "361/2026"}]).to_json(
        pasta_documentos / "b.json",
        orient="records",
        force_ascii=False,
    )
    pd.DataFrame([{**documento_valido, "Número do Documento": "362/2026"}]).to_parquet(
        pasta_documentos / "c.parquet",
        index=False,
    )

    registros = carregar_documentos(pasta_documentos)

    assert len(registros) == 3
    assert [registro["Número do Documento"] for registro in registros] == [
        "360/2026",
        "361/2026",
        "362/2026",
    ]


def test_ignora_extensao_desconhecida(
    pasta_documentos: Path,
    documento_valido: dict[str, object],
) -> None:
    (pasta_documentos / "notas.txt").write_text("não indexar", encoding="utf-8")
    (pasta_documentos / "dados.xml").write_text("<dados />", encoding="utf-8")
    (pasta_documentos / "ato.json").write_text(
        json.dumps([documento_valido], ensure_ascii=False),
        encoding="utf-8",
    )

    registros = carregar_documentos(pasta_documentos)

    assert len(registros) == 1
    assert registros[0]["Tipo"] == "Provimento"


def test_campo_obrigatorio_ausente_gera_schema_validation_error(
    pasta_documentos: Path,
    documento_valido: dict[str, object],
) -> None:
    invalido = {key: value for key, value in documento_valido.items() if key != "Ementa"}
    pd.DataFrame([invalido]).to_csv(pasta_documentos / "invalido.csv", index=False)

    with pytest.raises(SchemaValidationError, match="Ementa"):
        carregar_documentos(pasta_documentos)


def test_normaliza_nan_nat_e_timestamp_para_valores_estaveis(
    pasta_documentos: Path,
    documento_valido: dict[str, object],
) -> None:
    registro = {
        **documento_valido,
        "Assunto": float("nan"),
        "Ementa": pd.NA,
        "Data do Diário": pd.Timestamp("2026-02-03 14:30:00"),
        "Link web": pd.NaT,
    }
    pd.DataFrame([registro]).to_parquet(pasta_documentos / "nulos.parquet", index=False)

    [normalizado] = carregar_documentos(pasta_documentos)

    assert normalizado["Assunto"] is None
    assert normalizado["Ementa"] is None
    assert normalizado["Link web"] is None
    assert normalizado["Data do Diário"] == "2026-02-03T14:30:00"


def test_arquivo_suportado_invalido_invalida_toda_a_base(
    pasta_documentos: Path,
    documento_valido: dict[str, object],
) -> None:
    pd.DataFrame([documento_valido]).to_csv(pasta_documentos / "valido.csv", index=False)
    (pasta_documentos / "corrompido.xlsx").write_bytes(b"nao-e-uma-planilha")

    with pytest.raises(DocumentLoadError, match="corrompido.xlsx"):
        carregar_documentos(pasta_documentos)


def test_leitor_interno_rejeita_extensao_nao_suportada(tmp_path: Path) -> None:
    caminho = tmp_path / "ato.txt"
    caminho.write_text("não suportado", encoding="utf-8")

    with pytest.raises(ValueError, match="Extensão não suportada"):
        _carregar_dataframe(caminho)


def test_normalizacao_defensiva_converte_estrutura_para_texto() -> None:
    assert _normalizar_valor(["valor-a", "valor-b"]) == "['valor-a', 'valor-b']"


def test_normalizacao_defensiva_trata_item_que_falha() -> None:
    class ValorComItemInvalido:
        def item(self) -> object:
            raise ValueError("conversão indisponível")

        def __str__(self) -> str:
            return "valor-convertido"

    assert _normalizar_valor(ValorComItemInvalido()) == "valor-convertido"