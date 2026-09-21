#!/usr/bin/env bash
# Menu interativo do EcoOrigem. Cada opção chama um alvo do Makefile.
set -u
cd "$(dirname "$0")/.."

BOLD=$'\033[1m'; GREEN=$'\033[32m'; DIM=$'\033[2m'; RESET=$'\033[0m'

OPTIONS=(
  "venv|Ambiente|Cria o ambiente virtual .venv-ecoorigem e instala as dependências"
  "shell|Ambiente|Abre um shell com o ambiente virtual ativado"
  "start|Execução local|Inicia nó, implanta o contrato e sobe a interface em segundo plano"
  "node|Execução local|1) Inicia somente a blockchain local (terminal dedicado, porta 8545)"
  "deploy|Execução local|2) Implanta o contrato e concede os perfis de demonstração"
  "app|Execução local|3) Inicia somente a interface web (terminal dedicado, porta 5000)"
  "seed|Execução local|Cria lotes de demonstração em várias etapas"
  "status|Execução local|Mostra o estado do nó (blocos, contrato, integridade)"
  "validate|Execução local|Verifica a integridade da cadeia em execução"
  "stop|Execução local|Encerra nó e interface iniciados por 'start'"
  "reset|Execução local|Apaga cadeia e carteiras locais (recomeça do zero)"
  "docker-up|Docker|Sobe toda a stack com Docker (nó, implantação, interface)"
  "docker-seed|Docker|Cria lotes de demonstração na stack Docker"
  "docker-logs|Docker|Acompanha os logs dos contêineres (Ctrl+C para sair)"
  "docker-down|Docker|Derruba os contêineres mantendo os dados"
  "docker-reset|Docker|Derruba tudo e apaga os volumes"
  "docker-test|Docker|Executa os testes dentro de um contêiner"
  "test|Qualidade|Executa os testes automatizados"
  "coverage|Qualidade|Executa os testes com cobertura"
  "lint|Qualidade|Executa o Pylint"
  "format|Qualidade|Formata o código com Black"
  "security|Qualidade|Executa Bandit e pip-audit"
  "check|Qualidade|Executa formatação, lint, testes e segurança"
  "scenarios|Evidências|Executa os cenários documentados e gera o relatório de resultados"
  "demo-video|Evidências|Grava screenshots e o vídeo de apoio (stack Docker precisa estar no ar)"
)

show_menu() {
  clear 2>/dev/null || true
  echo "${BOLD}${GREEN}EcoOrigem${RESET}${BOLD} - rastreabilidade com blockchain local${RESET}"
  echo "${DIM}Interface: http://127.0.0.1:5000   Nó: http://127.0.0.1:8545${RESET}"
  local group="" i=1 entry target grp desc
  for entry in "${OPTIONS[@]}"; do
    IFS='|' read -r target grp desc <<<"$entry"
    if [[ "$grp" != "$group" ]]; then
      echo; echo "${BOLD}${grp}${RESET}"; group="$grp"
    fi
    printf "  %2d) %-13s %s\n" "$i" "$target" "$desc"
    i=$((i + 1))
  done
  echo; echo "   0) sair"; echo
}

while true; do
  show_menu
  read -r -p "Escolha uma opção: " choice || exit 0
  if [[ "$choice" == "0" || "$choice" == "q" ]]; then exit 0; fi
  if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#OPTIONS[@]} )); then
    IFS='|' read -r target _ _ <<<"${OPTIONS[$((choice - 1))]}"
    echo; echo "${BOLD}> make ${target}${RESET}"; echo
    make --no-print-directory "$target"
    echo; read -r -p "Pressione Enter para voltar ao menu..." _ || exit 0
  else
    echo "Opção inválida."; sleep 1
  fi
done
