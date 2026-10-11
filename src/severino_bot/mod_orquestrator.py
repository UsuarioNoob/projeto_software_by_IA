"""Casos de uso, fingerprint e orquestração do pipeline RAG."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path

from severino_bot.config import Settings
from severino_bot.mod_api_ia import (
    SINAL_CONTEXTO_INSUFICIENTE,
    SessaoHTTP,
    consultar_openrouter,
)
from severino_bot.mod_docs import (
    arquivo_suportado,
    carregar_documentos,
    criar_chunks,
)
from severino_bot.mod_embedding import (
    ModeloEmbedding,
    ResultadoBusca,
    VectorStore,
    buscar_chunks,
    conectar_vector_store,
    criar_modelo_embedding,
    indexar_chunks,
)


LOGGER = logging.getLogger(__name__)
VERSAO_FORMATO_INDICE = "2"

MENSAGEM_CONTEXTO_INSUFICIENTE = (
    "Não encontrei essa informação na base de atos normativos disponível. "
    "Posso ajudar com informações presentes nos documentos indexados, como tipo e número "
    "do ato, assunto, ementa, situação, data e número do diário e link para o documento."
)


@dataclass(frozen=True, slots=True)
class ResultadoPreparacao:
    """Estado necessário para consultas após preparar o índice vetorial."""

    store: VectorStore
    modelo_embedding: ModeloEmbedding
    fingerprint: str
    quantidade_chunks: int
    reindexado: bool


@dataclass(frozen=True, slots=True)
class ResultadoResposta:
    """Resposta final acompanhada do contexto e das fontes recuperadas."""

    resposta: str
    contexto: str
    fontes: tuple[ResultadoBusca, ...]


def _arquivos_suportados(diretorio: Path) -> list[Path]:
    """Lista documentos considerados pelo carregamento e pelo fingerprint."""
    caminho = Path(diretorio)
    if not caminho.exists():
        raise FileNotFoundError(f"Diretório de documentos não encontrado: {caminho}")
    if not caminho.is_dir():
        raise NotADirectoryError(
            f"O caminho de documentos não é um diretório: {caminho}"
        )
    return sorted(
        (
            arquivo
            for arquivo in caminho.iterdir()
            if arquivo_suportado(arquivo)
        ),
        key=lambda arquivo: arquivo.name.casefold(),
    )


def calcular_fingerprint(
    diretorio_documentos: Path,
    *,
    modelo_embedding: str,
    chunk_size: int,
    chunk_overlap: int,
    schema_version: str,
) -> str:
    """Calcula um SHA-256 determinístico dos documentos e parâmetros semânticos."""
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser maior que zero.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap deve estar entre zero e chunk_size - 1.")

    digest = hashlib.sha256()
    parametros = json.dumps(
        {
            "chunk_overlap": chunk_overlap,
            "chunk_size": chunk_size,
            "formato_indice": VERSAO_FORMATO_INDICE,
            "modelo_embedding": modelo_embedding,
            "schema_version": schema_version,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest.update(parametros.encode("utf-8"))

    for arquivo in _arquivos_suportados(diretorio_documentos):
        nome = arquivo.name.encode("utf-8")
        digest.update(len(nome).to_bytes(8, byteorder="big"))
        digest.update(nome)
        with arquivo.open("rb") as stream:
            while bloco := stream.read(1024 * 1024):
                digest.update(bloco)

    return digest.hexdigest()


def carregar_fingerprint(caminho: Path) -> str | None:
    """Lê o fingerprint salvo; conteúdo ausente ou inválido força reindexação."""
    arquivo = Path(caminho)
    if not arquivo.exists():
        return None

    try:
        conteudo = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        LOGGER.warning("Fingerprint inválido ou ilegível: arquivo=%s", arquivo)
        return None

    fingerprint = conteudo.get("fingerprint") if isinstance(conteudo, dict) else None
    if not isinstance(fingerprint, str) or not fingerprint.strip():
        LOGGER.warning("Fingerprint sem valor válido: arquivo=%s", arquivo)
        return None
    return fingerprint


def salvar_fingerprint(caminho: Path, fingerprint: str) -> None:
    """Persiste o fingerprint por substituição atômica do arquivo anterior."""
    if not fingerprint.strip():
        raise ValueError("O fingerprint não pode ser vazio.")

    arquivo = Path(caminho)
    temporario = arquivo.with_name(f"{arquivo.name}.tmp")
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    conteudo = json.dumps(
        {"fingerprint": fingerprint},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    try:
        temporario.write_text(f"{conteudo}\n", encoding="utf-8")
        temporario.replace(arquivo)
    finally:
        temporario.unlink(missing_ok=True)


def preparar_base_vetorial(
    settings: Settings,
    modelo_embedding: ModeloEmbedding | None = None,
) -> ResultadoPreparacao:
    """Reutiliza ou reconstrói o índice conforme o fingerprint atual."""
    fingerprint_atual = calcular_fingerprint(
        settings.documents_dir,
        modelo_embedding=settings.embedding_model,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        schema_version=settings.schema_version,
    )
    fingerprint_salvo = carregar_fingerprint(settings.fingerprint_file)
    store = conectar_vector_store(settings.chroma_dir, settings.chroma_collection)
    modelo = modelo_embedding or criar_modelo_embedding(settings.embedding_model)

    if fingerprint_salvo == fingerprint_atual and store.colecao.count() > 0:
        quantidade = store.colecao.count()
        LOGGER.info(
            "Base vetorial reutilizada: colecao=%s fingerprint=%s registros=%d",
            settings.chroma_collection,
            fingerprint_atual,
            quantidade,
        )
        return ResultadoPreparacao(
            store=store,
            modelo_embedding=modelo,
            fingerprint=fingerprint_atual,
            quantidade_chunks=quantidade,
            reindexado=False,
        )

    registros = carregar_documentos(settings.documents_dir)
    chunks = criar_chunks(
        registros,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    quantidade = indexar_chunks(store, chunks, modelo, recriar=True)
    salvar_fingerprint(settings.fingerprint_file, fingerprint_atual)

    LOGGER.info(
        "Base vetorial reconstruída: colecao=%s fingerprint=%s registros=%d",
        settings.chroma_collection,
        fingerprint_atual,
        quantidade,
    )
    return ResultadoPreparacao(
        store=store,
        modelo_embedding=modelo,
        fingerprint=fingerprint_atual,
        quantidade_chunks=quantidade,
        reindexado=True,
    )


def montar_contexto(resultados: list[ResultadoBusca]) -> str:
    """Monta contexto rastreável preservando a ordem do retrieval."""
    blocos: list[str] = []
    for posicao, resultado in enumerate(resultados, start=1):
        linhas_metadata = [
            f"{chave}: {valor}"
            for chave, valor in sorted(resultado.metadata.items())
        ]
        metadata = "\n".join(linhas_metadata) if linhas_metadata else "(sem metadata)"
        blocos.append(
            "\n".join(
                (
                    f"[FONTE {posicao}]",
                    f"Chunk ID: {resultado.chunk_id}",
                    f"Distância: {resultado.distancia:.6f}",
                    "Metadata:",
                    metadata,
                    "Conteúdo:",
                    resultado.texto,
                )
            )
        )
    return "\n\n".join(blocos)


def _resposta_sem_informacao_relevante(resposta: str) -> bool:
    """Reconhece o sinal do LLM sem depender de caixa ou texto adicional acidental."""
    normalizada = resposta.strip().casefold()
    return (
        SINAL_CONTEXTO_INSUFICIENTE.casefold() in normalizada
        or "não encontrei informação suficiente nos documentos" in normalizada
    )


def responder_pergunta(
    pergunta: str,
    preparacao: ResultadoPreparacao,
    settings: Settings,
    *,
    session: SessaoHTTP | None = None,
) -> ResultadoResposta:
    """Executa retrieval, monta contexto e consulta o modelo de linguagem."""
    pergunta_normalizada = pergunta.strip()
    if not pergunta_normalizada:
        raise ValueError("A pergunta não pode ser vazia.")

    resultados = buscar_chunks(
        preparacao.store,
        pergunta_normalizada,
        preparacao.modelo_embedding,
        top_k=settings.top_k,
    )
    if not resultados:
        LOGGER.info("Pergunta sem contexto recuperado; chamada ao LLM ignorada.")
        return ResultadoResposta(
            resposta=MENSAGEM_CONTEXTO_INSUFICIENTE,
            contexto="",
            fontes=(),
        )

    contexto = montar_contexto(resultados)
    resposta = consultar_openrouter(
        pergunta=pergunta_normalizada,
        contexto=contexto,
        api_key=settings.openrouter_api_key,
        modelo=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        session=session,
    )

    if _resposta_sem_informacao_relevante(resposta):
        LOGGER.info(
            "Pergunta fora do escopo documental; fontes irrelevantes foram omitidas."
        )
        return ResultadoResposta(
            resposta=MENSAGEM_CONTEXTO_INSUFICIENTE,
            contexto="",
            fontes=(),
        )

    LOGGER.info(
        "Pergunta respondida: fontes=%d modelo=%s",
        len(resultados),
        settings.openrouter_model,
    )
    return ResultadoResposta(
        resposta=resposta,
        contexto=contexto,
        fontes=tuple(resultados),
    )
