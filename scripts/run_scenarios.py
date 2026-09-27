"""Run the documented test scenarios against a fresh local node.

Every scenario is executed for real (signed transactions, contract rules,
mining and validation). The expected outcome is declared here and compared with
the obtained one. The result is written as a Markdown table used as evidence in
the delivery (``docs/evidencias/cenarios-de-teste.md``).
"""

# pylint: disable=duplicate-code,line-too-long
from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ecoorigem.blockchain import TX_CALL, TX_DEPLOY, Transaction, Wallet
from ecoorigem.errors import EcoOrigemError
from ecoorigem.node import LedgerNode, LedgerStore

ROOT = Path(__file__).resolve().parents[1]
CONFIRMED = "confirmada"
DOC_HASH = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
OTHER_HASH = "60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f558c11c752"


@dataclass
class Result:
    """One executed scenario."""

    code: str
    category: str
    operation: str
    expected: str
    obtained: str

    @property
    def passed(self) -> bool:
        """Whether the obtained outcome matches the expected one."""
        if self.expected == CONFIRMED:
            return self.obtained.startswith("confirmada no bloco")
        return self.expected == self.obtained

    @property
    def expected_text(self) -> str:
        """Expected outcome as shown in the report."""
        return (
            "confirmada em um novo bloco"
            if self.expected == CONFIRMED
            else self.expected
        )


class Lab:
    """Holds the node, the wallets and the collected results."""

    def __init__(self, directory: Path, difficulty: int) -> None:
        self.node = LedgerNode(LedgerStore(directory), difficulty)
        labels = ["administrador", "produtor", "beneficiador", "transportador"]
        labels += ["distribuidor", "intruso", "distribuidor2"]
        self.w = {name: Wallet.from_seed(name, "cenarios") for name in labels}
        self.results: list[Result] = []

    # -- helpers ---------------------------------------------------------
    def build(
        self, who: str, method: str, args: dict[str, Any], **extra
    ) -> Transaction:
        """Sign a call transaction for ``who``."""
        wallet = self.w[who]
        return Transaction.create(
            wallet,
            TX_CALL,
            method,
            args,
            extra.pop("nonce", self.node.account(wallet.address)["nonce"]),
            to=self.node.contract.address,
            **extra,
        )

    def submit(self, tx: Transaction) -> str:
        """Submit a transaction and describe the outcome in one phrase."""
        try:
            receipt = self.node.submit_transaction(tx.to_dict())
        except EcoOrigemError as error:
            return f"rejeitada ({error.code})"
        return f"confirmada no bloco {receipt['block_index']}"

    def call(self, who: str, method: str, args: dict[str, Any]) -> str:
        """Sign and submit a call."""
        return self.submit(self.build(who, method, args))

    def record(
        self, code: str, category: str, operation: str, expected: str, obtained: str
    ) -> None:
        """Store a scenario result. Block numbers are normalised in the comparison."""
        self.results.append(Result(code, category, operation, expected, obtained))

    def check(self, code, category, operation, expected, action) -> str:
        """Run ``action`` and compare its outcome with ``expected``."""
        obtained = action()
        self.record(code, category, operation, expected, obtained)
        return obtained


def run(lab: Lab) -> None:  # pylint: disable=too-many-statements,too-many-locals
    """Execute every documented scenario."""
    node, w = lab.node, lab.w
    valid, invalid, integrity = (
        "Operação válida",
        "Entrada inválida ou sem permissão",
        "Integridade",
    )
    lot = {
        "product": "Açaí",
        "origin": "Comunidade Ribeirinha do Rio Negro, Novo Airão",
        "quantity_kg": 250.5,
        "harvest_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "document_hash": DOC_HASH,
    }

    # ----------------------------------------------------- valid operations
    deploy = Transaction.create(w["administrador"], TX_DEPLOY, "EcoOrigem", {}, 0)
    lab.check(
        "V01",
        valid,
        "Implantar o contrato com a carteira Administrador",
        "confirmada",
        lambda: lab.submit(deploy),
    )
    for index, (who, role) in enumerate(
        [
            ("produtor", "PRODUCER"),
            ("beneficiador", "PROCESSOR"),
            ("transportador", "CARRIER"),
            ("distribuidor", "DISTRIBUTOR"),
            ("distribuidor2", "DISTRIBUTOR"),
        ],
        start=2,
    ):
        lab.check(
            f"V{index:02d}",
            valid,
            f"Administrador concede o perfil {role} a {who}",
            "confirmada",
            lambda who=who, role=role: lab.call(
                "administrador", "grant_role", {"account": w[who].address, "role": role}
            ),
        )
    lab.check(
        "V07",
        valid,
        "Produtor registra o lote LOT-0001 com hash do documento de origem",
        "confirmada",
        lambda: lab.call("produtor", "register_lot", lot),
    )
    lab.check(
        "V08",
        valid,
        "Beneficiador registra o beneficiamento de LOT-0001",
        "confirmada",
        lambda: lab.call(
            "beneficiador",
            "record_processing",
            {"lot_id": "LOT-0001", "description": "Despolpamento e congelamento."},
        ),
    )
    lab.check(
        "V09",
        valid,
        "Transportador inicia o transporte designando o distribuidor",
        "confirmada",
        lambda: lab.call(
            "transportador",
            "start_transport",
            {
                "lot_id": "LOT-0001",
                "recipient": w["distribuidor"].address,
                "destination": "Centro de distribuição, Manaus",
            },
        ),
    )
    lab.check(
        "V10",
        valid,
        "Distribuidor designado confirma o recebimento",
        "confirmada",
        lambda: lab.call("distribuidor", "confirm_delivery", {"lot_id": "LOT-0001"}),
    )
    lab.check(
        "V11",
        valid,
        "Distribuidor finaliza o lote",
        "confirmada",
        lambda: lab.call("distribuidor", "finalize_lot", {"lot_id": "LOT-0001"}),
    )
    lab.check(
        "V12",
        valid,
        "Consultar LOT-0001: status e histórico completo",
        "FINALIZED com 5 eventos",
        lambda: f"{node.lot('LOT-0001')['status']} com {len(node.lot('LOT-0001')['history'])} eventos",
    )
    lab.call("produtor", "register_lot", {**lot, "document_hash": ""})
    lab.check(
        "V13",
        valid,
        "Responsável anexa documento ao lote LOT-0002",
        "confirmada",
        lambda: lab.call(
            "produtor",
            "attach_document",
            {
                "lot_id": "LOT-0002",
                "document_hash": OTHER_HASH,
                "description": "Certificado orgânico 2026",
            },
        ),
    )
    lab.check(
        "V14",
        valid,
        "Verificar documento com hash correto",
        "registrado",
        lambda: (
            "registrado"
            if node.verify_document("LOT-0002", OTHER_HASH)["registered"]
            else "não registrado"
        ),
    )
    lab.check(
        "V15",
        valid,
        "Validar a cadeia inteira",
        "íntegra",
        lambda: "íntegra" if node.validate().valid else "inválida",
    )
    reopened = LedgerNode(LedgerStore(node.store.directory), node.difficulty)
    lab.check(
        "V16",
        valid,
        "Reiniciar o nó e reconstruir o estado do disco",
        "2 lotes, cadeia íntegra",
        lambda: f"{len(reopened.lots())} lotes, cadeia {'íntegra' if reopened.integrity_ok else 'inválida'}",
    )

    # ---------------------------------------------- invalid and unauthorized
    lab.call(
        "produtor", "register_lot", {**lot, "document_hash": ""}
    )  # LOT-0003 stays REGISTERED
    lab.call(
        "beneficiador",
        "record_processing",
        {"lot_id": "LOT-0002", "description": "Beneficiamento concluído."},
    )
    height = node.status()["height"]
    cases = [
        (
            "I01",
            "Carteira sem perfil tenta registrar lote",
            "rejeitada (ACCESS_DENIED)",
            "intruso",
            "register_lot",
            lot,
        ),
        (
            "I02",
            "Quantidade negativa",
            "rejeitada (INVALID_INPUT)",
            "produtor",
            "register_lot",
            {**lot, "quantity_kg": -5},
        ),
        (
            "I03",
            "Quantidade zero",
            "rejeitada (INVALID_INPUT)",
            "produtor",
            "register_lot",
            {**lot, "quantity_kg": 0},
        ),
        (
            "I04",
            "Data de coleta no futuro",
            "rejeitada (INVALID_INPUT)",
            "produtor",
            "register_lot",
            {
                **lot,
                "harvest_date": (
                    datetime.now(timezone.utc) + timedelta(days=3)
                ).strftime("%Y-%m-%d"),
            },
        ),
        (
            "I05",
            "Produto fora da lista aceita",
            "rejeitada (INVALID_INPUT)",
            "produtor",
            "register_lot",
            {**lot, "product": "Diamante"},
        ),
        (
            "I06",
            "Origem vazia",
            "rejeitada (INVALID_INPUT)",
            "produtor",
            "register_lot",
            {**lot, "origin": ""},
        ),
        (
            "I07",
            "Campo desconhecido no cadastro",
            "rejeitada (INVALID_INPUT)",
            "produtor",
            "register_lot",
            {**lot, "preco": 10},
        ),
        (
            "I08",
            "Finalizar lote CADASTRADO (pular etapas)",
            "rejeitada (INVALID_TRANSITION)",
            "distribuidor",
            "finalize_lot",
            {"lot_id": "LOT-0003"},
        ),
        (
            "I09",
            "Repetir o beneficiamento de lote já beneficiado",
            "rejeitada (INVALID_TRANSITION)",
            "beneficiador",
            "record_processing",
            {"lot_id": "LOT-0002", "description": "Nova tentativa de beneficiamento."},
        ),
        (
            "I10",
            "Beneficiar lote inexistente",
            "rejeitada (LOT_NOT_FOUND)",
            "beneficiador",
            "record_processing",
            {"lot_id": "LOT-0999", "description": "Lote que não existe."},
        ),
        (
            "I11",
            "Identificador de lote em formato inválido",
            "rejeitada (INVALID_INPUT)",
            "beneficiador",
            "record_processing",
            {"lot_id": "lote-1", "description": "Formato incorreto."},
        ),
        (
            "I12",
            "Alterar lote FINALIZADO (reprocessar)",
            "rejeitada (LOT_FINALIZED)",
            "beneficiador",
            "record_processing",
            {"lot_id": "LOT-0001", "description": "Reprocessar lote encerrado."},
        ),
        (
            "I13",
            "Anexar documento a lote FINALIZADO",
            "rejeitada (LOT_FINALIZED)",
            "distribuidor",
            "attach_document",
            {
                "lot_id": "LOT-0001",
                "document_hash": OTHER_HASH,
                "description": "Documento tardio",
            },
        ),
        (
            "I14",
            "Produtor tenta conceder perfil (não é administrador)",
            "rejeitada (ACCESS_DENIED)",
            "produtor",
            "grant_role",
            {"account": w["intruso"].address, "role": "CARRIER"},
        ),
        (
            "I15",
            "Conceder perfil já existente",
            "rejeitada (INVALID_INPUT)",
            "administrador",
            "grant_role",
            {"account": w["produtor"].address, "role": "PRODUCER"},
        ),
        (
            "I16",
            "Destinatário do transporte sem perfil Distribuidor",
            "rejeitada (INVALID_INPUT)",
            "transportador",
            "start_transport",
            {
                "lot_id": "LOT-0002",
                "recipient": w["intruso"].address,
                "destination": "Manaus",
            },
        ),
        (
            "I17",
            "Método inexistente no contrato",
            "rejeitada (UNKNOWN_METHOD)",
            "administrador",
            "selfdestruct",
            {},
        ),
        (
            "I18",
            "Anexar documento sem ser o responsável atual",
            "rejeitada (ACCESS_DENIED)",
            "beneficiador",
            "attach_document",
            {
                "lot_id": "LOT-0003",
                "document_hash": OTHER_HASH,
                "description": "Documento indevido",
            },
        ),
    ]
    for code, description, expected, who, method, args in cases:
        lab.check(
            code,
            invalid,
            description,
            expected,
            lambda who=who, method=method, args=args: lab.call(who, method, args),
        )

    lab.check(
        "I19",
        invalid,
        "Nenhum bloco foi criado pelas 18 operações rejeitadas",
        "0 blocos novos",
        lambda: f"{node.status()['height'] - height} blocos novos",
    )
    # Designated distributor rule needs a lot in transit: move LOT-0003 forward.
    lab.call(
        "beneficiador",
        "record_processing",
        {"lot_id": "LOT-0003", "description": "Beneficiamento concluído."},
    )
    lab.call(
        "transportador",
        "start_transport",
        {
            "lot_id": "LOT-0003",
            "recipient": w["distribuidor"].address,
            "destination": "Manaus",
        },
    )
    lab.check(
        "I20",
        invalid,
        "Outro distribuidor tenta confirmar o recebimento",
        "rejeitada (ACCESS_DENIED)",
        lambda: lab.call("distribuidor2", "confirm_delivery", {"lot_id": "LOT-0003"}),
    )

    forged = lab.build("intruso", "register_lot", lot)
    forged = replace(forged, sender=w["produtor"].address)
    lab.check(
        "I21",
        invalid,
        "Transação com remetente falsificado",
        "rejeitada (INVALID_SIGNATURE)",
        lambda: lab.submit(forged),
    )
    tampered = replace(
        lab.build("produtor", "register_lot", lot), args={**lot, "quantity_kg": 99999}
    )
    lab.check(
        "I22",
        invalid,
        "Transação alterada depois de assinada",
        "rejeitada (INVALID_SIGNATURE)",
        lambda: lab.submit(tampered),
    )
    first = lab.build("produtor", "register_lot", {**lot, "origin": "Coari, Amazonas"})
    lab.submit(first)
    lab.check(
        "I23",
        invalid,
        "Reenvio da mesma transação (replay)",
        "rejeitada (DUPLICATE_TRANSACTION)",
        lambda: lab.submit(first),
    )
    lab.check(
        "I24",
        invalid,
        "Nonce fora de sequência",
        "rejeitada (NONCE_MISMATCH)",
        lambda: lab.submit(lab.build("produtor", "register_lot", lot, nonce=77)),
    )
    lab.check(
        "I25",
        invalid,
        "Transação com data muito antiga",
        "rejeitada (TIMESTAMP_OUT_OF_RANGE)",
        lambda: lab.submit(
            lab.build(
                "produtor", "register_lot", lot, timestamp=node.clock() - 3_600_000
            )
        ),
    )
    redeploy = Transaction.create(w["intruso"], TX_DEPLOY, "EcoOrigem", {}, 0)
    lab.check(
        "I26",
        invalid,
        "Reimplantar o contrato",
        "rejeitada (CONTRACT_ALREADY_DEPLOYED)",
        lambda: lab.submit(redeploy),
    )
    lab.check(
        "I27",
        invalid,
        "Verificar arquivo alterado (hash diferente)",
        "não registrado",
        lambda: (
            "registrado"
            if node.verify_document("LOT-0002", DOC_HASH[::-1])["registered"]
            else "não registrado"
        ),
    )

    # ------------------------------------------------------------ integrity
    block = node.status()["height"] - 1
    report = node.lab_tamper(block, {"quantity_kg": 9999})
    lab.check(
        "A01",
        integrity,
        f"Alterar dado gravado no bloco {block} (sem refazer hashes)",
        "inválida a partir do bloco " + str(block),
        lambda: (
            ("inválida a partir do bloco " + str(report.first_invalid_block))
            if not report.valid
            else "íntegra"
        ),
    )
    lab.check(
        "A02",
        integrity,
        "Nova operação com a cadeia comprometida",
        "rejeitada (CHAIN_COMPROMISED)",
        lambda: lab.call("produtor", "register_lot", lot),
    )
    node.lab_restore()
    report = node.lab_tamper(block - 1, {"quantity_kg": 9999}, remine=True)
    codes = {issue.code for issue in report.issues}
    lab.check(
        "A03",
        integrity,
        f"Alterar o bloco {block - 1} e refazer a prova de trabalho dele",
        "encadeamento quebrado (BROKEN_LINK)",
        lambda: (
            "encadeamento quebrado (BROKEN_LINK)"
            if "BROKEN_LINK" in codes
            else "não detectado"
        ),
    )
    lab.check(
        "A04",
        integrity,
        "Restaurar a cadeia a partir do disco",
        "íntegra",
        lambda: "íntegra" if node.lab_restore().valid else "inválida",
    )
    lab.check(
        "A05",
        integrity,
        "Operação volta a ser aceita após a restauração",
        "confirmada",
        lambda: lab.call(
            "produtor", "register_lot", {**lot, "origin": "Parintins, Amazonas"}
        ),
    )


def to_markdown(results: list[Result], difficulty: int) -> str:
    """Render the results as the evidence document."""
    passed = sum(1 for r in results if r.passed)
    lines = [
        "# Cenários de teste: operações realizadas, resultados esperados e obtidos",
        "",
        f"Execução automatizada em {datetime.now().strftime('%d/%m/%Y %H:%M')} contra uma blockchain local nova "
        f"(dificuldade {difficulty}). Cada linha é uma operação real, assinada e enviada ao nó.",
        "",
        f"**Resultado: {passed} de {len(results)} cenários conforme o esperado.**",
        "",
        "Reprodução: `make scenarios`.",
    ]
    category = ""
    for r in results:
        if r.category != category:
            category = r.category
            lines += [
                "",
                f"## {category}",
                "",
                "| ID | Operação realizada | Resultado esperado | Resultado obtido | Status |",
                "| --- | --- | --- | --- | --- |",
            ]
        lines.append(
            f"| {r.code} | {r.operation} | {r.expected_text} | {r.obtained} | {'Aprovado' if r.passed else 'FALHOU'} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    """Run the scenarios and write the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--difficulty", type=int, default=4)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "evidencias" / "cenarios-de-teste.md",
    )
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        lab = Lab(Path(directory), args.difficulty)
        run(lab)
    failed = [r for r in lab.results if not r.passed]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(to_markdown(lab.results, args.difficulty), encoding="utf-8")
    print(
        f"{len(lab.results) - len(failed)}/{len(lab.results)} cenários conforme o esperado. Relatório: {args.output}"
    )
    for r in failed:
        print(f"  FALHOU {r.code}: esperado {r.expected!r}, obtido {r.obtained!r}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
