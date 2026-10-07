"""Carregamento, validação e normalização de documentos estruturados."""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Final

import pandas as pd
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode

from severino_bot.exceptions import DocumentLoadError, SchemaValidationError


LOGGER = logging.getLogger(__name__)

CAMPOS_OBRIGATORIOS: Final[tuple[str, ...]] = (
    "Tipo",
    "Número do Documento",
    "Assunto",
    "Ementa",
    "Situação",
    "Data do Diário",
    "Número Diário",
    "Link web",
)

EXTENSOES_SUPORTADAS: Final[frozenset[str]] = frozenset(
    {".csv", ".xls", ".xlsx", ".xlsm", ".json", ".parquet"}
)

CHAVES_METADATA: Final[dict[str, str]] = {
    "Tipo": "tipo",
    "Número do Documento": "numero",
    "Situação": "situacao",
    "Data do Diário": "data_diario",
    "Número Diário": "numero_diario",
    "Link web": "link_web",
}


def _carregar_dataframe(caminho: Path) -> pd.DataFrame:
    """Lê um arquivo suportado e devolve sua representação tabular."""
    extensao = caminho.suffix.lower()

    if extensao == ".csv":
        return pd.read_csv(caminho)
    if extensao in {".xls", ".xlsx", ".xlsm"}:
        return pd.read_excel(caminho)
    if extensao == ".json":
        return pd.read_json(caminho)
    if extensao == ".parquet":
        return pd.read_parquet(caminho)

    raise ValueError(f"Extensão não suportada: {extensao}")


def _validar_schema(dataframe: pd.DataFrame, caminho: Path) -> None:
    """Garante que todos os campos definidos no contrato estejam presentes."""
    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in dataframe.columns]
    if ausentes:
        campos = ", ".join(ausentes)
        raise SchemaValidationError(
            f"Schema inválido em '{caminho.name}'. Campos ausentes: {campos}."
        )


def _normalizar_valor(valor: Any) -> object:
    """Converte valores tabulares para tipos Python estáveis e serializáveis."""
    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        # Estruturas não escalares não são esperadas no schema, mas devem seguir
        # para conversão explícita em vez de causarem uma falha ambígua aqui.
        pass

    if isinstance(valor, pd.Timestamp):
        return valor.isoformat()
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()

    item = getattr(valor, "item", None)
    if callable(item):
        try:
            return item()
        except (TypeError, ValueError):
            pass

    if isinstance(valor, (str, int, float, bool)):
        return valor

    return str(valor)


def _normalizar_registros(dataframe: pd.DataFrame) -> list[dict[str, object]]:
    """Normaliza registros preservando somente o contrato oficial e sua ordem."""
    registros: list[dict[str, object]] = []
    for registro in dataframe.loc[:, list(CAMPOS_OBRIGATORIOS)].to_dict(orient="records"):
        registros.append(
            {
                campo: _normalizar_valor(registro[campo])
                for campo in CAMPOS_OBRIGATORIOS
            }
        )
    return registros


def carregar_documentos(diretorio: Path) -> list[dict[str, object]]:
    """Carrega e consolida arquivos estruturados presentes em ``diretorio``.

    Arquivos com extensões desconhecidas são ignorados. Qualquer falha de leitura
    em um arquivo suportado invalida a operação inteira, evitando uma base
    parcialmente indexada.
    """
    caminho_diretorio = Path(diretorio)
    if not caminho_diretorio.exists():
        raise FileNotFoundError(
            f"Diretório de documentos não encontrado: {caminho_diretorio}"
        )
    if not caminho_diretorio.is_dir():
        raise NotADirectoryError(
            f"O caminho de documentos não é um diretório: {caminho_diretorio}"
        )

    arquivos = sorted(
        (
            caminho
            for caminho in caminho_diretorio.iterdir()
            if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_SUPORTADAS
        ),
        key=lambda caminho: caminho.name.casefold(),
    )

    registros_consolidados: list[dict[str, object]] = []
    for caminho in arquivos:
        try:
            dataframe = _carregar_dataframe(caminho)
        except (OSError, ValueError, TypeError, ImportError) as exc:
            raise DocumentLoadError(
                f"Falha ao carregar o documento '{caminho.name}'."
            ) from exc

        _validar_schema(dataframe, caminho)
        registros_consolidados.extend(_normalizar_registros(dataframe))
        LOGGER.info(
            "Documento carregado: arquivo=%s registros=%d",
            caminho.name,
            len(dataframe),
        )

    return registros_consolidados


def _texto_indexavel(registro: dict[str, object]) -> str:
    """Monta o conteúdo textual definido no contrato de dados do SDD."""
    return "\n".join(
        (
            f"Tipo: {_valor_textual(registro.get('Tipo'))}",
            f"Número: {_valor_textual(registro.get('Número do Documento'))}",
            f"Assunto: {_valor_textual(registro.get('Assunto'))}",
            f"Ementa: {_valor_textual(registro.get('Ementa'))}",
            f"Situação: {_valor_textual(registro.get('Situação'))}",
        )
    )


def _valor_textual(valor: object) -> str:
    """Converte um valor normalizado em texto sem materializar ``None``."""
    return "" if valor is None else str(valor)


def _metadata_do_registro(registro: dict[str, object]) -> dict[str, object]:
    """Extrai metadata mínima usando somente escalares aceitos pelo ChromaDB."""
    metadata: dict[str, object] = {}
    for campo, chave in CHAVES_METADATA.items():
        valor = _normalizar_valor(registro.get(campo))
        metadata[chave] = "" if valor is None else valor
    return metadata


def _id_documento(registro: dict[str, object], indice: int) -> str:
    """Gera identidade reproduzível, inclusive para registros duplicados."""
    conteudo = json.dumps(
        {
            "indice": indice,
            "registro": {
                campo: _normalizar_valor(registro.get(campo))
                for campo in CAMPOS_OBRIGATORIOS
            },
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def _id_chunk(documento_id: str, indice: int, texto: str) -> str:
    """Gera identidade reproduzível para um fragmento do documento."""
    conteudo = f"{documento_id}:{indice}:{texto}"
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def _validar_parametros_chunking(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser maior que zero.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap não pode ser negativo.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap deve ser menor que chunk_size.")


def criar_chunks(
    registros: list[dict[str, object]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextNode]:
    """Converte registros normalizados em chunks determinísticos do LlamaIndex."""
    _validar_parametros_chunking(chunk_size, chunk_overlap)
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        include_metadata=False,
        include_prev_next_rel=False,
    )

    chunks: list[TextNode] = []
    ids: set[str] = set()
    for indice_registro, registro in enumerate(registros):
        texto = _texto_indexavel(registro)
        metadata = _metadata_do_registro(registro)
        documento_id = _id_documento(registro, indice_registro)
        # A metadata é aplicada aos TextNode finais. Incluí-la no Document
        # temporário faria o SentenceSplitter descontar seus tokens do espaço
        # disponível, mesmo com include_metadata=False.
        documento = Document(text=texto, id_=documento_id)

        nos = splitter.get_nodes_from_documents([documento])
        for indice_chunk, no in enumerate(nos):
            chunk_id = _id_chunk(documento_id, indice_chunk, no.text)
            if chunk_id in ids:
                raise ValueError(f"ID de chunk duplicado detectado: {chunk_id}")
            ids.add(chunk_id)
            chunks.append(
                TextNode(
                    id_=chunk_id,
                    text=no.text,
                    metadata=dict(metadata),
                    excluded_embed_metadata_keys=list(metadata),
                    excluded_llm_metadata_keys=list(metadata),
                )
            )

    LOGGER.info(
        "Chunks criados: registros=%d chunks=%d chunk_size=%d chunk_overlap=%d",
        len(registros),
        len(chunks),
        chunk_size,
        chunk_overlap,
    )
    return chunks
