"""Configuração externa e validada da aplicação."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _project_path(raw_value: str) -> Path:
    path = Path(raw_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número inteiro.") from exc
    if value <= 0:
        raise ValueError(f"{name} deve ser maior que zero.")
    return value


def _non_negative_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número inteiro.") from exc
    if value < 0:
        raise ValueError(f"{name} não pode ser negativo.")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Parâmetros necessários aos componentes do Severino BOT."""

    documents_dir: Path
    chroma_dir: Path
    chroma_collection: str
    fingerprint_file: Path
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_base_url: str
    request_timeout_seconds: int
    schema_version: str
    log_level: str

    def __post_init__(self) -> None:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP deve ser menor que CHUNK_SIZE.")
        if not self.chroma_collection.strip():
            raise ValueError("CHROMA_COLLECTION não pode ser vazio.")
        if not self.embedding_model.strip():
            raise ValueError("EMBEDDING_MODEL não pode ser vazio.")


def carregar_configuracao(env_file: Path | None = None) -> Settings:
    """Carrega configurações do ambiente sem exigir credencial na importação."""
    load_dotenv(dotenv_path=env_file or PROJECT_ROOT / ".env", override=False)

    token = os.getenv("OPENROUTER_API_KEY")
    return Settings(
        documents_dir=_project_path(os.getenv("DOCUMENTS_DIR", "docs")),
        chroma_dir=_project_path(os.getenv("CHROMA_DIR", "chroma_db")),
        chroma_collection=os.getenv("CHROMA_COLLECTION", "severino_bot"),
        fingerprint_file=_project_path(
            os.getenv("FINGERPRINT_FILE", "data/fingerprint.json")
        ),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        ),
        chunk_size=_positive_int("CHUNK_SIZE", 512),
        chunk_overlap=_non_negative_int("CHUNK_OVERLAP", 64),
        top_k=_positive_int("TOP_K", 5),
        openrouter_api_key=token.strip() if token and token.strip() else None,
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        openrouter_base_url=os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).rstrip("/"),
        request_timeout_seconds=_positive_int("REQUEST_TIMEOUT_SECONDS", 30),
        schema_version=os.getenv("SCHEMA_VERSION", "1"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


def configurar_logging(level: str) -> None:
    """Configura logging da aplicação com formato consistente."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Nível de log inválido: {level}")
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
