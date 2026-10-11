"""Ponto de entrada do Severino BOT para o Chainlit."""

from severino_bot.mod_ui import iniciar_interface


def main() -> None:
    """Inicializa o registro da interface da aplicação."""
    iniciar_interface()


# O Chainlit carrega o arquivo por importação, sem executá-lo como ``__main__``.
# O registro precisa ocorrer durante o carregamento do módulo.
main()
