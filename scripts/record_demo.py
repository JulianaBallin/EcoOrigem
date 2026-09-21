"""Drive the web interface through the demonstration script.

Generates the screenshots used in the documentation and a screen recording that
serves as the backup video for the presentation. Requires Playwright and Google
Chrome (``pip install -r requirements-docs.txt``) and a running stack with the
contract deployed and demo lots seeded (``make docker-up docker-seed``).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "assets" / "img" / "evidencias"


class Demo:
    """Small helper that pauses between steps so the recording is readable."""

    def __init__(self, page: Page, base: str, pace: int) -> None:
        self.page = page
        self.base = base
        self.pace = pace

    def pause(self, factor: float = 1.0) -> None:
        """Wait a multiple of the base pace."""
        self.page.wait_for_timeout(int(self.pace * factor))

    def goto(self, route: str) -> None:
        """Open a route of the single page application."""
        self.page.goto(f"{self.base}/#/{route}")
        self.page.wait_for_load_state("networkidle")
        self.pause()

    def wallet(self, name: str) -> None:
        """Select the active wallet by its display name."""
        self.page.select_option("#wallet-select", label=name)
        self.pause(0.5)

    def shot(self, name: str, full: bool = False) -> None:
        """Save a screenshot under assets/img/evidencias."""
        self.page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=full)

    def operation(self, title: str) -> None:
        """Choose an operation in the list."""
        self.page.get_by_role("button", name=title).first.click()
        self.pause(0.5)

    def fill(self, op: str, field: str, value: str) -> None:
        """Fill one field of the operation form."""
        self.page.fill(f"#f-{op}-{field}", value)

    def send(self) -> None:
        """Submit the form and wait for the outcome panel."""
        self.page.get_by_role("button", name="Assinar e enviar à blockchain").click()
        self.page.wait_for_selector(".outcome")
        self.pause(1.5)


def expect(page: Page, selector: str, message: str) -> None:
    """Fail the run when the expected outcome panel is not shown."""
    if page.locator(selector).count() != 1:
        raise RuntimeError(f"Resultado inesperado: {message}")


def run(demo: Demo) -> None:  # pylint: disable=too-many-statements
    """Execute the whole demonstration script."""
    page = demo.page
    # 1. Dashboard with the running local blockchain
    demo.goto("painel")
    demo.shot("01-painel", full=True)

    # 2. Valid operation: producer registers a lot
    demo.goto("registrar")
    demo.wallet("Produtor")
    demo.fill(
        "register_lot", "origin", "Comunidade Ribeirinha do Rio Negro, Novo Airão"
    )
    demo.fill("register_lot", "quantity_kg", "250")
    demo.shot("02-registrar-formulario")
    demo.send()
    expect(page, ".outcome.ok", "register_lot should be confirmed")
    demo.shot("03-registrar-confirmado")
    lot_id = page.locator(".outcome.ok a.btn").first.inner_text().split()[-1]

    # 3. Second valid step, by another profile
    demo.wallet("Beneficiador")
    demo.operation("Registrar beneficiamento")
    demo.fill("record_processing", "lot_id", lot_id)
    demo.fill(
        "record_processing",
        "description",
        "Despolpamento, pasteurização e congelamento.",
    )
    demo.send()
    expect(page, ".outcome.ok", "record_processing should be confirmed")

    # 4. Query the record and the state change
    demo.goto(f"consultar/{lot_id}")
    page.wait_for_selector(".timeline")
    demo.pause(1.5)
    demo.shot("04-consultar-lote", full=True)

    # 5. Rejected operations
    demo.goto("registrar")
    for index, scenario in enumerate(
        [
            "Carteira sem permissão",
            "Quantidade negativa",
            "Pular etapas (finalizar lote cadastrado)",
            "Alterar lote finalizado",
        ],
        start=1,
    ):
        page.get_by_role("button", name=scenario).click()
        demo.pause(0.8)
        demo.send()
        expect(page, ".outcome.bad", f"{scenario} should be rejected")
        demo.shot(f"05-rejeicao-{index}")
    demo.goto("rejeicoes")
    demo.shot("06-rejeicoes", full=True)

    # 6. Block explorer and Merkle proof
    demo.goto("blockchain")
    page.locator("details.txs summary").first.click()
    demo.shot("07-blockchain")
    page.get_by_role("button", name="Detalhes e prova de Merkle").first.click()
    page.wait_for_selector("#dialog .notice.ok")
    demo.pause(1.5)
    demo.shot("08-prova-merkle")
    page.click("#dialog-close")

    # 7. Permissions
    demo.goto("permissoes")
    demo.wallet("Administrador")
    demo.shot("09-permissoes", full=True)

    # 8. Integrity laboratory
    demo.goto("laboratorio")
    page.get_by_role("button", name="Adulterar dado gravado").click()
    page.wait_for_selector("#view-laboratorio .notice.bad")
    demo.pause(1.5)
    demo.shot("10-adulteracao-detectada")
    demo.goto("blockchain")
    demo.shot("11-blockchain-adulterada")
    demo.goto("laboratorio")
    page.get_by_role("button", name="Restaurar da cópia em disco").click()
    page.wait_for_selector("#view-laboratorio .notice.ok")
    demo.pause(1.5)
    demo.shot("12-cadeia-restaurada")


def is_unexpected(message) -> bool:
    """Ignore the browser log line of expected 4xx answers (rejected operations)."""
    if message.type != "error":
        return False
    return not (
        "Failed to load resource" in message.text and "status of 4" in message.text
    )


def main() -> int:
    """Run the demonstration and store screenshots and video."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    parser.add_argument("--pace", type=int, default=1200, help="pausa base em ms")
    parser.add_argument(
        "--video", type=Path, default=ROOT / "docs" / "video" / "demonstracao.webm"
    )
    args = parser.parse_args()

    SHOTS.mkdir(parents=True, exist_ok=True)
    args.video.parent.mkdir(parents=True, exist_ok=True)
    video_dir = ROOT / "data" / "tmp-video"
    shutil.rmtree(video_dir, ignore_errors=True)
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1280, "height": 800},
            locale="pt-BR",
        )
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda msg: errors.append(msg.text) if is_unexpected(msg) else None,
        )
        run(Demo(page, args.base, args.pace))
        context.close()
        browser.close()
    recorded = next(video_dir.glob("*.webm"))
    shutil.move(str(recorded), args.video)
    shutil.rmtree(video_dir, ignore_errors=True)
    print(f"Vídeo salvo em {args.video}")
    if errors:
        print("Erros de console:", *errors, sep="\n  ")
        return 1
    print("Nenhum erro de console.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
