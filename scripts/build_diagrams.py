# pylint: disable=line-too-long,wrong-import-position,too-many-arguments,too-many-positional-arguments,use-dict-literal,too-many-locals,unnecessary-lambda-assignment
"""Generate the architecture diagrams used by the report and the README.

All arrows are orthogonal (90 degree turns) and routed through free space.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "assets" / "img" / "diagramas"
GREEN_900, GREEN_700, GREEN_100, GREEN_50 = "#0b3d24", "#17693d", "#e3f0dc", "#f1f7ee"
INK, MUTED, BORDER = "#17261d", "#5a6b61", "#9fbf9a"
AMBER, BLUE, TEAL = "#fff4dd", "#e6f1fb", "#dff3f1"


def canvas(width: float, height: float):
    """Create a figure whose axes use a 0..width by 0..height coordinate system."""
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=200)
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    return fig, ax


def box(
    ax,
    x,
    y,
    w,
    h,
    title,
    lines=(),
    fill=GREEN_50,
    edge=GREEN_700,
    bold=GREEN_900,
    size=11,
):
    """Draw a rounded box with a title and optional detail lines."""
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=8",
            fc=fill,
            ec=edge,
            lw=1.6,
        )
    )
    ax.text(
        x + w / 2,
        y + 20,
        title,
        ha="center",
        va="center",
        fontsize=size,
        fontweight="bold",
        color=bold,
    )
    for index, line in enumerate(lines):
        ax.text(
            x + w / 2,
            y + 42 + index * 17,
            line,
            ha="center",
            va="center",
            fontsize=size - 2.5,
            color=INK,
        )


def arrow(ax, points, label=None, label_at=None, color=GREEN_700, both=False):
    """Draw an orthogonal arrow through ``points`` (list of (x, y))."""
    xs, ys = zip(*points)
    ax.plot(xs[:-1], ys[:-1], color=color, lw=1.8, solid_capstyle="round", zorder=1)
    style = "<|-|>" if both else "-|>"
    ax.annotate(
        "",
        xy=points[-1],
        xytext=points[-2],
        arrowprops=dict(
            arrowstyle=style,
            color=color,
            lw=1.8,
            shrinkA=0,
            shrinkB=0,
            mutation_scale=14,
        ),
        zorder=2,
    )
    if both:
        ax.annotate(
            "",
            xy=points[0],
            xytext=points[1],
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=1.8,
                shrinkA=0,
                shrinkB=0,
                mutation_scale=14,
            ),
            zorder=2,
        )
    if label and label_at:
        ax.text(
            *label_at,
            label,
            ha="left",
            va="center",
            fontsize=8.5,
            color=MUTED,
            style="italic",
        )


def save(fig, name):
    """Write the figure to assets/img/diagramas."""
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, facecolor="white")
    plt.close(fig)


def architecture():
    """Layers: browser, wallet gateway, node (API, contract, chain), storage."""
    fig, ax = canvas(1100, 660)
    box(
        ax,
        330,
        20,
        440,
        80,
        "Navegador",
        [
            "Interface web (HTML, CSS e JavaScript)",
            "Registrar, consultar e visualizar a cadeia",
        ],
        fill=BLUE,
        edge="#175a96",
        bold="#0f3f6b",
    )
    box(
        ax,
        330,
        170,
        440,
        100,
        "Gateway web e carteiras",
        [
            "Flask + keystore local (Ed25519)",
            "Assina a transação da carteira ativa",
            "Somente leitura de dados públicos",
        ],
        fill=AMBER,
        edge="#b26a00",
        bold="#5c3a00",
    )
    arrow(ax, [(550, 100), (550, 170)], "HTTP e JSON", (562, 135))
    arrow(ax, [(550, 270), (550, 340)], "transação assinada (JSON)", (562, 305))
    ax.add_patch(
        FancyBboxPatch(
            (40, 340),
            1020,
            250,
            boxstyle="round,pad=0,rounding_size=12",
            fc="white",
            ec=GREEN_700,
            lw=2,
            ls=(0, (6, 4)),
        )
    )
    ax.text(
        60,
        362,
        "Nó da blockchain local (processo Python, porta 8545)",
        fontsize=11,
        fontweight="bold",
        color=GREEN_900,
        va="center",
    )
    box(
        ax,
        70,
        400,
        280,
        160,
        "API e validação",
        [
            "Verifica assinatura, nonce",
            "e relógio da transação",
            "Mempool e log de rejeições",
            "Bloqueia escrita se a",
            "integridade falhar",
        ],
    )
    box(
        ax,
        410,
        400,
        280,
        160,
        "Contrato inteligente",
        [
            "EcoOrigem (Python)",
            "Perfis e controle de acesso",
            "Máquina de estados do lote",
            "Validação de entradas",
            "Eventos e histórico",
        ],
        fill=GREEN_100,
    )
    box(
        ax,
        750,
        400,
        280,
        160,
        "Cadeia de blocos",
        [
            "Blocos encadeados por SHA-256",
            "Raiz de Merkle por bloco",
            "Prova de trabalho (nonce)",
            "Persistência em ledger.json",
        ],
    )
    arrow(ax, [(350, 480), (410, 480)], both=True)
    arrow(ax, [(690, 480), (750, 480)], both=True)
    ax.text(
        550,
        625,
        "O estado do contrato é reconstruído reexecutando as transações da cadeia.",
        ha="center",
        va="center",
        fontsize=9,
        color=MUTED,
        style="italic",
    )
    save(fig, "arquitetura.png")


def state_machine():
    """Lot life cycle with the operation and profile that trigger each step."""
    fig, ax = canvas(1200, 300)
    names = ["CADASTRADO", "BENEFICIADO", "EM_TRANSPORTE", "DISTRIBUIDO", "FINALIZADO"]
    fills = ["#e8edf2", AMBER, BLUE, TEAL, "#e3f4e6"]
    ops = [
        ("register_lot", "Produtor"),
        ("record_processing", "Beneficiador"),
        ("start_transport", "Transportador"),
        ("confirm_delivery", "Distribuidor designado"),
        ("finalize_lot", "Distribuidor responsável"),
    ]
    width, gap, top = 170, 62, 130
    xs = [30 + i * (width + gap) for i in range(5)]
    for i, (x, name) in enumerate(zip(xs, names)):
        box(ax, x, top, width, 70, "", [], fill=fills[i], edge=GREEN_700, size=11)
        ax.text(
            x + width / 2,
            top + 35,
            name,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=GREEN_900,
        )
        op, who = ops[i]
        ax.text(
            x + width / 2,
            60,
            op,
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=GREEN_900,
        )
        ax.text(
            x + width / 2, 80, who, ha="center", va="center", fontsize=8.5, color=MUTED
        )
        ax.plot(
            [x + width / 2] * 2, [95, top - 2], color=BORDER, lw=1.4, ls=(0, (3, 3))
        )
        if i:
            arrow(ax, [(xs[i - 1] + width, top + 35), (x, top + 35)])
    ax.text(
        xs[4] + width,
        228,
        "Estado final: o contrato recusa qualquer alteração",
        ha="right",
        va="center",
        fontsize=9,
        color="#b3261e",
    )
    ax.text(
        600,
        275,
        "Saltar ou repetir etapas é rejeitado com INVALID_TRANSITION",
        ha="center",
        va="center",
        fontsize=9,
        color=MUTED,
        style="italic",
    )
    save(fig, "maquina-de-estados.png")


def blocks():
    """Three linked blocks. Arrows leave the hash and enter the next previous-hash field."""
    fig, ax = canvas(1200, 380)
    fields = [
        "Índice",
        "Data",
        "Hash anterior",
        "Raiz de Merkle",
        "Dificuldade e nonce",
        "Hash do bloco",
    ]
    labels = ["Bloco 0 (gênesis)", "Bloco 1", "Bloco 2"]
    width, height, gap, top = 300, 250, 100, 60
    xs = [40 + i * (width + gap) for i in range(3)]
    row = lambda i: top + 62 + i * 28
    for b, x in enumerate(xs):
        box(ax, x, top, width, height, labels[b], [], fill=GREEN_50)
        for i, field in enumerate(fields):
            fill = GREEN_100 if i in (2, 5) else "white"
            ax.add_patch(
                FancyBboxPatch(
                    (x + 16, row(i) - 11),
                    width - 32,
                    22,
                    boxstyle="round,pad=0,rounding_size=4",
                    fc=fill,
                    ec=BORDER,
                    lw=1,
                )
            )
            ax.text(
                x + 26,
                row(i),
                field,
                fontsize=9,
                va="center",
                color=INK,
                fontweight="bold" if i in (2, 5) else "normal",
            )
    for b in range(2):
        x_out = xs[b] + width - 16
        x_gap = xs[b] + width + gap / 2
        arrow(
            ax,
            [
                (x_out, row(5)),
                (x_gap, row(5)),
                (x_gap, row(2)),
                (xs[b + 1] + 16, row(2)),
            ],
        )
    ax.text(
        600,
        345,
        "O hash anterior de cada bloco repete o hash do bloco que o precede. Alterar um bloco quebra todos os seguintes.",
        ha="center",
        va="center",
        fontsize=9,
        color=MUTED,
        style="italic",
    )
    save(fig, "estrutura-dos-blocos.png")


def sequence():
    """Life of one operation from the form to the mined block."""
    fig, ax = canvas(1200, 560)
    actors = [
        ("Pessoa usuária", 110),
        ("Gateway e carteira", 340),
        ("Nó", 600),
        ("Contrato", 850),
        ("Cadeia", 1090),
    ]
    for name, x in actors:
        box(ax, x - 85, 15, 170, 40, name, [], fill=GREEN_100, size=10)
        ax.plot([x, x], [55, 540], color=BORDER, lw=1.3, ls=(0, (4, 4)), zorder=0)
    steps = [
        (0, 1, 100, "1  preenche e envia o formulário"),
        (1, 2, 155, "2  assina e envia a transação"),
        (2, 2, 210, None),
        (2, 3, 255, "4  executa a regra de negócio"),
        (3, 2, 305, "5  eventos ou revert"),
        (2, 4, 360, "6  minera e encadeia o bloco"),
        (2, 1, 415, "7  recibo (bloco e hash)"),
        (1, 0, 470, "8  confirmação ou rejeição"),
    ]
    xs = dict(enumerate(x for _, x in actors))
    for a, b, y, label in steps:
        if label is None:
            continue
        direction = 1 if xs[b] > xs[a] else -1
        arrow(ax, [(xs[a] + 4 * direction, y), (xs[b] - 4 * direction, y)])
        ax.text(
            (xs[a] + xs[b]) / 2,
            y - 14,
            label,
            ha="center",
            va="center",
            fontsize=9,
            color=INK,
            bbox=dict(fc="white", ec="none", pad=2),
            zorder=3,
        )
    ax.text(
        600,
        200,
        "3  valida assinatura, nonce e data",
        ha="center",
        va="center",
        fontsize=9,
        color=INK,
        bbox=dict(fc="white", ec="none", pad=2),
        zorder=3,
    )
    ax.add_patch(
        FancyBboxPatch(
            (470, 178),
            260,
            44,
            boxstyle="round,pad=0,rounding_size=6",
            fc="white",
            ec=GREEN_700,
            lw=1.4,
            zorder=2,
        )
    )
    ax.text(
        600,
        515,
        "Se qualquer verificação falhar, nenhum bloco é criado e a rejeição é registrada.",
        ha="center",
        va="center",
        fontsize=9,
        color="#b3261e",
        style="italic",
        bbox=dict(fc="white", ec="none", pad=3),
        zorder=3,
    )
    save(fig, "sequencia-da-operacao.png")


def main() -> int:
    """Generate every diagram."""
    for build in (architecture, state_machine, blocks, sequence):
        build()
    print(f"Diagramas gerados em {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
