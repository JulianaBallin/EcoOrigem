# EcoOrigem - comandos principais do projeto.
# Use "make menu" para um menu interativo ou "make help" para a lista de comandos.

VENV        ?= .venv-ecoorigem
PYTHON      ?= python3
VENV_PY     := $(VENV)/bin/python
STAMP       := $(VENV)/.installed
DATA_DIR    ?= data
RUN_DIR     := $(DATA_DIR)/run
LOG_DIR     := $(DATA_DIR)/logs
COMPOSE     ?= docker compose
export ECOORIGEM_DATA_DIR ?= $(DATA_DIR)

.DEFAULT_GOAL := help

.PHONY: help menu venv install shell test coverage lint format format-check security check \
        node deploy app seed accounts status validate start stop reset \
        docker-build docker-up docker-down docker-logs docker-seed docker-test docker-reset docker-status \
        clean

## ---------------------------------------------------------------- ajuda
help: ## Lista os comandos disponíveis
	@echo "EcoOrigem - rastreabilidade com blockchain local"
	@echo
	@echo "Uso: make <comando>   (ou make menu para o menu interativo)"
	@echo
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

menu: ## Abre o menu interativo com todas as opções explicadas
	@bash scripts/menu.sh

## ------------------------------------------------------ ambiente virtual
$(VENV_PY):
	$(PYTHON) -m venv $(VENV)

$(STAMP): $(VENV_PY) requirements-dev.txt
	$(VENV_PY) -m pip install --quiet --upgrade pip
	$(VENV_PY) -m pip install --quiet -r requirements-dev.txt
	@touch $(STAMP)

venv: $(STAMP) ## Cria o ambiente virtual .venv-ecoorigem e instala as dependências
	@echo "Ambiente virtual pronto em $(VENV). Para ativar no terminal: source $(VENV)/bin/activate"

install: venv ## Alias de venv

shell: venv ## Abre um shell com o ambiente virtual ativado
	@echo "Ambiente virtual ativado. Digite exit para sair."
	@bash --rcfile <(echo '[ -f ~/.bashrc ] && . ~/.bashrc; . $(VENV)/bin/activate') -i

## ---------------------------------------------------- qualidade e testes
test: venv ## Executa os testes automatizados
	$(VENV_PY) -m pytest -q

coverage: venv ## Executa os testes com relatório de cobertura
	$(VENV_PY) -m pytest -q --cov --cov-report=term-missing

lint: venv ## Executa o Pylint
	$(VENV_PY) -m pylint ecoorigem tests

format: venv ## Formata o código com Black
	$(VENV_PY) -m black ecoorigem tests

format-check: venv ## Confere a formatação com Black sem alterar arquivos
	$(VENV_PY) -m black --check ecoorigem tests

security: venv ## Executa Bandit e pip-audit (Black Duck não está disponível neste ambiente)
	$(VENV_PY) -m bandit -q -r ecoorigem
	$(VENV_PY) -m pip_audit -r requirements.txt

check: format-check lint test security ## Executa formatação, lint, testes e segurança

## --------------------------------------------- blockchain local (sem Docker)
node: venv ## 1) Inicia a blockchain local (porta 8545)
	$(VENV_PY) -m ecoorigem node

deploy: venv ## 2) Implanta o contrato e concede os perfis de demonstração
	$(VENV_PY) -m ecoorigem deploy --wait 10

app: venv ## 3) Inicia a interface web (http://127.0.0.1:5000)
	$(VENV_PY) -m ecoorigem web

seed: venv ## Cria lotes de demonstração em várias etapas
	$(VENV_PY) -m ecoorigem seed --wait 10

accounts: venv ## Lista as carteiras de demonstração (somente endereços)
	$(VENV_PY) -m ecoorigem accounts

status: venv ## Mostra o estado do nó
	$(VENV_PY) -m ecoorigem status --wait 3

validate: venv ## Verifica a integridade da cadeia no nó em execução
	$(VENV_PY) -m ecoorigem validate --wait 3

start: venv ## Inicia nó, implanta o contrato e sobe a interface em segundo plano
	@mkdir -p $(RUN_DIR) $(LOG_DIR)
	@if [ -f $(RUN_DIR)/node.pid ] && kill -0 $$(cat $(RUN_DIR)/node.pid) 2>/dev/null; then \
		echo "O nó já está em execução."; \
	else \
		nohup $(VENV_PY) -m ecoorigem node > $(LOG_DIR)/node.log 2>&1 & echo $$! > $(RUN_DIR)/node.pid; \
	fi
	@$(VENV_PY) -m ecoorigem deploy --wait 20
	@if [ -f $(RUN_DIR)/web.pid ] && kill -0 $$(cat $(RUN_DIR)/web.pid) 2>/dev/null; then \
		echo "A interface já está em execução."; \
	else \
		nohup $(VENV_PY) -m ecoorigem web > $(LOG_DIR)/web.log 2>&1 & echo $$! > $(RUN_DIR)/web.pid; \
	fi
	@sleep 1
	@echo "Interface: http://127.0.0.1:5000   Nó: http://127.0.0.1:8545   Logs: $(LOG_DIR)/"

stop: ## Encerra o nó e a interface iniciados com make start
	@for name in web node; do \
		if [ -f $(RUN_DIR)/$$name.pid ]; then \
			kill $$(cat $(RUN_DIR)/$$name.pid) 2>/dev/null && echo "Encerrado: $$name" || true; \
			rm -f $(RUN_DIR)/$$name.pid; \
		fi; \
	done

reset: venv ## Apaga a cadeia e as carteiras locais (encerre o nó antes)
	@$(MAKE) --no-print-directory stop
	$(VENV_PY) -m ecoorigem reset

## ------------------------------------------------------------------ Docker
docker-build: ## Constrói as imagens Docker
	$(COMPOSE) build

docker-up: ## Sobe nó, implantação do contrato e interface com Docker
	$(COMPOSE) up -d --build
	@echo "Interface: http://127.0.0.1:5000   Nó: http://127.0.0.1:8545"

docker-down: ## Derruba os contêineres (mantém a blockchain nos volumes)
	$(COMPOSE) down

docker-logs: ## Acompanha os logs dos serviços
	$(COMPOSE) logs -f --tail=100

docker-status: ## Mostra o estado dos contêineres
	$(COMPOSE) ps

docker-seed: ## Cria lotes de demonstração na stack Docker
	$(COMPOSE) --profile seed run --rm seed

docker-test: ## Executa os testes dentro de um contêiner
	$(COMPOSE) --profile test run --rm --build tests

docker-reset: ## Derruba tudo e apaga os volumes (blockchain e carteiras)
	$(COMPOSE) --profile seed --profile test down -v

clean: ## Remove caches locais de teste e compilação
	rm -rf .pytest_cache .coverage htmlcov
	find . -name __pycache__ -type d -not -path "./$(VENV)/*" -prune -exec rm -rf {} +
