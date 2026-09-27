"""Command line interface: ``python -m ecoorigem <command>``."""

from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import sys
from typing import Sequence

from werkzeug.serving import make_server

from ecoorigem import __version__
from ecoorigem.bootstrap import (
    build_node,
    build_web,
    deploy_contract,
    grant_demo_roles,
    seed_demo_lots,
    wait_for_node,
)
from ecoorigem.client import NodeClient
from ecoorigem.config import Settings
from ecoorigem.errors import EcoOrigemError
from ecoorigem.keystore import Keystore
from ecoorigem.node.storage import StorageError


def _print(message: str) -> None:
    print(message, flush=True)


def _serve(app, host: str, port: int, label: str) -> None:  # pragma: no cover
    server = make_server(host, port, app, threaded=True)
    _print(f"{label} em execução em http://{host}:{port} (Ctrl+C para encerrar)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _print(f"{label} encerrado.")


def cmd_node(settings: Settings, args: argparse.Namespace) -> int:
    """Start the local blockchain node."""
    if args.difficulty is not None:
        settings = dataclasses.replace(settings, difficulty=args.difficulty)
    if args.manual_mining:
        settings = dataclasses.replace(settings, auto_mine=False)
    node, app = build_node(settings)
    status = node.status()
    _print(
        f"Blockchain local iniciada: {status['height']} bloco(s), "
        f"dificuldade {status['difficulty']}, mineração "
        f"{'automática' if node.auto_mine else 'manual'}."
    )
    if not status["integrity"]["valid"]:
        _print(
            "ATENÇÃO: a verificação de integridade falhou. "
            "Operações de escrita bloqueadas."
        )
    _serve(app, args.host or settings.node_host, args.port or settings.node_port, "Nó")
    return 0


def cmd_web(settings: Settings, args: argparse.Namespace) -> int:
    """Start the web application."""
    if args.node_url:
        settings = dataclasses.replace(settings, node_url=args.node_url)
    app = build_web(settings)
    _serve(
        app, args.host or settings.web_host, args.port or settings.web_port, "Aplicação"
    )
    return 0


def _client(settings: Settings, wait: float) -> NodeClient:
    client = NodeClient.from_url(settings.node_url)
    wait_for_node(client, wait)
    return client


def cmd_deploy(settings: Settings, args: argparse.Namespace) -> int:
    """Deploy the contract and grant the demo roles."""
    keystore = Keystore.load_or_create(settings.keystore_path, settings.demo_seed)
    client = _client(settings, args.wait)
    result = deploy_contract(client, keystore)
    contract = result["contract"]
    if result["deployed_now"]:
        _print(f"Contrato implantado no bloco {result['receipt']['block_index']}.")
    else:
        _print("O contrato já estava implantado. Nenhuma alteração feita.")
    _print(f"Endereço do contrato: {contract['address']}")
    _print(f"Administrador: {contract['admin']}")
    if not args.no_roles:
        granted = grant_demo_roles(client, keystore)
        _print(
            "Perfis concedidos: " + ", ".join(granted)
            if granted
            else "Todos os perfis de demonstração já estavam concedidos."
        )
    return 0


def cmd_seed(settings: Settings, args: argparse.Namespace) -> int:
    """Create sample lots in several stages."""
    keystore = Keystore.load_or_create(settings.keystore_path, settings.demo_seed)
    client = _client(settings, args.wait)
    created = seed_demo_lots(client, keystore)
    _print("Lotes de demonstração criados: " + ", ".join(created))
    return 0


def cmd_accounts(settings: Settings, _args: argparse.Namespace) -> int:
    """List the demonstration wallets (public data only)."""
    keystore = Keystore.load_or_create(settings.keystore_path, settings.demo_seed)
    for wallet in keystore.wallets():
        _print(f"{wallet.label:<15} {wallet.address}")
    return 0


def cmd_status(settings: Settings, args: argparse.Namespace) -> int:
    """Print the node status as JSON."""
    client = _client(settings, args.wait)
    _print(json.dumps(client.status(), indent=2, ensure_ascii=False))
    return 0


def cmd_validate(settings: Settings, args: argparse.Namespace) -> int:
    """Run the integrity check on the running node."""
    client = _client(settings, args.wait)
    report = client.request("GET", "/validate")
    if report["valid"]:
        _print(f"Blockchain íntegra: {report['checked_blocks']} bloco(s) verificados.")
        return 0
    _print(f"Blockchain INVÁLIDA a partir do bloco {report['first_invalid_block']}:")
    for issue in report["issues"]:
        _print(f"  bloco {issue['block_index']}: {issue['code']} - {issue['message']}")
    return 2


def cmd_reset(settings: Settings, args: argparse.Namespace) -> int:
    """Delete the local chain and wallets. The node must be stopped."""
    targets = [settings.node_dir, settings.keystore_path.parent]
    if not args.yes:
        _print("Serão removidos: " + ", ".join(str(target) for target in targets))
        if input("Confirmar (digite 'sim'): ").strip().lower() != "sim":
            _print("Operação cancelada.")
            return 1
    for target in targets:
        shutil.rmtree(target, ignore_errors=True)
    _print("Dados locais removidos. Inicie o nó e implante o contrato novamente.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ecoorigem", description="EcoOrigem: rastreabilidade com blockchain local."
    )
    parser.add_argument(
        "--version", action="version", version=f"ecoorigem {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    node = sub.add_parser("node", help="inicia a blockchain local")
    node.add_argument("--host")
    node.add_argument("--port", type=int)
    node.add_argument("--difficulty", type=int, help="zeros iniciais exigidos no hash")
    node.add_argument(
        "--manual-mining", action="store_true", help="agrupa transações até POST /mine"
    )
    node.set_defaults(handler=cmd_node)

    web = sub.add_parser("web", help="inicia a interface web")
    web.add_argument("--host")
    web.add_argument("--port", type=int)
    web.add_argument("--node-url")
    web.set_defaults(handler=cmd_web)

    deploy = sub.add_parser(
        "deploy", help="implanta o contrato e concede os perfis de demonstração"
    )
    deploy.add_argument(
        "--wait", type=float, default=0, help="segundos de espera pelo nó"
    )
    deploy.add_argument("--no-roles", action="store_true", help="não concede perfis")
    deploy.set_defaults(handler=cmd_deploy)

    seed = sub.add_parser("seed", help="cria lotes de demonstração")
    seed.add_argument("--wait", type=float, default=0)
    seed.set_defaults(handler=cmd_seed)

    accounts = sub.add_parser("accounts", help="lista as carteiras de demonstração")
    accounts.set_defaults(handler=cmd_accounts)

    status = sub.add_parser("status", help="mostra o estado do nó")
    status.add_argument("--wait", type=float, default=0)
    status.set_defaults(handler=cmd_status)

    validate = sub.add_parser("validate", help="verifica a integridade da cadeia")
    validate.add_argument("--wait", type=float, default=0)
    validate.set_defaults(handler=cmd_validate)

    reset = sub.add_parser("reset", help="apaga cadeia e carteiras locais")
    reset.add_argument("--yes", action="store_true", help="não pedir confirmação")
    reset.set_defaults(handler=cmd_reset)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point."""
    args = build_parser().parse_args(argv)
    try:
        return args.handler(Settings.from_env(), args)
    except (EcoOrigemError, StorageError) as error:
        _print(f"Erro: {error.message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
