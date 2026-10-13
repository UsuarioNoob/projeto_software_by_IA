"""Embeddings, persistência no ChromaDB e retrieval semântico."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re
from typing import Protocol
import unicodedata

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from llama_index.core.schema import TextNode

from severino_bot.exceptions import EmptyVectorStoreError, VectorStoreError


LOGGER = logging.getLogger(__name__)

PALAVRAS_IGNORADAS = frozenset(
    {
        "a",
        "ato",
        "atos",
        "as",
        "com",
        "da",
        "das",
        "de",
        "do",
        "dos",
        "e",
        "em",
        "falar",
        "fala",
        "falam",
        "falando",
        "informa",
        "informar",
        "me",
        "o",
        "os",
        "para",
        "por",
        "qual",
        "quais",
        "que",
        "quero",
        "relacionado",
        "relacionados",
        "relacionada",
        "relacionadas",
        "sabe",
        "sobre",
        "trata",
        "tratam",
        "tratar",
        "toda",
        "todas",
        "todo",
        "todos",
        "tudo",
        "voce",
    }
)


class ModeloEmbedding(Protocol):
    """Contrato mínimo para modelos usados na indexação."""

    def get_text_embedding_batch(self, textos: list[str]) -> list[list[float]]:
        """Converte uma lista de textos em vetores numéricos."""

    def get_query_embedding(self, texto: str) -> list[float]:
        """Converte uma pergunta em um vetor numérico."""


@dataclass(frozen=True, slots=True)
class ResultadoBusca:
    """Chunk recuperado com seus dados de origem e distância vetorial."""

    chunk_id: str
    texto: str
    metadata: dict[str, object]
    distancia: float


@dataclass(slots=True)
class VectorStore:
    """Mantém a conexão persistente e sua coleção ativa."""

    cliente: ClientAPI
    colecao: Collection
    nome_colecao: str

    def recriar_colecao(self) -> Collection:
        """Remove todos os dados substituindo a coleção por uma nova."""
        try:
            self.cliente.delete_collection(self.nome_colecao)
            self.colecao = self.cliente.get_or_create_collection(
                name=self.nome_colecao,
                embedding_function=None,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Não foi possível recriar a coleção '{self.nome_colecao}'."
            ) from exc
        return self.colecao


def criar_modelo_embedding(nome_modelo: str) -> ModeloEmbedding:
    """Cria o modelo Hugging Face configurado para embeddings locais."""
    if not nome_modelo.strip():
        raise ValueError("O nome do modelo de embedding não pode ser vazio.")

    # Importação local evita carregar sentence-transformers em operações que
    # apenas reconectam ao banco vetorial já persistido.
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    try:
        return HuggingFaceEmbedding(model_name=nome_modelo)
    except (OSError, RuntimeError, ValueError) as exc:
        raise VectorStoreError(
            f"Não foi possível carregar o modelo de embedding '{nome_modelo}'."
        ) from exc


def conectar_vector_store(diretorio: Path, nome_colecao: str) -> VectorStore:
    """Cria ou recupera uma coleção persistente do ChromaDB."""
    if not nome_colecao.strip():
        raise ValueError("O nome da coleção não pode ser vazio.")

    caminho = Path(diretorio)
    try:
        caminho.mkdir(parents=True, exist_ok=True)
        cliente = chromadb.PersistentClient(path=caminho)
        colecao = cliente.get_or_create_collection(
            name=nome_colecao,
            embedding_function=None,
        )
    except Exception as exc:
        raise VectorStoreError(
            f"Não foi possível conectar à coleção '{nome_colecao}' em '{caminho}'."
        ) from exc

    LOGGER.info(
        "Vector store conectado: colecao=%s caminho=%s registros=%d",
        nome_colecao,
        caminho,
        colecao.count(),
    )
    return VectorStore(
        cliente=cliente,
        colecao=colecao,
        nome_colecao=nome_colecao,
    )


def _gerar_embeddings(
    modelo_embedding: ModeloEmbedding,
    textos: list[str],
) -> list[list[float]]:
    """Gera embeddings e valida o contrato mínimo esperado pelo ChromaDB."""
    try:
        embeddings = modelo_embedding.get_text_embedding_batch(textos)
    except Exception as exc:
        raise VectorStoreError("Não foi possível gerar os embeddings dos chunks.") from exc

    if len(embeddings) != len(textos):
        raise VectorStoreError(
            "O modelo de embedding retornou quantidade diferente da solicitada."
        )
    if any(not embedding for embedding in embeddings):
        raise VectorStoreError("O modelo de embedding retornou um vetor vazio.")
    return embeddings


def _gerar_embedding_consulta(
    modelo_embedding: ModeloEmbedding,
    pergunta: str,
) -> list[float]:
    """Gera e valida o vetor utilizado em uma consulta semântica."""
    try:
        embedding = modelo_embedding.get_query_embedding(pergunta)
    except Exception as exc:
        raise VectorStoreError("Não foi possível gerar o embedding da pergunta.") from exc

    if not embedding:
        raise VectorStoreError("O modelo de embedding retornou um vetor de consulta vazio.")
    return embedding


def indexar_chunks(
    store: VectorStore,
    chunks: list[TextNode],
    modelo_embedding: ModeloEmbedding,
    *,
    recriar: bool = False,
) -> int:
    """Persiste chunks e vetores, reutilizando uma coleção válida por padrão."""
    quantidade_existente = store.colecao.count()
    if quantidade_existente > 0 and not recriar:
        LOGGER.info(
            "Índice reutilizado: colecao=%s registros=%d",
            store.nome_colecao,
            quantidade_existente,
        )
        return quantidade_existente

    if recriar:
        store.recriar_colecao()

    if not chunks:
        LOGGER.info("Nenhum chunk recebido para indexação: colecao=%s", store.nome_colecao)
        return 0

    ids = [chunk.node_id for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise VectorStoreError("Não é possível indexar chunks com IDs duplicados.")

    textos = [chunk.text for chunk in chunks]
    metadados = [dict(chunk.metadata) for chunk in chunks]
    embeddings = _gerar_embeddings(modelo_embedding, textos)

    try:
        store.colecao.add(
            ids=ids,
            documents=textos,
            metadatas=metadados,
            embeddings=embeddings,
        )
    except Exception as exc:
        raise VectorStoreError(
            f"Não foi possível persistir os chunks na coleção '{store.nome_colecao}'."
        ) from exc

    quantidade_persistida = store.colecao.count()
    if quantidade_persistida != len(chunks):
        raise VectorStoreError(
            "A quantidade persistida no ChromaDB difere da quantidade de chunks."
        )

    LOGGER.info(
        "Chunks indexados: colecao=%s registros=%d",
        store.nome_colecao,
        quantidade_persistida,
    )
    return quantidade_persistida


def _normalizar_texto_busca(texto: object) -> str:
    """Normaliza caixa, acentos e pontuação para comparação lexical."""
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", str(texto or "").casefold())
        if not unicodedata.combining(caractere)
    )
    return " ".join(re.findall(r"[a-z0-9]+", sem_acentos))


def _termos_relevantes(pergunta: str) -> tuple[str, ...]:
    """Extrai termos úteis de uma pergunta ampla sem depender do LLM."""
    termos = {
        termo
        for termo in _normalizar_texto_busca(pergunta).split()
        if len(termo) >= 3 and termo not in PALAVRAS_IGNORADAS
    }
    return tuple(sorted(termos))


def _resultados_lexicais(store: VectorStore, pergunta: str) -> list[ResultadoBusca]:
    """Localiza menções diretas com a melhor cobertura temática da pergunta."""
    termos = _termos_relevantes(pergunta)
    if not termos:
        return []

    try:
        resposta = store.colecao.get(include=["documents", "metadatas"])
    except Exception as exc:
        raise VectorStoreError(
            f"Não foi possível consultar os campos textuais de '{store.nome_colecao}'."
        ) from exc

    ids = resposta.get("ids") or []
    documentos = resposta.get("documents") or []
    metadados = resposta.get("metadatas") or []
    if not (len(ids) == len(documentos) == len(metadados)):
        raise VectorStoreError("O ChromaDB retornou campos lexicais inconsistentes.")

    candidatos: list[tuple[int, ResultadoBusca]] = []
    documentos_encontrados: set[str] = set()
    for chunk_id, documento, metadata_original in zip(
        ids, documentos, metadados, strict=True
    ):
        metadata = dict(metadata_original or {})
        campos = _normalizar_texto_busca(
            f"{metadata.get('assunto', '')} {metadata.get('ementa', '')}"
        )
        pontuacao = sum(1 for termo in termos if termo in campos.split())
        if pontuacao == 0:
            continue

        documento_id = str(metadata.get("documento_id") or chunk_id)
        if documento_id in documentos_encontrados:
            continue
        documentos_encontrados.add(documento_id)
        candidatos.append(
            (
                pontuacao,
                ResultadoBusca(
                    chunk_id=str(chunk_id),
                    texto=documento or "",
                    metadata=metadata,
                    distancia=0.0,
                ),
            )
        )

    candidatos.sort(
        key=lambda item: (
            -item[0],
            str(item[1].metadata.get("numero", "")).casefold(),
            item[1].chunk_id,
        )
    )
    if not candidatos:
        return []

    melhor_pontuacao = candidatos[0][0]
    return [
        resultado
        for pontuacao, resultado in candidatos
        if pontuacao == melhor_pontuacao
    ]


def buscar_chunks(
    store: VectorStore,
    pergunta: str,
    modelo_embedding: ModeloEmbedding,
    *,
    top_k: int,
) -> list[ResultadoBusca]:
    """Prioriza menções textuais precisas e usa proximidade semântica como fallback."""
    pergunta_normalizada = pergunta.strip()
    if not pergunta_normalizada:
        raise ValueError("A pergunta não pode ser vazia.")
    if top_k <= 0:
        raise ValueError("top_k deve ser maior que zero.")

    quantidade = store.colecao.count()
    if quantidade == 0:
        raise EmptyVectorStoreError(
            f"A coleção vetorial '{store.nome_colecao}' está vazia."
        )

    resultados_lexicais = _resultados_lexicais(store, pergunta_normalizada)
    if resultados_lexicais:
        LOGGER.info(
            "Retrieval lexical preciso concluído: colecao=%s resultados=%d",
            store.nome_colecao,
            len(resultados_lexicais),
        )
        return resultados_lexicais

    embedding = _gerar_embedding_consulta(modelo_embedding, pergunta_normalizada)
    try:
        resposta = store.colecao.query(
            query_embeddings=[embedding],
            n_results=min(top_k, quantidade),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        raise VectorStoreError(
            f"Não foi possível consultar a coleção '{store.nome_colecao}'."
        ) from exc

    ids = resposta.get("ids") or []
    documentos = resposta.get("documents") or []
    metadados = resposta.get("metadatas") or []
    distancias = resposta.get("distances") or []
    if not ids or not documentos or not metadados or not distancias:
        raise VectorStoreError("O ChromaDB retornou uma resposta de consulta incompleta.")

    ids_consulta = ids[0]
    documentos_consulta = documentos[0]
    metadados_consulta = metadados[0]
    distancias_consulta = distancias[0]
    tamanhos = {
        len(ids_consulta),
        len(documentos_consulta),
        len(metadados_consulta),
        len(distancias_consulta),
    }
    if len(tamanhos) != 1:
        raise VectorStoreError("O ChromaDB retornou campos de consulta inconsistentes.")

    resultados_semanticos = [
        ResultadoBusca(
            chunk_id=chunk_id,
            texto=documento or "",
            metadata=dict(metadata or {}),
            distancia=float(distancia),
        )
        for chunk_id, documento, metadata, distancia in zip(
            ids_consulta,
            documentos_consulta,
            metadados_consulta,
            distancias_consulta,
            strict=True,
        )
    ]
    resultados_semanticos.sort(key=lambda resultado: resultado.distancia)

    resultados: list[ResultadoBusca] = []
    documentos_adicionados: set[str] = set()
    for resultado in resultados_semanticos:
        documento_id = str(resultado.metadata.get("documento_id") or resultado.chunk_id)
        if documento_id in documentos_adicionados:
            continue
        documentos_adicionados.add(documento_id)
        resultados.append(resultado)

    LOGGER.info(
        "Retrieval semântico concluído: colecao=%s top_k=%d resultados=%d",
        store.nome_colecao,
        top_k,
        len(resultados),
    )
    return resultados
