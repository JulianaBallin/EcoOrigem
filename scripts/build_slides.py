"""Gera a apresentação da Entrega 2 com oito slides horizontais."""

# pylint: disable=protected-access,too-many-arguments,too-many-locals,too-many-statements

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "docs" / "slides"
TEMPLATE = SLIDES / "template-entrega-1.pptx"
OUTPUT = SLIDES / "apresentacao-ecoorigem.pptx"
PDF = SLIDES / "apresentacao-ecoorigem.pdf"
UEA_LOGO = ROOT / "docs" / "assets" / "uea.png"
REPORT_IMAGE = ROOT / "docs" / "assets" / "relatorio-arquitetura.png"

FONT = "Ubuntu"
CREAM = "FFF8E8"
PAPER = "FFFDF7"
GREEN = "104B38"
GREEN_DARK = "073E2D"
GREEN_SOFT = "CFE8D8"
MINT = "69C7A5"
TEAL = "2F9F91"
ORANGE = "F2A24A"
ORANGE_SOFT = "FADBAF"
YELLOW = "F4DF84"
LIME = "9AB33D"
BLUE = "697FEA"
PURPLE = "7C72D8"
BLACK = "202522"
GRAY = "5B665F"
LIGHT_GRAY = "E8E9E3"
WHITE = "FFFFFF"
RED = "C85A4A"


def rgb(value: str) -> RGBColor:
    """Converte hexadecimal em RGBColor."""
    return RGBColor.from_string(value)


def remove_all_slides(prs: Presentation) -> None:
    """Remove o conteúdo do modelo e mantém tamanho e tema."""
    slide_ids = prs.slides._sldIdLst
    for slide_id in list(slide_ids):
        prs.part.drop_rel(slide_id.rId)
        slide_ids.remove(slide_id)


def solid(shape, color: str, transparency: int = 0) -> None:
    """Aplica preenchimento sólido."""
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(color)
    shape.fill.transparency = transparency


def no_line(shape) -> None:
    """Remove o contorno de uma forma."""
    shape.line.fill.background()


def set_text(
    shape,
    text: str,
    size: float,
    color: str = BLACK,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    font: str = FONT,
    margin: float = 0.12,
) -> None:
    """Configura texto horizontal sem negrito."""
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    lines = text.split("\n")
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.alignment = align
        paragraph.space_before = Pt(0)
        paragraph.space_after = Pt(0)
        paragraph.line_spacing = 1.0
        for run in paragraph.runs:
            run.font.name = font
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
    color: str = BLACK,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    font: str = FONT,
    margin: float = 0.08,
):
    """Adiciona caixa de texto."""
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    set_text(shape, text, size, color, align, font, margin)
    return shape


def add_round_rect(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    radius_shape=MSO_SHAPE.ROUNDED_RECTANGLE,
    line: str | None = None,
    line_width: float = 1.0,
):
    """Adiciona retângulo arredondado."""
    shape = slide.shapes.add_shape(
        radius_shape, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    solid(shape, fill)
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(line_width)
    else:
        no_line(shape)
    shape.rotation = 0
    return shape


def add_shadow(slide, x: float, y: float, w: float, h: float) -> None:
    """Adiciona profundidade suave sob um cartão."""
    add_round_rect(slide, x + 0.08, y + 0.10, w, h, GREEN_DARK, line=None).fill.transparency = 88


def add_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    accent: str = MINT,
    body_size: float = 17,
    title_size: float = 22,
    center: bool = False,
) -> None:
    """Adiciona cartão com faixa e tipografia regular."""
    add_shadow(slide, x, y, w, h)
    card = add_round_rect(slide, x, y, w, h, PAPER, line=GREEN_SOFT, line_width=1.2)
    card.adjustments[0] = 0.10
    add_round_rect(slide, x + 0.20, y + 0.20, 0.16, h - 0.40, accent)
    alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    add_text(slide, x + 0.52, y + 0.18, w - 0.72, 0.52, title, title_size, GREEN_DARK, alignment)
    add_text(slide, x + 0.52, y + 0.75, w - 0.72, h - 0.93, body, body_size, GRAY, alignment)


def add_background(slide, slide_number: int) -> None:
    """Cria o fundo e os detalhes orgânicos comuns."""
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = rgb(CREAM)

    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(17.8), Inches(-0.7), Inches(3.0), Inches(3.0))
    solid(circle, YELLOW, 12)
    no_line(circle)
    circle.rotation = 0

    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(-1.1), Inches(9.2), Inches(2.5), Inches(2.5))
    solid(circle, GREEN_SOFT, 8)
    no_line(circle)
    circle.rotation = 0

    pill = add_round_rect(slide, 18.45, 10.40, 0.75, 0.38, GREEN_DARK)
    set_text(pill, f"{slide_number:02d}", 13, WHITE, PP_ALIGN.CENTER, margin=0.01)


def add_title(slide, title: str, subtitle: str | None = None) -> None:
    """Adiciona título principal arredondado."""
    width = min(12.8, max(6.3, 2.35 + len(title) * 0.30))
    title_shape = add_round_rect(slide, 0.75, 0.48, width, 0.92, GREEN_DARK)
    title_shape.adjustments[0] = 0.32
    set_text(title_shape, title, 34, WHITE, PP_ALIGN.LEFT, margin=0.18)
    if subtitle:
        add_text(slide, 0.92, 1.48, 17.7, 0.48, subtitle, 16.5, GRAY)


def add_small_pill(
    slide,
    x: float,
    y: float,
    w: float,
    text: str,
    fill: str,
    color: str = GREEN_DARK,
    size: float = 14,
) -> None:
    """Adiciona marcador arredondado."""
    shape = add_round_rect(slide, x, y, w, 0.42, fill)
    shape.adjustments[0] = 0.35
    set_text(shape, text, size, color, PP_ALIGN.CENTER, margin=0.02)


def add_connector(
    slide,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = TEAL,
    width: float = 2.2,
    arrow: bool = True,
    dashed: bool = False,
) -> None:
    """Desenha conexão visual entre componentes."""
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    line.line.color.rgb = rgb(color)
    line.line.width = Pt(width)
    if arrow:
        line.line.end_arrowhead = True
    if dashed:
        line.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    line.rotation = 0


def add_circle(slide, x: float, y: float, diameter: float, fill: str, line: str | None = None):
    """Adiciona círculo."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(diameter), Inches(diameter)
    )
    solid(shape, fill)
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1.2)
    else:
        no_line(shape)
    shape.rotation = 0
    return shape


def add_icon(slide, kind: str, x: float, y: float, size: float = 0.72) -> None:
    """Desenha ícones vetoriais simples sem imagens externas."""
    if kind == "remix":
        base = add_round_rect(slide, x, y, size, size, BLACK)
        set_text(base, "R", 26, WHITE, PP_ALIGN.CENTER, margin=0.01)
        return

    if kind in {"solidity", "sepolia"}:
        color = GRAY if kind == "solidity" else BLUE
        diamond = slide.shapes.add_shape(
            MSO_SHAPE.DIAMOND, Inches(x + size * 0.18), Inches(y), Inches(size * 0.64), Inches(size)
        )
        solid(diamond, color)
        no_line(diamond)
        diamond.rotation = 0
        line = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT,
            Inches(x + size * 0.20), Inches(y + size * 0.53),
            Inches(x + size * 0.80), Inches(y + size * 0.53),
        )
        line.line.color.rgb = rgb(WHITE)
        line.line.width = Pt(1.0)
        return

    if kind == "metamask":
        face = slide.shapes.add_shape(
            MSO_SHAPE.HEXAGON, Inches(x + 0.08), Inches(y + 0.12), Inches(size - 0.16), Inches(size - 0.12)
        )
        solid(face, ORANGE)
        no_line(face)
        face.rotation = 0
        for offset in (0.02, size - 0.25):
            ear = slide.shapes.add_shape(
                MSO_SHAPE.ISOSCELES_TRIANGLE,
                Inches(x + offset), Inches(y), Inches(0.23), Inches(0.30),
            )
            solid(ear, ORANGE)
            no_line(ear)
            ear.rotation = 0
        return

    if kind == "web3":
        points = [(x + 0.08, y + 0.40), (x + 0.34, y + 0.10), (x + 0.61, y + 0.42)]
        add_connector(slide, points[0][0], points[0][1], points[1][0], points[1][1], ORANGE, 1.5, False)
        add_connector(slide, points[1][0], points[1][1], points[2][0], points[2][1], ORANGE, 1.5, False)
        add_connector(slide, points[0][0], points[0][1], points[2][0], points[2][1], ORANGE, 1.5, False)
        for px, py in points:
            add_circle(slide, px - 0.07, py - 0.07, 0.18, ORANGE)
        return

    if kind == "ipfs":
        shape = slide.shapes.add_shape(
            MSO_SHAPE.HEXAGON, Inches(x), Inches(y), Inches(size), Inches(size)
        )
        solid(shape, WHITE)
        shape.line.color.rgb = rgb(TEAL)
        shape.line.width = Pt(2.2)
        shape.rotation = 0
        add_text(slide, x + 0.08, y + 0.17, size - 0.16, 0.32, "IPFS", 12, TEAL, PP_ALIGN.CENTER)
        return

    if kind == "vercel":
        shape = slide.shapes.add_shape(
            MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(x), Inches(y + 0.08), Inches(size), Inches(size * 0.72)
        )
        solid(shape, BLACK)
        no_line(shape)
        shape.rotation = 0
        return

    if kind == "etherscan":
        add_circle(slide, x, y, size, TEAL)
        for index, height in enumerate((0.18, 0.28, 0.40)):
            bar = add_round_rect(
                slide,
                x + 0.16 + index * 0.14,
                y + size - 0.15 - height,
                0.09,
                height,
                WHITE,
            )
            bar.adjustments[0] = 0.10
        return

    if kind == "frontend":
        screen = add_round_rect(slide, x, y + 0.06, size, size * 0.70, WHITE, line=GREEN_DARK, line_width=1.6)
        add_round_rect(slide, x + 0.06, y + 0.13, size - 0.12, 0.10, GREEN_SOFT)
        for index in range(3):
            add_circle(slide, x + 0.10 + index * 0.11, y + 0.15, 0.05, GREEN_DARK)
        return

    if kind == "person":
        add_circle(slide, x + size * 0.32, y, size * 0.34, GREEN_DARK)
        body = add_round_rect(slide, x + size * 0.16, y + size * 0.36, size * 0.68, size * 0.52, GREEN_DARK)
        body.adjustments[0] = 0.28
        return

    if kind == "contract":
        page = add_round_rect(slide, x + 0.05, y, size * 0.78, size, WHITE, line=GREEN_DARK, line_width=1.5)
        for index in range(3):
            add_round_rect(slide, x + 0.18, y + 0.20 + index * 0.17, size * 0.48, 0.06, GREEN_DARK)
        return

    add_circle(slide, x, y, size, MINT)


def add_tool_card(
    slide,
    x: float,
    y: float,
    name: str,
    purpose: str,
    icon: str,
    accent: str,
) -> None:
    """Adiciona tecnologia com ícone e objetivo."""
    add_shadow(slide, x, y, 4.18, 2.28)
    add_round_rect(slide, x, y, 4.18, 2.28, PAPER, line=GREEN_SOFT, line_width=1.1)
    add_round_rect(slide, x + 0.22, y + 0.24, 0.95, 0.95, accent)
    add_icon(slide, icon, x + 0.34, y + 0.35, 0.70)
    add_text(slide, x + 1.35, y + 0.27, 2.55, 0.52, name, 21, GREEN_DARK)
    add_text(slide, x + 1.35, y + 0.82, 2.52, 1.18, purpose, 14.2, GRAY)


def add_flow_node(
    slide,
    x: float,
    y: float,
    w: float,
    title: str,
    subtitle: str,
    icon: str,
    accent: str,
) -> None:
    """Adiciona etapa do fluxo completo."""
    add_shadow(slide, x, y, w, 2.12)
    add_round_rect(slide, x, y, w, 2.12, PAPER, line=GREEN_SOFT, line_width=1.0)
    add_round_rect(slide, x + (w - 0.88) / 2, y + 0.22, 0.88, 0.88, accent)
    add_icon(slide, icon, x + (w - 0.62) / 2, y + 0.35, 0.62)
    add_text(slide, x + 0.12, y + 1.17, w - 0.24, 0.38, title, 17.5, GREEN_DARK, PP_ALIGN.CENTER)
    add_text(slide, x + 0.12, y + 1.54, w - 0.24, 0.40, subtitle, 12.5, GRAY, PP_ALIGN.CENTER)


def set_notes(slide, text: str) -> None:
    """Grava as notas de fala."""
    slide.notes_slide.notes_text_frame.text = text


def build_context(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 1)
    add_title(slide, "Contexto", "Problema real, objetivo e atores da rastreabilidade")

    add_text(slide, 0.92, 2.18, 8.2, 1.08, "EcoOrigem", 48, GREEN_DARK)
    add_small_pill(slide, 0.95, 3.22, 3.30, "Bioeconomia amazônica", YELLOW, GREEN_DARK, 15)

    add_card(
        slide, 0.90, 4.05, 8.25, 2.25,
        "Problema",
        "Registros ficam separados entre organizações. O consumidor não consegue verificar com facilidade qual histórico permaneceu íntegro e quem executou cada etapa.",
        ORANGE, 18, 24,
    )
    add_card(
        slide, 10.00, 2.18, 9.05, 4.12,
        "Objetivo",
        "Compartilhar um histórico público e verificável de lotes. A MetaMask identifica os participantes, o contrato aplica perfis e estados, e a Sepolia confirma transações e eventos.",
        MINT, 20, 26,
    )

    actors = ["Produtor", "Beneficiador", "Transportador", "Distribuidor", "Consumidor"]
    start_x = 1.00
    y = 7.40
    for index, actor in enumerate(actors):
        x = start_x + index * 3.78
        if index < len(actors) - 1:
            add_connector(slide, x + 2.85, y + 0.58, x + 3.58, y + 0.58, TEAL, 2.3, True)
        card = add_round_rect(slide, x, y, 2.90, 1.18, GREEN_SOFT if index % 2 == 0 else ORANGE_SOFT)
        set_text(card, actor, 17, GREEN_DARK, PP_ALIGN.CENTER, margin=0.06)
    add_text(slide, 1.10, 9.20, 17.80, 0.62, "A blockchain preserva o registro confirmado, mas não prova que o dado informado na origem era verdadeiro.", 17, GRAY, PP_ALIGN.CENTER)
    set_notes(slide, "Apresentar o problema dos registros fragmentados e o objetivo do EcoOrigem. Destacar que blockchain garante integridade do registro confirmado, não a veracidade do dado de origem.")


def build_first_delivery(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 2)
    add_title(slide, "Primeira Entrega", "A base didática construída antes da integração com a Ethereum")
    add_card(slide, 0.90, 2.25, 8.75, 2.60, "Blockchain local em Python", "Blocos encadeados, prova de trabalho, nonce, hash SHA-256 e persistência local.", LIME, 19, 24)
    add_card(slide, 10.30, 2.25, 8.75, 2.60, "Integridade verificável", "Raiz de Merkle, assinatura de carteiras e validação de transações antes da inclusão no bloco.", ORANGE, 19, 24)
    add_card(slide, 0.90, 5.45, 8.75, 2.60, "Regras de rastreabilidade", "Contrato didático com perfis, custódia e ordem de etapas do produtor ao distribuidor.", TEAL, 19, 24)
    add_card(slide, 10.30, 5.45, 8.75, 2.60, "Aplicação e qualidade", "Interface web, API, Docker, logs amigáveis, testes automatizados e relatório técnico.", YELLOW, 19, 24)
    add_small_pill(slide, 6.20, 9.02, 7.60, "Resultado: conceito validado em ambiente local", GREEN_DARK, WHITE, 18)
    set_notes(slide, "Resumir a Primeira Entrega como base conceitual. Explicar que ela permitiu validar encadeamento, integridade, regras e experiência antes da migração para a rede pública de teste.")


def build_second_delivery(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 3)
    add_title(slide, "Segunda Entrega", "Melhorias e novas implementações para uma dApp pública")

    improvements = [
        ("Contrato Solidity", "Sete grupos obrigatórios usados com regras reais, NatSpec, eventos e erros.", "contract", PURPLE),
        ("Ethereum Sepolia", "Estado público, transações confirmadas e histórico consultável no Etherscan.", "sepolia", BLUE),
        ("MetaMask", "Conexão, assinatura de sessão, troca de rede e confirmação de transações.", "metamask", ORANGE_SOFT),
        ("Frontend Web3.js", "Leituras, escritas pagáveis, eventos e erros traduzidos em HTML, CSS e JavaScript.", "web3", ORANGE_SOFT),
        ("Documentos e IPFS", "SHA-256 e URI on-chain; o arquivo permanece fora da blockchain.", "ipfs", GREEN_SOFT),
        ("Deploy e testes", "Vercel por HTTPS, suíte local, testes Remix e auditoria de credenciais.", "vercel", LIGHT_GRAY),
    ]
    positions = [(0.85, 2.15), (7.00, 2.15), (13.15, 2.15), (0.85, 5.85), (7.00, 5.85), (13.15, 5.85)]
    for (title, body, icon, accent), (x, y) in zip(improvements, positions):
        add_shadow(slide, x, y, 5.15, 2.80)
        add_round_rect(slide, x, y, 5.15, 2.80, PAPER, line=GREEN_SOFT, line_width=1.0)
        add_round_rect(slide, x + 0.24, y + 0.25, 0.98, 0.98, accent)
        add_icon(slide, icon, x + 0.38, y + 0.38, 0.70)
        add_text(slide, x + 1.43, y + 0.29, 3.38, 0.55, title, 21, GREEN_DARK)
        add_text(slide, x + 0.30, y + 1.34, 4.55, 1.16, body, 15.3, GRAY)
    set_notes(slide, "Apresentar as mudanças da Entrega 2 como evolução da base local: Solidity, Sepolia, MetaMask, Web3.js, IPFS, Vercel e novos níveis de teste e segurança.")


def build_technologies(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 4)
    add_title(slide, "IDEs, frameworks e serviços", "Cada tecnologia tem uma responsabilidade no ciclo da dApp")

    tools = [
        ("Remix IDE", "Importa, compila, testa e envia o deploy.", "remix", LIGHT_GRAY),
        ("Solidity", "Implementa regras, perfis, estados e eventos.", "solidity", LIGHT_GRAY),
        ("MetaMask", "Guarda chaves e solicita assinaturas.", "metamask", ORANGE_SOFT),
        ("Sepolia", "Executa e replica o contrato de teste.", "sepolia", GREEN_SOFT),
        ("Web3.js 4.x", "Liga o frontend à carteira e à ABI.", "web3", ORANGE_SOFT),
        ("IPFS", "Mantém documentos fora da blockchain.", "ipfs", GREEN_SOFT),
        ("Vercel", "Publica o frontend estático por HTTPS.", "vercel", LIGHT_GRAY),
        ("Etherscan", "Confere contrato, blocos, eventos e hashes.", "etherscan", GREEN_SOFT),
    ]
    positions = [(0.75, 2.10), (5.55, 2.10), (10.35, 2.10), (15.15, 2.10), (0.75, 6.05), (5.55, 6.05), (10.35, 6.05), (15.15, 6.05)]

    for index in range(3):
        x = positions[index][0]
        add_connector(slide, x + 4.22, 3.24, positions[index + 1][0] - 0.10, 3.24, TEAL, 2.0, True)
    for index in range(4, 7):
        x = positions[index][0]
        add_connector(slide, x + 4.22, 7.19, positions[index + 1][0] - 0.10, 7.19, TEAL, 2.0, True)
    add_connector(slide, 17.26, 4.40, 17.26, 5.86, ORANGE, 2.0, True)
    add_connector(slide, 2.84, 5.86, 2.84, 4.40, ORANGE, 2.0, False, True)

    for item, position in zip(tools, positions):
        add_tool_card(slide, position[0], position[1], *item)

    add_small_pill(slide, 6.70, 9.50, 6.60, "Código → assinatura → rede → evidência", GREEN_DARK, WHITE, 16)
    set_notes(slide, "Percorrer as duas linhas. No ciclo de desenvolvimento: Remix, Solidity, MetaMask e Sepolia. No ciclo da aplicação: Web3.js, IPFS, Vercel e Etherscan. Mostrar que nenhuma ferramenta recebe chave privada do projeto.")


def build_flow(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 5)
    add_title(slide, "Fluxo completo da dApp", "Da ação no navegador até a confirmação pública e o histórico do lote")

    nodes = [
        ("Pessoa usuária", "preenche e consulta", "person", GREEN_SOFT),
        ("Frontend", "Vercel + Web3.js", "frontend", YELLOW),
        ("MetaMask", "conecta e assina", "metamask", ORANGE_SOFT),
        ("EcoOrigem.sol", "valida e grava", "contract", GREEN_SOFT),
        ("Sepolia", "confirma e replica", "sepolia", GREEN_SOFT),
        ("Etherscan", "expõe a evidência", "etherscan", GREEN_SOFT),
    ]
    x_positions = [0.55, 3.80, 7.05, 10.30, 13.55, 16.80]
    for index in range(len(nodes) - 1):
        add_connector(slide, x_positions[index] + 2.60, 3.50, x_positions[index + 1] - 0.12, 3.50, TEAL, 2.4, True)
    for node, x in zip(nodes, x_positions):
        add_flow_node(slide, x, 2.42, 2.65, *node)

    add_connector(slide, 11.62, 4.65, 11.62, 5.67, ORANGE, 2.0, True, True)
    add_round_rect(slide, 9.92, 5.70, 3.42, 1.10, PAPER, line=TEAL, line_width=1.6)
    add_icon(slide, "ipfs", 10.18, 5.88, 0.64)
    add_text(slide, 10.98, 5.83, 2.05, 0.36, "IPFS", 18, GREEN_DARK)
    add_text(slide, 10.98, 6.17, 2.05, 0.32, "arquivo fora da rede", 12.5, GRAY)

    add_text(slide, 0.90, 7.35, 4.10, 0.48, "Máquina de estados do lote", 21, GREEN_DARK)
    states = ["Cadastrado", "Beneficiado", "Em transporte", "Distribuído", "Finalizado"]
    state_x = [0.90, 4.50, 8.10, 11.70, 15.30]
    colors = [YELLOW, GREEN_SOFT, ORANGE_SOFT, GREEN_SOFT, MINT]
    for index, (state, x, color) in enumerate(zip(states, state_x, colors)):
        if index < len(states) - 1:
            add_connector(slide, x + 2.75, 8.77, state_x[index + 1] - 0.15, 8.77, GREEN_DARK, 2.0, True)
        shape = add_round_rect(slide, x, 8.15, 2.78, 1.22, color)
        set_text(shape, state, 17, GREEN_DARK, PP_ALIGN.CENTER, margin=0.06)
    add_text(slide, 1.05, 9.78, 17.85, 0.44, "Cada transação válida emite eventos; operações fora do perfil ou da ordem são recusadas sem alterar o estado.", 15.5, GRAY, PP_ALIGN.CENTER)
    set_notes(slide, "Explicar o caminho de uma escrita: formulário, Web3.js, MetaMask, contrato, Sepolia e Etherscan. O IPFS recebe apenas o arquivo, enquanto hash e URI ficam no contrato. Em seguida, percorrer os cinco estados.")


def build_demo(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 6)
    add_title(slide, "Demonstração ao vivo", "O que será mostrado e em qual ferramenta")

    add_small_pill(slide, 0.95, 2.08, 4.00, "O que será demonstrado", GREEN_DARK, WHITE, 17)
    add_small_pill(slide, 15.05, 2.08, 3.95, "Onde será mostrado", GREEN_DARK, WHITE, 17)
    rows = [
        ("01", "Conectar e autenticar a carteira", "Vercel + MetaMask", MINT),
        ("02", "Ler totais, perfil e lotes com call", "Frontend", YELLOW),
        ("03", "Cadastrar lote com taxa em SepoliaETH", "Frontend + MetaMask", ORANGE),
        ("04", "Acompanhar hash, bloco e confirmação", "Frontend + Etherscan", TEAL),
        ("05", "Provocar erro de perfil e conferir evento", "Frontend + Etherscan", LIME),
    ]
    y = 2.82
    for number, action, where, accent in rows:
        add_shadow(slide, 0.95, y, 18.05, 1.22)
        add_round_rect(slide, 0.95, y, 18.05, 1.22, PAPER, line=GREEN_SOFT, line_width=1.0)
        circle = add_circle(slide, 1.20, y + 0.22, 0.78, accent)
        set_text(circle, number, 16, GREEN_DARK, PP_ALIGN.CENTER, margin=0.01)
        add_text(slide, 2.28, y + 0.21, 11.85, 0.78, action, 19, GREEN_DARK)
        where_shape = add_round_rect(slide, 14.90, y + 0.22, 3.72, 0.78, GREEN_SOFT)
        set_text(where_shape, where, 15, GREEN_DARK, PP_ALIGN.CENTER, margin=0.04)
        y += 1.48
    add_text(slide, 1.20, 10.35, 17.55, 0.42, "Plano B: vídeo de 3 a 5 minutos e capturas reais, sem fazer novo deploy durante a apresentação.", 15.5, GRAY, PP_ALIGN.CENTER)
    set_notes(slide, "Executar a demonstração pela URL da Vercel e pelo contrato já implantado. Mostrar leitura, escrita pagável, estado da transação, erro compreensível e evento no Etherscan. Não fazer deploy ao vivo.")


def build_bonus(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 7)
    add_title(slide, "Bônus: relatório de desenvolvimento", "Registro técnico preservado como evidência da evolução do projeto")

    add_card(slide, 0.90, 2.20, 7.85, 2.10, "Relatório técnico", "Documento de 21 páginas produzido na Primeira Entrega e preservado em PDF e DOCX.", MINT, 18, 24)
    add_card(slide, 0.90, 4.78, 7.85, 2.10, "Conteúdo", "Arquitetura, decisões de implementação, testes, segurança, resultados e limitações.", ORANGE, 18, 24)
    add_card(slide, 0.90, 7.36, 7.85, 2.10, "Valor para a Entrega 2", "Mostra a base que originou a migração para Solidity, MetaMask, Sepolia, Web3.js e Vercel.", YELLOW, 18, 24)

    add_shadow(slide, 10.10, 2.15, 7.35, 7.78)
    frame = add_round_rect(slide, 10.10, 2.15, 7.35, 7.78, WHITE, line=GREEN_SOFT, line_width=1.5)
    frame.adjustments[0] = 0.04
    slide.shapes.add_picture(
        str(REPORT_IMAGE),
        Inches(11.23), Inches(2.48),
        width=Inches(5.08), height=Inches(7.18),
    )
    add_small_pill(slide, 14.85, 9.42, 3.40, "Print do relatório", GREEN_DARK, WHITE, 14)
    add_text(slide, 1.00, 10.18, 17.90, 0.42, "Arquivos: docs/relatorio/relatorio-desenvolvimento-ecoorigem.pdf e .docx", 14.5, GRAY, PP_ALIGN.CENTER)
    set_notes(slide, "Apresentar o relatório como evidência adicional da Primeira Entrega. O print mostra uma página real de arquitetura. Explicar que a Segunda Entrega reaproveita o conhecimento documentado e muda a infraestrutura para Ethereum pública de teste.")


def build_thanks(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide, 8)

    add_small_pill(slide, 7.45, 1.02, 5.10, "EcoOrigem", GREEN_SOFT, GREEN_DARK, 24)
    add_text(slide, 2.00, 2.25, 16.00, 1.35, "Obrigada", 58, GREEN_DARK, PP_ALIGN.CENTER)
    add_text(slide, 3.00, 3.70, 14.00, 0.65, "Rastreabilidade verificável para a bioeconomia amazônica", 23, GRAY, PP_ALIGN.CENTER)

    leaf_left = slide.shapes.add_shape(MSO_SHAPE.TEAR, Inches(2.10), Inches(4.85), Inches(1.10), Inches(1.85))
    solid(leaf_left, MINT)
    no_line(leaf_left)
    leaf_left.rotation = 0
    leaf_right = slide.shapes.add_shape(MSO_SHAPE.TEAR, Inches(16.80), Inches(4.85), Inches(1.10), Inches(1.85))
    solid(leaf_right, ORANGE)
    no_line(leaf_right)
    leaf_right.rotation = 0

    team = "Ana Beatriz Maciel Nunes   •   Fernando Luiz da Silva Freire   •   Juliana Ballin Lima"
    add_text(slide, 2.00, 6.15, 16.00, 0.62, team, 17, GREEN_DARK, PP_ALIGN.CENTER)
    add_small_pill(slide, 5.30, 7.20, 9.40, "github.com/JulianaBallin/EcoOrigem", GREEN_DARK, WHITE, 18)
    add_text(slide, 4.00, 8.30, 12.00, 0.48, "Oficina de Desenvolvimento de Sistemas III", 18, GRAY, PP_ALIGN.CENTER)
    slide.shapes.add_picture(str(UEA_LOGO), Inches(8.25), Inches(9.03), width=Inches(3.50), height=Inches(1.22))
    set_notes(slide, "Agradecer, deixar o repositório visível e abrir espaço para a arguição.")


def validate_deck(prs: Presentation) -> None:
    """Valida as regras visuais pedidas antes de salvar."""
    if len(prs.slides) != 8:
        raise RuntimeError(f"A apresentação deve ter 8 slides, mas tem {len(prs.slides)}.")

    for slide_index, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if getattr(shape, "rotation", 0) not in (0, None):
                raise RuntimeError(f"Elemento rotacionado no slide {slide_index}.")
            if not getattr(shape, "has_text_frame", False):
                continue
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if run.font.bold is True:
                        raise RuntimeError(f"Texto em negrito no slide {slide_index}.")


def build() -> None:
    """Monta, valida e exporta PPTX e PDF."""
    prs = Presentation(TEMPLATE)
    remove_all_slides(prs)
    build_context(prs)
    build_first_delivery(prs)
    build_second_delivery(prs)
    build_technologies(prs)
    build_flow(prs)
    build_demo(prs)
    build_bonus(prs)
    build_thanks(prs)
    validate_deck(prs)
    prs.save(OUTPUT)

    with tempfile.TemporaryDirectory(prefix="ecoorigem-slides-", dir="/tmp") as profile:
        subprocess.run(
            [
                "libreoffice",
                f"-env:UserInstallation=file://{profile}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(SLIDES),
                str(OUTPUT),
            ],
            check=True,
            cwd=ROOT,
        )
    if not PDF.exists():
        raise RuntimeError("O LibreOffice não gerou o PDF da apresentação.")
    print(f"Apresentação gerada: {OUTPUT}")
    print(f"PDF gerado: {PDF}")


if __name__ == "__main__":
    build()
