"""Teste do bootstrap usado por ``chainlit run main.py``."""

from __future__ import annotations

from pathlib import Path
import runpy

import pytest

from severino_bot import mod_ui


def test_carregamento_do_main_registra_interface(
    mocker: pytest.MockFixture,
) -> None:
    iniciar = mocker.patch.object(mod_ui, "iniciar_interface")
    caminho = Path(__file__).resolve().parents[2] / "main.py"

    runpy.run_path(str(caminho), run_name="arquivo_chainlit")

    iniciar.assert_called_once_with()