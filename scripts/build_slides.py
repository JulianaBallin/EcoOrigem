"""Build the nine-slide Delivery 2 deck from the original Canva template."""

# pylint: disable=protected-access,too-many-arguments,too-many-locals
# pylint: disable=too-many-statements,too-many-positional-arguments
# pylint: disable=too-many-branches,too-many-return-statements,line-too-long

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SLIDES_DIR = ROOT / "docs" / "slides"
TEMPLATE = SLIDES_DIR / "template-entrega-1.pptx"
OUTPUT = SLIDES_DIR / "apresentacao-ecoorigem.pptx"
PDF = SLIDES_DIR / "apresentacao-ecoorigem.pdf"
UEA_LOGO = ROOT / "docs" / "assets" / "uea.png"
REPORT_IMAGE = ROOT / "docs" / "assets" / "relatorio-arquitetura.png"

TITLE_FONT = "Ubuntu Sans"
BODY_FONT = "Ubuntu Sans"
CREAM = "FFF9ED"
GREEN = "72BF97"
GREEN_DARK = "558176"
GREEN_LINE = "91B7A6"
OLIVE = "96AF40"
ORANGE = "FAB558"
YELLOW = "FFE889"
WHITE = "FFFFFF"
INK = "3C6556"
GRAY = "77968E"
BLACK = "202522"
BLUE = "6E83EA"
TEAL = "31A99B"
PURPLE = "8175D8"
SAFE_TOP = 0.55
SAFE_BOTTOM = 10.65


def rgb(value: str) -> RGBColor:
    """Convert a hexadecimal color to a PowerPoint color."""
    return RGBColor.from_string(value)


def select_template_slides(prs: Presentation, indexes: list[int]) -> None:
    """Keep selected template slides and reorder them without copying artwork."""
    slide_ids = prs.slides._sldIdLst
    original = list(slide_ids)
    selected = [original[index] for index in indexes]

    for slide_id in original:
        slide_ids.remove(slide_id)
        if slide_id not in selected:
            prs.part.drop_rel(slide_id.rId)
    for slide_id in selected:
        slide_ids.append(slide_id)


def keep_shapes(slide, indexes: set[int]) -> None:
    """Remove old content while retaining the original decorative artwork."""
    for index, shape in reversed(list(enumerate(slide.shapes))):
        if index not in indexes:
            slide.shapes._spTree.remove(shape._element)


def iter_shapes(shapes):
    """Yield shapes recursively, including children of groups."""
    for shape in shapes:
        yield shape
        if hasattr(shape, "shapes"):
            yield from iter_shapes(shape.shapes)


def solid(shape, color: str, transparency: int = 0) -> None:
    """Apply a solid fill."""
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(color)
    shape.fill.transparency = transparency


def no_line(shape) -> None:
    """Remove a shape outline."""
    shape.line.fill.background()


def style_text(
    shape,
    text: str,
    size: float,
    color: str = GREEN_DARK,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    font_name: str = BODY_FONT,
    margin: float = 0.08,
    bold: bool = False,
) -> None:
    """Set horizontal text with explicit hierarchy and installed fonts."""
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    for index, line in enumerate(text.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.alignment = align
        paragraph.space_before = Pt(0)
        paragraph.space_after = Pt(0)
        paragraph.line_spacing = 1.0
        for run in paragraph.runs:
            run.font.name = font_name
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.italic = False
            run.font.color.rgb = rgb(color)
    shape.rotation = 0


def add_text(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    size: float,
    color: str = GREEN_DARK,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    font_name: str = BODY_FONT,
    margin: float = 0.08,
    bold: bool = False,
):
    """Add a horizontal text box."""
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    style_text(shape, text, size, color, align, font_name, margin, bold)
    return shape


def add_round_rect(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str = CREAM,
    line: str | None = GREEN_LINE,
    width: float = 1.0,
):
    """Add a rounded rectangle matching the template cards."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x),
        Inches(y),
        Inches(w),
        Inches(h),
    )
    solid(shape, fill)
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(width)
    else:
        no_line(shape)
    shape.rotation = 0
    return shape


def add_oval(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    transparency: int = 0,
):
    """Add an organic oval used as an accent instead of a content card."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(x),
        Inches(y),
        Inches(w),
        Inches(h),
    )
    solid(shape, fill, transparency)
    no_line(shape)
    shape.rotation = 0
    return shape


def add_title(
    slide,
    title: str,
    subtitle: str,
    width: float = 16.5,
    title_color: str = GREEN_DARK,
    subtitle_color: str = ORANGE,
    title_size: float = 47,
) -> None:
    """Add a bold rounded title, a colored subtitle and organic accents."""
    add_oval(slide, 0.72, 0.73, 0.42, 0.42, subtitle_color)
    add_oval(slide, 0.62, 1.13, 0.19, 0.19, title_color)
    add_text(
        slide,
        1.28,
        0.60,
        width,
        0.92,
        title,
        title_size,
        title_color,
        PP_ALIGN.LEFT,
        TITLE_FONT,
        0.02,
        True,
    )
    add_text(
        slide,
        1.31,
        1.55,
        width,
        0.48,
        subtitle,
        19,
        subtitle_color,
        PP_ALIGN.LEFT,
        BODY_FONT,
        0.02,
        False,
    )


def add_circle(slide, x: float, y: float, size: float, fill: str, line: str | None = None):
    """Add a circle."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(size), Inches(size)
    )
    solid(shape, fill)
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1.0)
    else:
        no_line(shape)
    shape.rotation = 0
    return shape


def add_line(
    slide,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = GREEN_DARK,
    width: float = 2.0,
) -> None:
    """Add a straight horizontal or vertical connector."""
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1),
        Inches(y1),
        Inches(x2),
        Inches(y2),
    )
    line.line.color.rgb = rgb(color)
    line.line.width = Pt(width)


def add_arrow(slide, x: float, y: float, w: float, h: float, direction: str) -> None:
    """Add a small arrow between diagram nodes."""
    arrow_type = {
        "right": MSO_SHAPE.RIGHT_ARROW,
        "left": MSO_SHAPE.LEFT_ARROW,
        "down": MSO_SHAPE.DOWN_ARROW,
    }[direction]
    arrow = slide.shapes.add_shape(
        arrow_type, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    solid(arrow, GREEN_DARK)
    no_line(arrow)
    arrow.rotation = 0


def add_icon(slide, kind: str, x: float, y: float, size: float = 0.68) -> None:
    """Draw compact vector icons that fit the original visual language."""
    if kind == "remix":
        base = add_round_rect(slide, x, y, size, size, BLACK, None)
        style_text(base, "R", 21, WHITE, PP_ALIGN.CENTER, TITLE_FONT, 0.01, True)
        return
    if kind in {"solidity", "sepolia"}:
        color = GRAY if kind == "solidity" else BLUE
        diamond = slide.shapes.add_shape(
            MSO_SHAPE.DIAMOND,
            Inches(x + size * 0.18),
            Inches(y),
            Inches(size * 0.64),
            Inches(size),
        )
        solid(diamond, color)
        no_line(diamond)
        diamond.rotation = 0
        return
    if kind == "metamask":
        face = slide.shapes.add_shape(
            MSO_SHAPE.HEXAGON,
            Inches(x + 0.07),
            Inches(y + 0.10),
            Inches(size - 0.14),
            Inches(size - 0.10),
        )
        solid(face, ORANGE)
        no_line(face)
        face.rotation = 0
        for offset in (0.01, size - 0.22):
            ear = slide.shapes.add_shape(
                MSO_SHAPE.ISOSCELES_TRIANGLE,
                Inches(x + offset),
                Inches(y),
                Inches(0.21),
                Inches(0.28),
            )
            solid(ear, ORANGE)
            no_line(ear)
            ear.rotation = 0
        return
    if kind == "web3":
        points = [(x + 0.08, y + 0.40), (x + 0.33, y + 0.09), (x + 0.60, y + 0.40)]
        for start, end in ((0, 1), (1, 2), (0, 2)):
            add_line(slide, *points[start], *points[end], ORANGE, 1.3)
        for px, py in points:
            add_circle(slide, px - 0.07, py - 0.07, 0.17, ORANGE)
        return
    if kind == "ipfs":
        shape = slide.shapes.add_shape(
            MSO_SHAPE.HEXAGON, Inches(x), Inches(y), Inches(size), Inches(size)
        )
        solid(shape, CREAM)
        shape.line.color.rgb = rgb(TEAL)
        shape.line.width = Pt(1.8)
        shape.rotation = 0
        add_text(
            slide,
            x + 0.07,
            y + 0.18,
            size - 0.14,
            0.28,
            "IPFS",
            10.5,
            TEAL,
            PP_ALIGN.CENTER,
            bold=True,
        )
        return
    if kind == "vercel":
        triangle = slide.shapes.add_shape(
            MSO_SHAPE.ISOSCELES_TRIANGLE,
            Inches(x),
            Inches(y + 0.07),
            Inches(size),
            Inches(size * 0.72),
        )
        solid(triangle, BLACK)
        no_line(triangle)
        triangle.rotation = 0
        return
    if kind == "etherscan":
        add_circle(slide, x, y, size, TEAL)
        for index, height in enumerate((0.16, 0.26, 0.37)):
            add_round_rect(
                slide,
                x + 0.15 + index * 0.13,
                y + size - 0.14 - height,
                0.08,
                height,
                WHITE,
                None,
            )
        return
    if kind == "browser":
        add_round_rect(slide, x, y + 0.05, size, size * 0.72, CREAM, GREEN_DARK, 1.4)
        add_round_rect(slide, x + 0.06, y + 0.12, size - 0.12, 0.09, GREEN, None)
        return
    if kind == "person":
        add_circle(slide, x + size * 0.33, y, size * 0.31, GREEN_DARK)
        add_round_rect(slide, x + size * 0.18, y + size * 0.34, size * 0.64, size * 0.50, GREEN_DARK, None)
        return
    if kind == "contract":
        add_round_rect(slide, x + 0.06, y, size * 0.76, size, CREAM, GREEN_DARK, 1.4)
        for index in range(3):
            add_round_rect(slide, x + 0.18, y + 0.19 + index * 0.16, size * 0.45, 0.05, GREEN_DARK, None)
        return
    add_circle(slide, x, y, size, GREEN)


def add_labeled_icon(
    slide,
    x: float,
    y: float,
    title: str,
    body: str,
    icon: str,
    accent: str,
    title_color: str = GREEN_DARK,
    body_color: str = INK,
    width: float = 5.65,
) -> None:
    """Add an icon and open typography without a surrounding content box."""
    add_circle(slide, x, y + 0.05, 1.08, accent)
    add_icon(slide, icon, x + 0.20, y + 0.24, 0.68)
    add_text(slide, x + 1.34, y, width - 1.34, 0.54, title, 22, title_color, bold=True)
    add_text(slide, x + 1.34, y + 0.62, width - 1.34, 1.05, body, 17, body_color)


def add_technology(
    slide,
    x: float,
    y: float,
    title: str,
    body: str,
    icon: str,
    accent: str,
) -> None:
    """Add one circular technology node with labels below it."""
    add_circle(slide, x + 1.34, y, 1.18, accent)
    add_icon(slide, icon, x + 1.57, y + 0.23, 0.72)
    add_text(slide, x, y + 1.35, 3.85, 0.46, title, 21, GREEN_DARK, PP_ALIGN.CENTER, bold=True)
    add_text(slide, x + 0.10, y + 1.88, 3.65, 0.83, body, 15.5, INK, PP_ALIGN.CENTER)


def add_flow_node(
    slide,
    x: float,
    y: float,
    title: str,
    subtitle: str,
    icon: str,
    accent: str,
) -> None:
    """Add one circular step in the complete dApp flow."""
    add_circle(slide, x + 0.67, y, 1.02, accent)
    add_icon(slide, icon, x + 0.86, y + 0.19, 0.64)
    add_text(slide, x, y + 1.16, 2.36, 0.42, title, 18.5, GREEN_DARK, PP_ALIGN.CENTER, bold=True)
    add_text(slide, x, y + 1.62, 2.36, 0.54, subtitle, 14.5, INK, PP_ALIGN.CENTER)


def set_notes(slide, text: str) -> None:
    """Replace speaker notes."""
    slide.notes_slide.notes_text_frame.text = text


def build_cover(slide) -> None:
    """Slide 1: separate cover with project, students and course only."""
    keep_shapes(slide, set(range(5)))
    add_text(
        slide,
        4.35,
        3.08,
        11.30,
        1.35,
        "EcoOrigem",
        78,
        CREAM,
        PP_ALIGN.CENTER,
        TITLE_FONT,
        0.02,
        True,
    )
    add_text(
        slide,
        4.55,
        4.75,
        10.90,
        0.62,
        "Oficina de Desenvolvimento de Sistemas III",
        25,
        YELLOW,
        PP_ALIGN.CENTER,
        BODY_FONT,
        0.02,
        True,
    )
    add_text(
        slide,
        4.45,
        6.20,
        11.10,
        1.35,
        "Ana Beatriz Maciel Nunes\nFernando Luiz da Silva Freire\nJuliana Ballin Lima",
        22,
        CREAM,
        PP_ALIGN.CENTER,
    )
    set_notes(slide, "Apresentar o nome do projeto, a disciplina e os integrantes da equipe.")


def build_context(slide) -> None:
    """Slide 2: context using the map and botanical artwork."""
    keep_shapes(slide, set(range(6)))
    add_title(slide, "Contexto", "Problema e objetivo do projeto", 8.1)

    add_circle(slide, 9.55, 2.58, 0.62, ORANGE)
    add_text(slide, 10.48, 2.40, 7.95, 0.58, "O problema", 28, GREEN_DARK, bold=True)
    add_text(
        slide,
        10.48,
        3.08,
        7.85,
        1.68,
        "Registros separados dificultam verificar a integridade do histórico e identificar quem executou cada etapa da cadeia da bioeconomia.",
        20,
        INK,
    )

    add_circle(slide, 9.55, 5.65, 0.62, GREEN)
    add_text(slide, 10.48, 5.47, 7.95, 0.58, "O objetivo", 28, GREEN_DARK, bold=True)
    add_text(
        slide,
        10.48,
        6.15,
        7.85,
        2.05,
        "Registrar o ciclo do lote em um contrato público. A MetaMask identifica os participantes, o Solidity aplica perfis e estados, e a Sepolia confirma transações e eventos.",
        20,
        INK,
    )
    add_text(
        slide,
        10.48,
        8.72,
        7.55,
        0.62,
        "Produtor  →  consumidor",
        21,
        ORANGE,
        bold=True,
    )
    set_notes(slide, "Apresentar o problema dos registros fragmentados e o objetivo do EcoOrigem. Explicar que a blockchain preserva o registro confirmado, mas não garante a veracidade do dado informado na origem.")


def build_first_delivery(slide) -> None:
    """Slide 3: first delivery inside the original organic composition."""
    keep_shapes(slide, {0, 1, 2, 3, 4, 7})
    add_title(
        slide,
        "Primeira Entrega",
        "Base didática validada em ambiente local",
        15.0,
        GREEN_DARK,
        CREAM,
        46,
    )
    add_text(
        slide,
        3.10,
        3.38,
        13.80,
        0.60,
        "Blockchain local em Python",
        30,
        GREEN_DARK,
        PP_ALIGN.CENTER,
        bold=True,
    )
    add_text(
        slide,
        3.15,
        4.10,
        13.70,
        1.10,
        "Blocos encadeados, prova de trabalho, nonce, SHA-256, raiz de Merkle e carteiras com assinatura digital.",
        19,
        INK,
        PP_ALIGN.CENTER,
    )
    first = [
        (2.78, "Regras de negócio", "Perfis, custódia e ordem obrigatória do produtor ao distribuidor.", "contract", PURPLE),
        (8.10, "Aplicação web", "Nó HTTP, interface, Docker e mensagens amigáveis para a demonstração.", "browser", YELLOW),
        (13.42, "Qualidade", "268 testes, cenários válidos e inválidos, relatório técnico e evidências.", "etherscan", GREEN),
    ]
    for x, title, body, icon, accent in first:
        add_circle(slide, x + 1.43, 6.02, 0.98, accent)
        add_icon(slide, icon, x + 1.62, 6.21, 0.60)
        add_text(slide, x, 7.14, 3.84, 0.60, title, 22, GREEN_DARK, PP_ALIGN.CENTER, bold=True)
        add_text(slide, x, 7.90, 3.84, 1.46, body, 17.5, INK, PP_ALIGN.CENTER)
    add_text(
        slide,
        5.40,
        9.93,
        9.20,
        0.55,
        "Resultado: conceito e fluxo comprovados",
        18,
        GREEN_DARK,
        PP_ALIGN.CENTER,
        bold=True,
    )
    set_notes(slide, "Resumir a Primeira Entrega como base conceitual e funcional. Mostrar que o projeto já possuía blockchain, regras, interface, testes e relatório antes da migração para Ethereum.")


def build_second_delivery(slide) -> None:
    """Slide 4: second delivery on the original green background."""
    keep_shapes(slide, {1, 2, 3})
    add_title(
        slide,
        "Segunda Entrega",
        "Melhorias e novas implementações da dApp pública",
        15.0,
        CREAM,
        YELLOW,
        46,
    )
    items = [
        ("Contrato Solidity", "Perfis, estados, eventos, erros e taxa pagável.", "contract", PURPLE),
        ("Ethereum Sepolia", "Estado público e transações consultáveis.", "sepolia", YELLOW),
        ("MetaMask", "Conexão, assinatura e confirmação de transações.", "metamask", ORANGE),
        ("Frontend Web3.js", "Leituras, escritas, eventos e erros tratados.", "web3", YELLOW),
        ("Hash e IPFS", "Prova on-chain com arquivo mantido fora da rede.", "ipfs", GREEN),
        ("Vercel e testes", "HTTPS, Remix, testes locais e auditoria de segredos.", "vercel", CREAM),
    ]
    positions = [
        (0.72, 2.55),
        (7.15, 2.55),
        (13.58, 2.55),
        (0.72, 6.15),
        (7.15, 6.15),
        (13.58, 6.15),
    ]
    for (title, body, icon, accent), (x, y) in zip(items, positions):
        add_labeled_icon(slide, x, y, title, body, icon, accent, CREAM, CREAM)
    add_text(
        slide,
        5.45,
        9.72,
        9.10,
        0.54,
        "Do ambiente local para uma rede Ethereum pública de teste",
        18,
        YELLOW,
        PP_ALIGN.CENTER,
        bold=True,
    )
    set_notes(slide, "Apresentar a evolução para Solidity, Sepolia, MetaMask, Web3.js, IPFS e Vercel. Destacar testes e segurança como parte da implementação, não como etapa posterior.")


def build_technologies(slide) -> None:
    """Slide 5: connected technology diagram with the original parrots."""
    keep_shapes(slide, {0})
    parrots = slide.shapes[0]
    parrots.left = Inches(17.50)
    parrots.top = Inches(0.10)
    parrots.width = Inches(2.20)
    parrots.height = Inches(2.18)
    add_title(
        slide,
        "IDEs, frameworks e serviços",
        "Como cada tecnologia participa do ciclo da dApp",
        15.8,
        title_size=44,
    )
    tools = [
        ("Remix IDE", "Compila, testa e faz o deploy.", "remix", GREEN),
        ("Solidity", "Define regras, perfis e eventos.", "solidity", YELLOW),
        ("MetaMask", "Mantém chaves e assina ações.", "metamask", ORANGE),
        ("Sepolia", "Executa o contrato de teste.", "sepolia", GREEN),
        ("Web3.js 4.x", "Conecta o frontend à ABI.", "web3", YELLOW),
        ("IPFS", "Armazena documentos off-chain.", "ipfs", GREEN),
        ("Vercel", "Publica o frontend com HTTPS.", "vercel", CREAM),
        ("Etherscan", "Confere blocos, eventos e hashes.", "etherscan", GREEN),
    ]
    positions = [
        (0.10, 2.72),
        (5.00, 2.72),
        (9.90, 2.72),
        (14.80, 2.72),
        (0.10, 6.38),
        (5.00, 6.38),
        (9.90, 6.38),
        (14.80, 6.38),
    ]
    for y in (3.31, 6.97):
        add_line(slide, 2.62, y, 6.34, y, GREEN_LINE, 2.2)
        add_line(slide, 7.52, y, 11.24, y, GREEN_LINE, 2.2)
        add_line(slide, 12.42, y, 16.14, y, GREEN_LINE, 2.2)
    for (title, body, icon, accent), (x, y) in zip(tools, positions):
        add_technology(slide, x, y, title, body, icon, accent)
    set_notes(slide, "Percorrer a primeira linha como ciclo de desenvolvimento e a segunda como ciclo de integração e publicação. Explicar que as chaves permanecem na MetaMask e nunca entram no projeto.")


def build_flow(slide) -> None:
    """Slide 6: full flow beside the original forest artwork."""
    keep_shapes(slide, {0})
    add_title(slide, "Fluxo completo da dApp", "Da ação no navegador à evidência pública", 10.0, title_size=44)
    nodes = [
        (0.42, 2.35, "Pessoa", "preenche e consulta", "person", GREEN),
        (3.47, 2.35, "Frontend", "Vercel + Web3.js", "browser", YELLOW),
        (6.52, 2.35, "MetaMask", "conecta e assina", "metamask", ORANGE),
        (6.52, 4.78, "Contrato", "valida e grava", "contract", GREEN),
        (3.47, 4.78, "Sepolia", "confirma e replica", "sepolia", YELLOW),
        (0.42, 4.78, "Etherscan", "expõe a evidência", "etherscan", GREEN),
    ]
    for x, y, title, subtitle, icon, accent in nodes:
        add_flow_node(slide, x, y, title, subtitle, icon, accent)
    add_arrow(slide, 2.84, 2.73, 0.38, 0.24, "right")
    add_arrow(slide, 5.89, 2.73, 0.38, 0.24, "right")
    add_arrow(slide, 7.53, 4.05, 0.28, 0.46, "down")
    add_arrow(slide, 5.89, 5.16, 0.38, 0.24, "left")
    add_arrow(slide, 2.84, 5.16, 0.38, 0.24, "left")

    add_circle(slide, 8.78, 4.90, 0.92, CREAM, TEAL)
    add_icon(slide, "ipfs", 8.94, 5.06, 0.60)
    add_text(slide, 8.15, 5.96, 2.15, 0.72, "arquivo no IPFS", 15.5, TEAL, PP_ALIGN.CENTER, bold=True)
    add_line(slide, 8.18, 5.24, 8.72, 5.24, TEAL, 1.7)

    add_text(slide, 0.68, 7.42, 9.62, 0.46, "Máquina de estados do lote", 21, GREEN_DARK, bold=True)
    states = ["Cadastrado", "Beneficiado", "Transporte", "Distribuído", "Finalizado"]
    state_x = [0.76, 2.66, 4.56, 6.46, 8.36]
    for index, (state, x) in enumerate(zip(states, state_x)):
        add_circle(slide, x, 8.30, 0.62, CREAM if index % 2 == 0 else YELLOW, GREEN_LINE)
        add_text(slide, x - 0.62, 9.04, 1.85, 0.40, state, 13, GREEN_DARK, PP_ALIGN.CENTER, bold=True)
        if index < 4:
            add_line(slide, x + 0.64, 8.61, x + 1.86, 8.61, GREEN_LINE, 1.7)
    add_text(
        slide,
        0.70,
        9.80,
        9.55,
        0.66,
        "Operações fora do perfil ou da ordem são recusadas sem alterar o estado.",
        15,
        GRAY,
        PP_ALIGN.CENTER,
    )
    set_notes(slide, "Explicar o fluxo em serpentina: pessoa, frontend, MetaMask, contrato, Sepolia e Etherscan. O IPFS guarda o arquivo; hash e URI ficam no contrato. Finalizar com os cinco estados obrigatórios.")


def build_demo(slide) -> None:
    """Slide 7: live demo list beside the original jungle artwork."""
    keep_shapes(slide, {0})
    add_title(slide, "Demonstração ao vivo", "O que será mostrado e onde", 10.0, title_size=44)
    rows = [
        ("01", "Conectar e autenticar a carteira", "Vercel + MetaMask", GREEN),
        ("02", "Ler totais, perfil e lotes com call", "Frontend", YELLOW),
        ("03", "Cadastrar lote com taxa em SepoliaETH", "Frontend + MetaMask", ORANGE),
        ("04", "Acompanhar hash, bloco e confirmação", "Frontend + Etherscan", TEAL),
        ("05", "Provocar erro de perfil e conferir evento", "Frontend + Etherscan", OLIVE),
    ]
    y = 2.35
    for number, action, place, accent in rows:
        circle = add_circle(slide, 0.92, y + 0.06, 0.82, accent)
        style_text(circle, number, 15, GREEN_DARK, PP_ALIGN.CENTER, BODY_FONT, 0.01, True)
        add_text(slide, 2.02, y, 7.82, 0.58, action, 20, GREEN_DARK, bold=True)
        add_text(slide, 2.04, y + 0.60, 6.90, 0.40, place, 16, ORANGE, bold=True)
        y += 1.46
    add_text(
        slide,
        1.00,
        9.82,
        8.92,
        0.58,
        "Plano B: vídeo e capturas reais, sem novo deploy durante a apresentação.",
        15,
        GRAY,
        PP_ALIGN.CENTER,
    )
    set_notes(slide, "Executar a demonstração pela URL da Vercel e pelo contrato já implantado. Mostrar leitura, escrita pagável, confirmação, erro compreensível e evento no Etherscan.")


def build_bonus(slide) -> None:
    """Slide 8: report evidence over the original pond scene."""
    keep_shapes(slide, {0})
    artwork = slide.shapes[0]
    artwork.left = Inches(11.50)
    artwork.top = Inches(0)
    add_title(
        slide,
        "Bônus: relatório de desenvolvimento",
        "Evidência técnica da evolução do projeto",
        11.8,
        title_size=40,
    )
    add_oval(slide, 0.48, 2.18, 5.88, 7.50, GREEN, 58)
    slide.shapes.add_picture(
        str(REPORT_IMAGE),
        Inches(0.92),
        Inches(2.42),
        width=Inches(4.92),
        height=Inches(6.96),
    )
    callouts = [
        (2.67, GREEN, "Relatório técnico", "21 páginas preservadas em PDF e DOCX."),
        (5.10, ORANGE, "Conteúdo", "Arquitetura, decisões, testes, segurança e limitações."),
        (7.53, YELLOW, "Valor para a Entrega 2", "Documenta a base que originou a migração para Ethereum."),
    ]
    for y, accent, title, body in callouts:
        add_circle(slide, 6.38, y, 0.76, accent)
        add_text(slide, 7.42, y - 0.08, 4.18, 0.50, title, 22, GREEN_DARK, bold=True)
        add_text(slide, 7.42, y + 0.53, 4.18, 1.04, body, 17, INK)
    add_text(
        slide,
        0.75,
        9.83,
        10.85,
        0.50,
        "docs/relatorio/relatorio-desenvolvimento-ecoorigem.pdf",
        15,
        GREEN_DARK,
        PP_ALIGN.CENTER,
        bold=True,
    )
    set_notes(slide, "Mostrar o print real de uma página do relatório. Explicar que o documento registra a arquitetura, as decisões e os testes da Primeira Entrega, servindo como evidência da evolução.")


def build_thanks(slide) -> None:
    """Slide 9: thanks using the original final botanical composition."""
    keep_shapes(slide, {2, 3, 4, 5, 6, 7})
    add_text(slide, 4.70, 2.25, 10.60, 0.60, "EcoOrigem", 29, YELLOW, PP_ALIGN.CENTER, TITLE_FONT, bold=True)
    add_text(
        slide,
        4.45,
        3.43,
        11.10,
        1.25,
        "Obrigada",
        72,
        CREAM,
        PP_ALIGN.CENTER,
        TITLE_FONT,
        0.02,
        True,
    )
    add_text(slide, 5.00, 5.05, 10.00, 0.65, "Perguntas?", 30, CREAM, PP_ALIGN.CENTER, TITLE_FONT, bold=True)
    add_text(
        slide,
        5.05,
        6.32,
        9.90,
        0.52,
        "github.com/JulianaBallin/EcoOrigem",
        18,
        YELLOW,
        PP_ALIGN.CENTER,
        bold=True,
    )
    slide.shapes.add_picture(str(UEA_LOGO), Inches(8.30), Inches(8.90), width=Inches(3.40), height=Inches(1.13))
    set_notes(slide, "Agradecer, manter o repositório visível e abrir espaço para a arguição.")


def validate_deck(prs: Presentation) -> None:
    """Enforce slide count, title order, hierarchy, rotation and safe margins."""
    expected = [
        "EcoOrigem",
        "Contexto",
        "Primeira Entrega",
        "Segunda Entrega",
        "IDEs, frameworks e serviços",
        "Fluxo completo da dApp",
        "Demonstração ao vivo",
        "Bônus: relatório de desenvolvimento",
        "Obrigada",
    ]
    if len(prs.slides) != len(expected):
        raise RuntimeError(f"Esperados 9 slides, encontrados {len(prs.slides)}.")

    for slide_number, (slide, title) in enumerate(zip(prs.slides, expected), start=1):
        texts = []
        title_is_bold = False
        for shape in iter_shapes(slide.shapes):
            if not getattr(shape, "has_text_frame", False):
                continue
            text = shape.text.strip()
            if text:
                texts.append(text)
                if shape.rotation not in (0, None):
                    raise RuntimeError(f"Texto rotacionado no slide {slide_number}: {text!r}")
                top = shape.top / 914400
                bottom = (shape.top + shape.height) / 914400
                if top < SAFE_TOP - 0.03 or bottom > SAFE_BOTTOM + 0.03:
                    raise RuntimeError(
                        f"Texto fora da margem vertical no slide {slide_number}: {text!r}"
                    )
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if text == title and run.font.bold is True:
                        title_is_bold = True
        if title not in texts:
            raise RuntimeError(f"Título ausente no slide {slide_number}: {title}")
        if not title_is_bold:
            raise RuntimeError(f"Título sem peso forte no slide {slide_number}: {title}")


def build() -> None:
    """Build, validate and export the deck."""
    prs = Presentation(TEMPLATE)
    select_template_slides(prs, [1, 0, 2, 5, 4, 3, 7, 8, 10])
    builders = [
        build_cover,
        build_context,
        build_first_delivery,
        build_second_delivery,
        build_technologies,
        build_flow,
        build_demo,
        build_bonus,
        build_thanks,
    ]
    for slide, builder in zip(prs.slides, builders):
        builder(slide)

    validate_deck(prs)
    prs.core_properties.title = "EcoOrigem - Entrega 2"
    prs.core_properties.subject = "dApp Ethereum Sepolia"
    prs.save(OUTPUT)

    with tempfile.TemporaryDirectory(prefix="ecoorigem-slides-", dir="/tmp") as profile:
        environment = os.environ.copy()
        environment["XDG_CONFIG_HOME"] = str(Path(profile) / "config")
        environment["XDG_CACHE_HOME"] = str(Path(profile) / "cache")
        environment["XDG_RUNTIME_DIR"] = str(Path(profile) / "runtime")
        Path(environment["XDG_RUNTIME_DIR"]).mkdir(parents=True, mode=0o700)
        subprocess.run(
            [
                "libreoffice",
                f"-env:UserInstallation=file://{profile}/office",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(SLIDES_DIR),
                str(OUTPUT),
            ],
            check=True,
            cwd=ROOT,
            env=environment,
        )
    if not PDF.exists():
        raise RuntimeError("O PDF da apresentação não foi gerado.")
    print(f"Apresentação gerada: {OUTPUT}")
    print(f"PDF gerado: {PDF}")


if __name__ == "__main__":
    build()
