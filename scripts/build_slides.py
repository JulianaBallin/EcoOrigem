"""Build the eight-slide Delivery 2 deck from the original Canva template."""

# pylint: disable=protected-access,too-many-arguments,too-many-locals,too-many-statements

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

TITLE_FONT = "TOMO Trompa Pro"
BODY_FONT = "Open Sans 2"
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
SAFE_TOP = 0.72
SAFE_BOTTOM = 10.53


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
) -> None:
    """Set horizontal regular-weight text using the original deck fonts."""
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
            run.font.bold = False
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
):
    """Add a horizontal text box."""
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    style_text(shape, text, size, color, align, font_name, margin)
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


def add_title(
    slide,
    title: str,
    subtitle: str,
    width: float = 14.0,
    title_color: str = GREEN_DARK,
    subtitle_color: str = GRAY,
) -> None:
    """Add the shared horizontal title with balanced top spacing."""
    add_text(
        slide,
        0.90,
        SAFE_TOP,
        width,
        0.72,
        title,
        39,
        title_color,
        PP_ALIGN.LEFT,
        TITLE_FONT,
        0.02,
    )
    add_text(
        slide,
        0.94,
        1.48,
        width,
        0.43,
        subtitle,
        15.5,
        subtitle_color,
        PP_ALIGN.LEFT,
        BODY_FONT,
        0.02,
    )


def add_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    accent: str = GREEN,
    title_size: float = 19,
    body_size: float = 14.5,
    center: bool = False,
) -> None:
    """Add a template-style card with a small color marker."""
    add_round_rect(slide, x + 0.05, y + 0.07, w, h, GREEN_DARK, None).fill.transparency = 86
    add_round_rect(slide, x, y, w, h, CREAM, GREEN_LINE, 1.0)
    marker = add_round_rect(slide, x + 0.17, y + 0.19, 0.12, h - 0.38, accent, None)
    marker.adjustments[0] = 0.20
    alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    add_text(slide, x + 0.42, y + 0.16, w - 0.58, 0.48, title, title_size, GREEN_DARK, alignment)
    add_text(slide, x + 0.42, y + 0.70, w - 0.58, h - 0.84, body, body_size, INK, alignment)


def add_pill(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    fill: str,
    color: str,
    size: float,
) -> None:
    """Add a compact rounded label."""
    shape = add_round_rect(slide, x, y, w, h, fill, None)
    shape.adjustments[0] = 0.28
    style_text(shape, text, size, color, PP_ALIGN.CENTER, BODY_FONT, 0.03)


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
        style_text(base, "R", 21, WHITE, PP_ALIGN.CENTER, TITLE_FONT, 0.01)
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
        add_text(slide, x + 0.07, y + 0.18, size - 0.14, 0.28, "IPFS", 10.5, TEAL, PP_ALIGN.CENTER)
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
        screen = add_round_rect(slide, x, y + 0.05, size, size * 0.72, CREAM, GREEN_DARK, 1.4)
        add_round_rect(slide, x + 0.06, y + 0.12, size - 0.12, 0.09, GREEN, None)
        return
    if kind == "person":
        add_circle(slide, x + size * 0.33, y, size * 0.31, GREEN_DARK)
        add_round_rect(slide, x + size * 0.18, y + size * 0.34, size * 0.64, size * 0.50, GREEN_DARK, None)
        return
    if kind == "contract":
        page = add_round_rect(slide, x + 0.06, y, size * 0.76, size, CREAM, GREEN_DARK, 1.4)
        for index in range(3):
            add_round_rect(slide, x + 0.18, y + 0.19 + index * 0.16, size * 0.45, 0.05, GREEN_DARK, None)
        return
    add_circle(slide, x, y, size, GREEN)


def add_tool_card(
    slide,
    x: float,
    y: float,
    title: str,
    body: str,
    icon: str,
    accent: str,
) -> None:
    """Add one technology card."""
    add_round_rect(slide, x + 0.05, y + 0.07, 4.05, 2.45, GREEN_DARK, None).fill.transparency = 87
    add_round_rect(slide, x, y, 4.05, 2.45, CREAM, GREEN_LINE, 1.0)
    add_round_rect(slide, x + 0.20, y + 0.20, 0.88, 0.88, accent, None)
    add_icon(slide, icon, x + 0.31, y + 0.31, 0.65)
    add_text(slide, x + 1.25, y + 0.22, 2.55, 0.45, title, 18, GREEN_DARK)
    add_text(slide, x + 1.25, y + 0.72, 2.55, 1.42, body, 13.2, INK)


def add_flow_node(
    slide,
    x: float,
    y: float,
    title: str,
    subtitle: str,
    icon: str,
    accent: str,
) -> None:
    """Add one node in the complete dApp flow."""
    add_round_rect(slide, x + 0.04, y + 0.06, 2.65, 1.48, GREEN_DARK, None).fill.transparency = 87
    add_round_rect(slide, x, y, 2.65, 1.48, CREAM, GREEN_LINE, 1.0)
    add_round_rect(slide, x + 0.15, y + 0.23, 0.72, 0.72, accent, None)
    add_icon(slide, icon, x + 0.23, y + 0.31, 0.55)
    add_text(slide, x + 0.97, y + 0.22, 1.48, 0.38, title, 16, GREEN_DARK)
    add_text(slide, x + 0.97, y + 0.64, 1.48, 0.55, subtitle, 11.5, INK)


def set_notes(slide, text: str) -> None:
    """Replace speaker notes."""
    slide.notes_slide.notes_text_frame.text = text


def build_context(slide) -> None:
    """Slide 1: context using the map and botanical cover artwork."""
    keep_shapes(slide, set(range(6)))
    add_title(slide, "Contexto", "Problema e objetivo do projeto", 9.1)
    add_card(
        slide,
        9.35,
        2.35,
        9.10,
        2.45,
        "Problema",
        "A cadeia da bioeconomia reúne organizações diferentes. Registros separados dificultam verificar a integridade do histórico e identificar quem executou cada etapa.",
        ORANGE,
        23,
        17,
    )
    add_card(
        slide,
        9.35,
        5.25,
        9.10,
        2.45,
        "Objetivo",
        "Registrar o ciclo do lote em um contrato público. A MetaMask identifica os participantes, o Solidity aplica perfis e estados, e a Sepolia confirma transações e eventos.",
        GREEN,
        23,
        17,
    )
    add_pill(slide, 10.80, 8.20, 6.25, 0.62, "Produtor  →  consumidor", YELLOW, GREEN_DARK, 17)
    add_text(
        slide,
        9.20,
        9.35,
        9.35,
        0.72,
        "Ana Beatriz Maciel Nunes   •   Fernando Luiz da Silva Freire   •   Juliana Ballin Lima",
        13.5,
        GRAY,
        PP_ALIGN.CENTER,
    )
    set_notes(slide, "Apresentar o problema dos registros fragmentados e o objetivo do EcoOrigem. Explicar que a blockchain preserva o registro confirmado, mas não garante a veracidade do dado informado na origem.")


def build_first_delivery(slide) -> None:
    """Slide 2: first delivery inside the original orange card layout."""
    keep_shapes(slide, {0, 1, 2, 3, 4, 6, 7, 8, 9})
    add_title(slide, "Primeira Entrega", "Base didática validada em ambiente local", 15.0, GREEN_DARK, GREEN_DARK)
    add_text(slide, 3.10, 3.53, 13.80, 0.52, "Blockchain local em Python", 25, GREEN_DARK, PP_ALIGN.CENTER)
    add_text(
        slide,
        3.15,
        4.10,
        13.70,
        1.05,
        "Blocos encadeados, prova de trabalho, nonce, SHA-256, raiz de Merkle e carteiras com assinatura digital.",
        17,
        INK,
        PP_ALIGN.CENTER,
    )
    first = [
        (2.82, "Regras de negócio", "Perfis, custódia e ordem obrigatória do produtor ao distribuidor."),
        (8.14, "Aplicação web", "Nó HTTP, interface, Docker e mensagens amigáveis para a demonstração."),
        (13.46, "Qualidade", "268 testes, cenários válidos e inválidos, relatório técnico e evidências."),
    ]
    for x, title, body in first:
        add_text(slide, x, 6.48, 3.80, 0.58, title, 20, GREEN_DARK, PP_ALIGN.CENTER)
        add_text(slide, x, 7.25, 3.80, 2.10, body, 15.5, INK, PP_ALIGN.CENTER)
    add_pill(slide, 6.35, 10.00, 7.30, 0.48, "Resultado: conceito e fluxo comprovados", CREAM, GREEN_DARK, 15)
    set_notes(slide, "Resumir a Primeira Entrega como base conceitual e funcional. Mostrar que o projeto já possuía blockchain, regras, interface, testes e relatório antes da migração para Ethereum.")


def build_second_delivery(slide) -> None:
    """Slide 3: second delivery on the original green background."""
    keep_shapes(slide, {1, 2, 3})
    add_title(slide, "Segunda Entrega", "Melhorias e novas implementações da dApp pública", 15.0, CREAM, CREAM)
    items = [
        ("Contrato Solidity", "Perfis, estados, eventos, erros e taxa pagável.", "contract", PURPLE),
        ("Ethereum Sepolia", "Estado público e transações consultáveis.", "sepolia", YELLOW),
        ("MetaMask", "Conexão, assinatura e confirmação de transações.", "metamask", ORANGE),
        ("Frontend Web3.js", "Leituras, escritas, eventos e erros tratados.", "web3", YELLOW),
        ("Hash e IPFS", "Prova on-chain com arquivo mantido fora da rede.", "ipfs", GREEN),
        ("Vercel e testes", "HTTPS, testes locais, Remix e auditoria de segredos.", "vercel", CREAM),
    ]
    positions = [(0.85, 2.40), (7.25, 2.40), (13.65, 2.40), (0.85, 6.25), (7.25, 6.25), (13.65, 6.25)]
    for (title, body, icon, accent), (x, y) in zip(items, positions):
        add_round_rect(slide, x + 0.05, y + 0.07, 5.45, 2.78, GREEN_DARK, None).fill.transparency = 84
        add_round_rect(slide, x, y, 5.45, 2.78, CREAM, CREAM, 0.8)
        add_round_rect(slide, x + 0.22, y + 0.25, 0.92, 0.92, accent, None)
        add_icon(slide, icon, x + 0.34, y + 0.37, 0.67)
        add_text(slide, x + 1.36, y + 0.27, 3.72, 0.52, title, 20, GREEN_DARK)
        add_text(slide, x + 0.30, y + 1.35, 4.85, 1.05, body, 14.3, INK)
    add_pill(slide, 6.75, 9.78, 6.50, 0.52, "Local  →  Ethereum pública de teste", CREAM, GREEN_DARK, 15)
    set_notes(slide, "Apresentar a evolução para Solidity, Sepolia, MetaMask, Web3.js, IPFS e Vercel. Destacar testes e segurança como parte da implementação, não como etapa posterior.")


def build_technologies(slide) -> None:
    """Slide 4: technologies while preserving the original parrot artwork."""
    keep_shapes(slide, {0})
    parrot = slide.shapes[0]
    parrot.left = Inches(17.15)
    parrot.top = Inches(0.18)
    parrot.width = Inches(2.65)
    parrot.height = Inches(2.30)
    add_title(slide, "IDEs, frameworks e serviços", "Responsabilidade de cada tecnologia no ciclo da dApp", 15.4)
    tools = [
        ("Remix IDE", "Importa, compila, testa e envia o deploy.", "remix", GREEN),
        ("Solidity", "Implementa regras, perfis, estados e eventos.", "solidity", YELLOW),
        ("MetaMask", "Guarda chaves e solicita assinaturas.", "metamask", ORANGE),
        ("Sepolia", "Executa e replica o contrato de teste.", "sepolia", GREEN),
        ("Web3.js 4.x", "Liga o frontend à carteira e à ABI.", "web3", YELLOW),
        ("IPFS", "Mantém documentos fora da blockchain.", "ipfs", GREEN),
        ("Vercel", "Publica o frontend estático por HTTPS.", "vercel", CREAM),
        ("Etherscan", "Confere contrato, blocos, eventos e hashes.", "etherscan", GREEN),
    ]
    positions = [(0.72, 2.65), (5.48, 2.65), (10.24, 2.65), (15.00, 2.65), (0.72, 6.15), (5.48, 6.15), (10.24, 6.15), (15.00, 6.15)]
    for (title, body, icon, accent), (x, y) in zip(tools, positions):
        add_tool_card(slide, x, y, title, body, icon, accent)
    for x in (4.84, 9.60, 14.36):
        add_arrow(slide, x, 3.62, 0.42, 0.25, "right")
        add_arrow(slide, x, 7.12, 0.42, 0.25, "right")
    add_pill(slide, 6.60, 9.76, 6.80, 0.50, "Código  →  assinatura  →  rede  →  evidência", GREEN, CREAM, 14.5)
    set_notes(slide, "Percorrer a primeira linha como ciclo de desenvolvimento e a segunda como ciclo de uso e publicação. Explicar que as chaves permanecem na MetaMask e nunca entram no projeto.")


def build_flow(slide) -> None:
    """Slide 5: full flow beside the original forest artwork."""
    keep_shapes(slide, {0})
    add_title(slide, "Fluxo completo da dApp", "Da ação no navegador até a evidência pública", 10.3)
    nodes = [
        (0.75, 2.30, "Pessoa", "preenche e consulta", "person", GREEN),
        (4.10, 2.30, "Frontend", "Vercel + Web3.js", "browser", YELLOW),
        (7.45, 2.30, "MetaMask", "conecta e assina", "metamask", ORANGE),
        (7.45, 4.85, "Contrato", "valida e grava", "contract", GREEN),
        (4.10, 4.85, "Sepolia", "confirma e replica", "sepolia", YELLOW),
        (0.75, 4.85, "Etherscan", "expõe a evidência", "etherscan", GREEN),
    ]
    for x, y, title, subtitle, icon, accent in nodes:
        add_flow_node(slide, x, y, title, subtitle, icon, accent)
    add_arrow(slide, 3.53, 2.91, 0.40, 0.25, "right")
    add_arrow(slide, 6.88, 2.91, 0.40, 0.25, "right")
    add_arrow(slide, 8.55, 4.02, 0.28, 0.56, "down")
    add_arrow(slide, 6.88, 5.46, 0.40, 0.25, "left")
    add_arrow(slide, 3.53, 5.46, 0.40, 0.25, "left")

    add_line(slide, 8.77, 6.34, 8.77, 7.10, ORANGE, 1.7)
    add_round_rect(slide, 7.48, 7.08, 2.60, 0.78, CREAM, TEAL, 1.2)
    add_icon(slide, "ipfs", 7.67, 7.17, 0.54)
    add_text(slide, 8.38, 7.20, 1.45, 0.36, "arquivo no IPFS", 11.5, GREEN_DARK)

    add_text(slide, 0.82, 8.10, 9.45, 0.42, "Máquina de estados do lote", 18, GREEN_DARK)
    states = ["Cadastrado", "Beneficiado", "Transporte", "Distribuído", "Finalizado"]
    state_x = [0.75, 2.75, 4.75, 6.75, 8.75]
    for index, (state, x) in enumerate(zip(states, state_x)):
        add_pill(slide, x, 8.65, 1.75, 0.66, state, CREAM if index % 2 == 0 else YELLOW, GREEN_DARK, 12.2)
        if index < 4:
            add_arrow(slide, x + 1.78, 8.87, 0.19, 0.20, "right")
    add_text(slide, 0.82, 9.80, 9.25, 0.48, "Operações fora do perfil ou da ordem são recusadas sem alterar o estado.", 13.2, GRAY, PP_ALIGN.CENTER)
    set_notes(slide, "Explicar o fluxo em serpentina: pessoa, frontend, MetaMask, contrato, Sepolia e Etherscan. O IPFS guarda o arquivo; hash e URI ficam no contrato. Finalizar com os cinco estados obrigatórios.")


def build_demo(slide) -> None:
    """Slide 6: live demo list beside the original jungle artwork."""
    keep_shapes(slide, {0})
    add_title(slide, "Demonstração ao vivo", "O que será mostrado e onde", 10.2)
    rows = [
        ("01", "Conectar e autenticar a carteira", "Vercel + MetaMask", GREEN),
        ("02", "Ler totais, perfil e lotes com call", "Frontend", YELLOW),
        ("03", "Cadastrar lote com taxa em SepoliaETH", "Frontend + MetaMask", ORANGE),
        ("04", "Acompanhar hash, bloco e confirmação", "Frontend + Etherscan", TEAL),
        ("05", "Provocar erro de perfil e conferir evento", "Frontend + Etherscan", OLIVE),
    ]
    y = 2.35
    for number, action, place, accent in rows:
        add_round_rect(slide, 0.92, y, 9.05, 1.15, CREAM, GREEN_LINE, 1.0)
        circle = add_circle(slide, 1.15, y + 0.20, 0.74, accent)
        style_text(circle, number, 14, GREEN_DARK, PP_ALIGN.CENTER, BODY_FONT, 0.01)
        add_text(slide, 2.10, y + 0.16, 5.20, 0.74, action, 16, GREEN_DARK)
        add_pill(slide, 7.35, y + 0.27, 2.30, 0.58, place, GREEN, CREAM, 11.5)
        y += 1.47
    add_text(slide, 1.05, 9.90, 8.75, 0.43, "Plano B: vídeo e capturas reais, sem novo deploy durante a apresentação.", 12.5, GRAY, PP_ALIGN.CENTER)
    set_notes(slide, "Executar a demonstração pela URL da Vercel e pelo contrato já implantado. Mostrar leitura, escrita pagável, confirmação, erro compreensível e evento no Etherscan.")


def build_bonus(slide) -> None:
    """Slide 7: report evidence over the original pond scene."""
    keep_shapes(slide, {0})
    add_title(slide, "Bônus: relatório de desenvolvimento", "Evidência técnica da evolução do projeto", 11.5)
    frame = add_round_rect(slide, 0.83, 2.13, 5.35, 7.62, WHITE, GREEN_LINE, 1.2)
    frame.adjustments[0] = 0.04
    slide.shapes.add_picture(
        str(REPORT_IMAGE),
        Inches(1.10),
        Inches(2.40),
        width=Inches(4.81),
        height=Inches(6.81),
    )
    add_card(slide, 6.55, 2.40, 5.20, 1.75, "Relatório técnico", "21 páginas preservadas em PDF e DOCX.", GREEN, 19, 14.5)
    add_card(slide, 6.55, 4.65, 5.20, 1.75, "Conteúdo", "Arquitetura, decisões, testes, segurança e limitações.", ORANGE, 19, 14.5)
    add_card(slide, 6.55, 6.90, 5.20, 1.75, "Valor para a Entrega 2", "Documenta a base que originou a migração para Ethereum.", YELLOW, 19, 14.5)
    add_pill(slide, 1.10, 9.68, 10.65, 0.50, "docs/relatorio/relatorio-desenvolvimento-ecoorigem.pdf", GREEN, CREAM, 13.5)
    set_notes(slide, "Mostrar o print real de uma página do relatório. Explicar que o documento registra a arquitetura, as decisões e os testes da Primeira Entrega, servindo como evidência da evolução.")


def build_thanks(slide) -> None:
    """Slide 8: thanks using the original final botanical composition."""
    keep_shapes(slide, {0, 2, 3, 4, 5, 6, 7})
    add_text(slide, 5.00, 1.08, 10.00, 0.98, "EcoOrigem", 48, CREAM, PP_ALIGN.CENTER, TITLE_FONT)
    add_text(slide, 5.35, 4.48, 9.30, 0.88, "Obrigada", 44, GREEN_DARK, PP_ALIGN.CENTER, TITLE_FONT)
    add_text(slide, 5.35, 5.46, 9.30, 0.52, "Perguntas?", 23, GREEN_DARK, PP_ALIGN.CENTER, TITLE_FONT)
    add_text(slide, 5.15, 6.30, 9.70, 0.56, "Ana Beatriz   •   Fernando Luiz   •   Juliana Ballin", 14.5, GRAY, PP_ALIGN.CENTER)
    add_pill(slide, 6.25, 7.18, 7.50, 0.58, "github.com/JulianaBallin/EcoOrigem", GREEN_DARK, CREAM, 14)
    slide.shapes.add_picture(str(UEA_LOGO), Inches(8.30), Inches(9.16), width=Inches(3.40), height=Inches(1.13))
    set_notes(slide, "Agradecer, manter o repositório visível e abrir espaço para a arguição.")


def validate_deck(prs: Presentation) -> None:
    """Enforce slide count, title order, text weight, rotation and safe margins."""
    expected = [
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
        raise RuntimeError(f"Esperados 8 slides, encontrados {len(prs.slides)}.")

    for slide_number, (slide, title) in enumerate(zip(prs.slides, expected), start=1):
        texts = []
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
                    if run.font.bold is True:
                        raise RuntimeError(
                            f"Negrito encontrado no slide {slide_number}: {run.text!r}"
                        )
        if title not in texts:
            raise RuntimeError(f"Título ausente no slide {slide_number}: {title}")


def build() -> None:
    """Build, validate and export the deck."""
    prs = Presentation(TEMPLATE)
    select_template_slides(prs, [0, 2, 5, 4, 3, 7, 8, 10])
    builders = [
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
