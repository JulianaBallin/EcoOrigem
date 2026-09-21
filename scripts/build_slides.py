"""Build the presentation (PPTX and PDF) used in the class demonstration.

The deck follows the ten minute script of the course: problem and justification,
architecture and contract, live demonstration, tests and conclusion. Numbers
come from ``docs/evidencias/metricas.json``, written by ``make report``.
Run with ``make slides``.
"""

# pylint: disable=line-too-long,too-many-locals,too-many-statements,too-many-arguments,too-many-positional-arguments,protected-access,no-member

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVID = DOCS / "assets" / "evidencias"
DIAG = DOCS / "assets" / "diagramas"
SLIDE_IMG = DOCS / "assets" / "slides"
LOGO = ROOT / "assets" / "img" / "logo.png"
UEA = DOCS / "assets" / "logos" / "uea.png"
METRICS = DOCS / "evidencias" / "metricas.json"
OUT = DOCS / "apresentacao-ecoorigem.pptx"

FONT = "Arial"
INK, FOREST, GREEN, LIME = "17261D", "0B3D24", "17693D", "8CC63F"
TINT, MUTED, LINE, RED = "F1F7EE", "5A6B61", "D2DECE", "B3261E"
PALE = "CFE5C5"


def rgb(value: str) -> RGBColor:
    """Hex string to RGBColor."""
    return RGBColor.from_string(value)


class Deck:
    """Thin helper around python-pptx with the deck's typography and palette."""

    def __init__(self) -> None:
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(13.333), Inches(7.5)
        self.number = 0

    def slide(self, background: str = "FFFFFF", numbered: bool = True):
        """Add a blank slide with a solid background and a small page number."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = rgb(background)
        self.number += 1
        if numbered:
            dark = background != "FFFFFF"
            self.text(
                slide,
                12.2,
                6.95,
                0.7,
                0.3,
                str(self.number),
                11,
                color=PALE if dark else MUTED,
                align=PP_ALIGN.RIGHT,
            )
        return slide

    @staticmethod
    def rect(
        slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, line=None, radius=None
    ):
        """Add a filled rectangle (optionally rounded) with an optional outline."""
        shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        style = shp._element.find(qn("p:style"))  # pylint: disable=protected-access
        if style is not None:
            shp._element.remove(style)  # pylint: disable=protected-access
        if fill is None:
            shp.fill.background()
        else:
            shp.fill.solid()
            shp.fill.fore_color.rgb = rgb(fill)
        if line:
            shp.line.color.rgb = rgb(line)
            shp.line.width = Pt(1)
        else:
            shp.line.fill.background()
        if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            shp.adjustments[0] = radius
        return shp

    @staticmethod
    def text(
        slide,
        x,
        y,
        w,
        h,
        content,
        size,
        bold=False,
        color=INK,
        align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP,
        spacing=None,
        line_spacing=None,
        after=0,
    ):
        """Add a text box. ``content`` is a string or a list of paragraphs."""
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        frame = box.text_frame
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = frame.margin_top = (
            frame.margin_bottom
        ) = 0
        frame.vertical_anchor = anchor
        paragraphs = content if isinstance(content, list) else [content]
        for index, item in enumerate(paragraphs):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.alignment = align
            paragraph.space_after = Pt(after)
            if line_spacing:
                paragraph.line_spacing = line_spacing
            run = paragraph.add_run()
            run.text = item
            run.font.name, run.font.size, run.font.bold = FONT, Pt(size), bold
            run.font.color.rgb = rgb(color)
            if spacing:
                run._r.get_or_add_rPr().set(
                    "spc", str(spacing)
                )  # pylint: disable=protected-access
        return box

    @staticmethod
    def picture(slide, path, x, y, w=None, h=None):
        """Place an image keeping its aspect ratio."""
        return slide.shapes.add_picture(
            str(path),
            Inches(x),
            Inches(y),
            Inches(w) if w else None,
            Inches(h) if h else None,
        )

    @staticmethod
    def line(slide, x1, y1, x2, y2, color=MUTED, width=1.25, dash=False):
        """Add a straight connector segment."""
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
        )
        connector.line.color.rgb = rgb(color)
        connector.line.width = Pt(width)
        if dash:
            connector.line.dash_style = 4  # MSO_LINE.DASH
        return connector

    @staticmethod
    def notes(slide, text: str) -> None:
        """Set the speaker notes."""
        slide.notes_slide.notes_text_frame.text = text


def overline(deck: Deck, slide, x, y, label, color=GREEN, w=4.0):
    """Small spaced caps label above a block."""
    deck.text(slide, x, y, w, 0.3, label.upper(), 11.5, True, color, spacing=160)


def title(deck: Deck, slide, text, color=INK, w=11.6, size=34):
    """Slide title, left aligned."""
    deck.text(slide, 0.9, 0.7, w, 1.3, text, size, True, color, line_spacing=0.95)


# ------------------------------------------------------------ image prep
def prepare_images() -> dict[str, Path]:
    """Create the tiles used on the demonstration slide."""
    SLIDE_IMG.mkdir(parents=True, exist_ok=True)
    size = (1280, 492)
    tiles: dict[str, Path] = {}

    def crop(source: str, box: tuple[int, int, int, int], name: str) -> None:
        image = Image.open(EVID / source).convert("RGB").crop(box)
        target = SLIDE_IMG / name
        image.save(target)
        tiles[name] = target

    def onto_canvas(source: str, name: str, width: int) -> None:
        image = Image.open(EVID / source).convert("RGB")
        scaled = image.resize(
            (width, int(image.height * width / image.width)), Image.LANCZOS
        )
        canvas = Image.new("RGB", size, "#" + TINT)
        canvas.paste(
            scaled, ((size[0] - scaled.width) // 2, (size[1] - scaled.height) // 2)
        )
        target = SLIDE_IMG / name
        canvas.save(target)
        tiles[name] = target

    crop("01-painel.png", (0, 0, size[0], size[1]), "demo-1-painel.png")
    onto_canvas("03-registrar-confirmado.png", "demo-2-confirmado.png", 1040)
    crop(
        "04-consultar-lote.png", (0, 150, size[0], 150 + size[1]), "demo-3-consulta.png"
    )
    onto_canvas("05-rejeicao-1.png", "demo-4-rejeicao.png", 1040)
    return tiles


# ------------------------------------------------------------------ slides
def build(metrics: dict) -> Deck:
    """Assemble the eight slides."""
    deck = Deck()
    scen = metrics["scenarios"]
    total = scen["V"] + scen["I"] + scen["A"]

    # 1. Cover
    s = deck.slide(FOREST, numbered=False)
    deck.rect(s, 8.2, 0, 5.133, 7.5, "FFFFFF")
    deck.text(s, 0.9, 2.15, 7.0, 1.3, "EcoOrigem", 72, True, "FFFFFF")
    deck.text(
        s,
        0.9,
        3.55,
        6.6,
        1.4,
        "Rastreabilidade de produtos da bioeconomia amazônica em uma blockchain local",
        22,
        False,
        PALE,
        line_spacing=1.1,
    )
    deck.text(
        s,
        0.9,
        6.0,
        6.8,
        0.9,
        [
            "Oficina de Desenvolvimento de Sistemas III",
            "Ana Beatriz Maciel Nunes, Fernando Luiz da Silva Freire e Juliana Ballin Lima",
        ],
        12,
        False,
        PALE,
        after=3,
    )
    deck.picture(s, LOGO, 8.75, 2.35, w=4.05)
    deck.picture(s, UEA, 9.55, 4.65, w=2.5)
    deck.notes(
        s,
        "Abertura, 10 segundos. Apresentar o nome do projeto e a equipe. Sugestão de fala: Ana.",
    )

    # 2. Problem and objective
    s = deck.slide()
    overline(deck, s, 0.9, 0.75, "Problema")
    deck.text(
        s,
        0.9,
        1.1,
        6.2,
        2.2,
        "Cada etapa da cadeia guarda o seu próprio registro.",
        34,
        True,
        INK,
        line_spacing=0.95,
    )
    deck.text(
        s,
        0.9,
        3.05,
        5.6,
        1.5,
        "O consumidor não tem como saber qual versão é a verdadeira, e quem administra o sistema pode reescrever o passado.",
        16,
        False,
        MUTED,
        line_spacing=1.15,
    )
    overline(deck, s, 0.9, 4.85, "Objetivo")
    deck.text(
        s,
        0.9,
        5.2,
        5.6,
        1.4,
        "Registrar cada etapa do lote de forma verificável, com regras que impedem atalhos.",
        20,
        True,
        GREEN,
        line_spacing=1.1,
    )
    actors = ["Produtor", "Beneficiador", "Transportador", "Distribuidor"]
    top, box_h, gap = 1.45, 0.95, 0.3
    for index, name in enumerate(actors):
        y = top + index * (box_h + gap)
        deck.rect(s, 7.3, y, 2.7, box_h, TINT, MSO_SHAPE.ROUNDED_RECTANGLE, LINE, 0.12)
        deck.text(s, 7.55, y + 0.17, 2.3, 0.35, name, 16, True, INK)
        deck.text(s, 7.55, y + 0.55, 2.3, 0.3, "registro próprio", 12, False, MUTED)
        deck.line(s, 10.0, y + box_h / 2, 10.45, y + box_h / 2, MUTED, 1.25, True)
    first, last = top + box_h / 2, top + 3 * (box_h + gap) + box_h / 2
    deck.line(s, 10.45, first, 10.45, last, MUTED, 1.25, True)
    mid = (first + last) / 2
    deck.line(s, 10.45, mid, 10.85, mid, MUTED, 1.25, True)
    deck.rect(
        s, 10.85, mid - 0.7, 1.75, 1.4, FOREST, MSO_SHAPE.ROUNDED_RECTANGLE, None, 0.1
    )
    deck.text(
        s,
        10.85,
        mid - 0.55,
        1.75,
        0.75,
        "?",
        40,
        True,
        LIME,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
    )
    deck.text(
        s,
        10.85,
        mid + 0.2,
        1.75,
        0.4,
        "Consumidor",
        13,
        True,
        "FFFFFF",
        PP_ALIGN.CENTER,
    )
    deck.notes(
        s,
        "Tempo total do bloco 1: 2 minutos, junto com o próximo slide. Problema: os registros ficam separados em cada organização e ninguém prova qual é o verdadeiro. Objetivo: registrar cada etapa de forma verificável, com regras. Sugestão de fala: Ana.",
    )

    # 3. Why blockchain
    s = deck.slide()
    title(
        deck,
        s,
        "O histórico precisa valer para todos, e ninguém pode reescrevê-lo sozinho.",
        w=10.8,
    )
    deck.rect(s, 0.9, 2.55, 4.9, 3.7, TINT, MSO_SHAPE.ROUNDED_RECTANGLE, None, 0.05)
    overline(deck, s, 1.3, 2.9, "Banco de dados", MUTED)
    deck.text(
        s,
        1.3,
        3.45,
        4.1,
        2.6,
        [
            "Quem administra pode alterar e apagar.",
            "As regras ficam na aplicação e podem ser contornadas.",
            "A auditoria depende do próprio dono do dado.",
        ],
        17,
        False,
        INK,
        after=14,
        line_spacing=1.05,
    )
    deck.rect(s, 6.1, 2.55, 6.3, 3.7, FOREST, MSO_SHAPE.ROUNDED_RECTANGLE, None, 0.05)
    overline(deck, s, 6.6, 2.9, "Blockchain do EcoOrigem", LIME, 5.0)
    deck.text(
        s,
        6.6,
        3.45,
        5.3,
        2.6,
        [
            "Alterar um bloco quebra o encadeamento dali em diante.",
            "As regras são executadas pelo contrato inteligente.",
            "Cada operação leva a assinatura digital da carteira.",
        ],
        17,
        False,
        "FFFFFF",
        after=14,
        line_spacing=1.05,
    )
    deck.text(
        s,
        0.9,
        6.5,
        9.5,
        0.4,
        "Faz sentido porque há vários participantes que não confiam plenamente uns nos outros.",
        14,
        False,
        MUTED,
    )
    deck.notes(
        s,
        "Comparar um banco de dados centralizado com a blockchain. Ressalvar que blockchain garante que o registro não muda depois de gravado, não que ele seja verdadeiro na origem. Sugestão de fala: Ana.",
    )

    # 4. Architecture
    s = deck.slide()
    title(deck, s, "A carteira assina, o nó valida e o contrato decide.", w=11.5)
    deck.picture(s, DIAG / "arquitetura-slide.png", 0.75, 1.95, w=7.7)
    x = 8.95
    for offset, (label, body) in enumerate(
        [
            (
                "Navegador e gateway",
                "A interface nunca fala direto com o nó. O gateway assina com a carteira ativa.",
            ),
            (
                "Nó da blockchain",
                "Confere assinatura, nonce e data, minera com prova de trabalho e grava o bloco.",
            ),
            (
                "Contrato inteligente",
                "Perfis, ordem das etapas e validação das entradas, em Python.",
            ),
        ]
    ):
        y = 2.0 + offset * 1.55
        overline(deck, s, x, y, label, GREEN, 3.9)
        deck.text(s, x, y + 0.35, 3.9, 1.0, body, 15, False, INK, line_spacing=1.1)
    deck.notes(
        s,
        "Bloco 2: 2 minutos, junto com o próximo slide. Mostrar o caminho de uma operação: interface, gateway com carteira, nó, contrato e cadeia. Relacionar com o modelo de DApp da Aula 01. Sugestão de fala: Fernando.",
    )

    # 5. Contract
    s = deck.slide()
    title(deck, s, "O contrato só deixa o lote andar em ordem.", w=11.5)
    deck.picture(s, DIAG / "maquina-de-estados.png", 0.7, 1.75, w=11.95)
    for index, (label, body) in enumerate(
        [
            (
                "Quem pode",
                "Cada etapa exige um perfil: produtor, beneficiador, transportador ou distribuidor.",
            ),
            (
                "Em que ordem",
                "Pular ou repetir uma etapa é rejeitado. O lote finalizado não muda mais.",
            ),
            (
                "O que fica na cadeia",
                "Origem, etapas, responsáveis e o hash dos documentos. Os arquivos ficam de fora.",
            ),
        ]
    ):
        x = 0.9 + index * 4.1
        overline(deck, s, x, 5.05, label, GREEN, 3.6)
        deck.text(s, x, 5.4, 3.6, 1.3, body, 15, False, INK, line_spacing=1.1)
    deck.notes(
        s,
        "Explicar perfis, máquina de estados e regras de custódia: só o distribuidor designado confirma o recebimento. Mencionar que tudo é validado antes de alterar o estado, como um revert do Solidity. Sugestão de fala: Fernando.",
    )

    # 6. Demonstration
    tiles = prepare_images()
    s = deck.slide()
    title(deck, s, "Demonstração na blockchain local", size=30, w=8)
    deck.text(s, 9.4, 0.85, 3.0, 0.4, "4 minutos", 14, False, MUTED, PP_ALIGN.RIGHT)
    captions = [
        "1  Blockchain em execução",
        "2  Operação confirmada no bloco",
        "3  Registro e estado do lote",
        "4  Operação sem permissão rejeitada",
    ]
    order = [
        "demo-1-painel.png",
        "demo-2-confirmado.png",
        "demo-3-consulta.png",
        "demo-4-rejeicao.png",
    ]
    tile_w = 5.5
    tile_h = tile_w * 492 / 1280
    for index, (name, caption) in enumerate(zip(order, captions)):
        col, row = index % 2, index // 2
        x, y = 0.9 + col * (tile_w + 0.45), 1.6 + row * (tile_h + 0.75)
        deck.picture(s, tiles[name], x, y, w=tile_w)
        deck.text(
            s,
            x,
            y + tile_h + 0.1,
            tile_w,
            0.3,
            caption,
            13,
            True,
            GREEN if index < 3 else RED,
        )
    deck.notes(
        s,
        "Bloco 3: 4 minutos, feito ao vivo na máquina da equipe. Os quatro passos exigidos: 1) mostrar a blockchain local em execução (make docker-up ou make start); 2) realizar uma operação pela interface e mostrar a confirmação com hash e bloco; 3) consultar o registro e mostrar a mudança de estado do lote; 4) rejeição de operação inválida ou sem permissão, usando os cenários da aba Registrar. Se a máquina falhar, usar o vídeo docs/video/demonstracao.webm. Sugestão: Juliana executa os passos 1 e 2, Fernando o passo 3 e Ana o passo 4.",
    )

    # 7. Tests
    s = deck.slide()
    title(deck, s, "Testado no que funciona e no que deve falhar.", w=11.5)
    stats = [
        (str(metrics["passed"]), "testes automatizados aprovados"),
        (f"{metrics['coverage']}%", "de cobertura do código"),
        (f"{scen['ok']} de {total}", "cenários com o resultado esperado"),
    ]
    for index, (number, label) in enumerate(stats):
        y = 1.9 + index * 1.55
        deck.text(s, 0.9, y, 3.6, 0.9, number, 46, True, GREEN)
        deck.text(s, 0.9, y + 0.85, 3.6, 0.4, label, 14, False, MUTED)
    data = CategoryChartData()
    data.categories = [
        "Operações válidas",
        "Entradas inválidas ou sem permissão",
        "Integridade da cadeia",
    ]
    data.add_series("Cenários", (scen["V"], scen["I"], scen["A"]))
    frame = s.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED,
        Inches(5.3),
        Inches(1.95),
        Inches(7.1),
        Inches(3.1),
        data,
    )
    chart = frame.chart
    chart.has_legend = False
    chart.has_title = False
    chart.font.name, chart.font.size = FONT, Pt(13)
    chart.font.color.rgb = rgb(INK)
    plot = chart.plots[0]
    plot.gap_width = 55
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.font.size, labels.font.bold = Pt(14), True
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    plot.series[0].format.fill.solid()
    plot.series[0].format.fill.fore_color.rgb = rgb(GREEN)
    chart.value_axis.visible = False
    chart.value_axis.has_major_gridlines = False
    chart.category_axis.reverse_order = True
    chart.category_axis.format.line.color.rgb = rgb(LINE)
    chart.category_axis.tick_labels.font.size = Pt(13)
    deck.text(
        s,
        5.3,
        5.35,
        7.1,
        1.3,
        [
            "Toda entrada inválida ou sem permissão foi rejeitada sem criar bloco.",
            "A adulteração de um bloco foi detectada, com e sem refazer a prova de trabalho.",
        ],
        14,
        False,
        MUTED,
        after=6,
        line_spacing=1.1,
    )
    deck.notes(
        s,
        f"Bloco 4, parte 1. {metrics['passed']} testes pytest, cobertura de {metrics['coverage']}%, Pylint {metrics['pylint']} de 10, Bandit e pip-audit sem achados. Black Duck não foi executado por indisponibilidade da ferramenta. {total} cenários reais com resultado esperado versus obtido. Sugestão de fala: Juliana.",
    )

    # 8. Limits and conclusion
    s = deck.slide(FOREST)
    overline(deck, s, 0.9, 0.85, "Limitações", LIME)
    deck.text(
        s,
        0.9,
        1.35,
        5.0,
        4.4,
        [
            "Um único nó: a validação detecta a fraude, mas não há rede para recusá-la.",
            "Carteiras de demonstração guardadas no servidor, sem MetaMask.",
            "A blockchain garante o registro, não a verdade da informação na origem.",
        ],
        16,
        False,
        "FFFFFF",
        after=16,
        line_spacing=1.1,
    )
    overline(deck, s, 6.9, 0.85, "Conclusão", LIME)
    deck.text(
        s,
        6.9,
        1.35,
        5.6,
        3.0,
        "Uma blockchain local em Python já sustenta a rastreabilidade do lote, do produtor ao consumidor.",
        30,
        True,
        "FFFFFF",
        line_spacing=1.0,
    )
    deck.text(
        s,
        6.9,
        4.6,
        5.5,
        1.2,
        "Próximos passos: vários nós com consenso, carteira no navegador e QR Code por lote.",
        16,
        False,
        PALE,
        line_spacing=1.1,
    )
    deck.text(
        s, 0.9, 6.55, 6.0, 0.3, "github.com/JulianaBallin/EcoOrigem", 13, False, PALE
    )
    deck.notes(
        s,
        "Bloco 4, parte 2: limitações e conclusão, dentro dos 2 minutos. Ser direto sobre o que o protótipo não faz. Encerrar com os próximos passos. Sugestão de fala: Juliana.",
    )
    return deck


def main() -> int:
    """Build the PPTX and convert it to PDF."""
    if not METRICS.exists():
        print("Execute make report antes: faltam as métricas medidas.")
        return 1
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    deck = build(metrics)
    deck.prs.save(str(OUT))
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(DOCS),
            str(OUT),
        ],
        check=False,
        capture_output=True,
    )
    print(f"Apresentação gerada: {OUT} e {OUT.with_suffix('.pdf')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
