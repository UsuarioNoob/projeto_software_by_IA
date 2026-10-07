"""Integração exclusiva com a interface Chainlit."""

import logging


LOGGER = logging.getLogger(__name__)


def iniciar_interface() -> None:
    """Registra o bootstrap da UI; handlers serão adicionados incrementalmente."""
    LOGGER.info("Interface do Severino BOT carregada.")
