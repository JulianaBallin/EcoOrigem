#!/usr/bin/env bash
set -euo pipefail

while true; do
  printf '\nEcoOrigem - dApp Ethereum Sepolia\n'
  printf '  1) Instalar dependências\n'
  printf '  2) Compilar contrato e atualizar ABI\n'
  printf '  3) Executar todos os testes\n'
  printf '  4) Validar contrato, frontend e segurança\n'
  printf '  5) Servir o frontend localmente\n'
  printf '  6) Gerar apresentação\n'
  printf '  0) Sair\n'
  read -r -p 'Escolha: ' option

  case "$option" in
    1) make install ;;
    2) make abi ;;
    3) make test ;;
    4) make check && make security ;;
    5) make serve ;;
    6) make slides ;;
    0) exit 0 ;;
    *) printf 'Opção inválida.\n' ;;
  esac
done
