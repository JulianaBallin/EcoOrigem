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
# Logs coloridos no nó e na interface (use LOG_COLOR=0 ou NO_COLOR=1 para desativar).
LOG_COLOR   ?= 1

ifdef NO_COLOR
C_OK :=
C_BAD :=
C_STEP :=
C_DIM :=
C_RESET :=
else
C_OK    := \033[1;32m
C_BAD   := \033[1;31m
C_STEP  := \033[1;36m
C_DIM   := \033[2m
C_RESET := \033[0m
endif

.DEFAULT_GOAL := help

.PHONY: report slides diagrams help menu venv install shell test coverage lint format format-check security check scenarios docs-deps demo-video \
        node deploy app seed accounts status validate start stop reset demo logs \
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
	$(VENV_PY) -m pylint ecoorigem tests scripts

format: venv ## Formata o código com Black
	$(VENV_PY) -m black ecoorigem tests scripts

format-check: venv ## Confere a formatação com Black sem alterar arquivos
	$(VENV_PY) -m black --check ecoorigem tests scripts

security: venv ## Executa Bandit e pip-audit (Black Duck não está disponível neste ambiente)
	$(VENV_PY) -m bandit -q -r ecoorigem
	$(VENV_PY) -m pip_audit -r requirements.txt

check: format-check lint test security ## Executa formatação, lint, testes e segurança

scenarios: venv ## Executa os cenários documentados e gera docs/evidencias/cenarios-de-teste.md
	PYTHONPATH=. $(VENV_PY) scripts/run_scenarios.py

docs-deps: venv ## Instala as ferramentas de evidência (Playwright, Pillow, python-docx)
	$(VENV_PY) -m pip install --quiet -r requirements-docs.txt
	$(VENV_PY) -m playwright install ffmpeg

report: docs-deps ## Gera o relatório técnico (DOCX e PDF) em docs/
	$(VENV_PY) scripts/build_report.py

slides: report ## Gera a apresentação (PPTX e PDF) em docs/
	$(VENV_PY) scripts/build_slides.py

diagrams: docs-deps ## Regera os diagramas em docs/assets/diagramas
	$(VENV_PY) scripts/build_diagrams.py

demo-video: docs-deps ## Grava screenshots e o vídeo de apoio com a stack Docker no ar
	$(VENV_PY) scripts/record_demo.py

## --------------------------------------------- blockchain local (sem Docker)
node: venv ## 1) Inicia a blockchain local (porta 8545)
	ECOORIGEM_LOG_COLOR=$(LOG_COLOR) $(VENV_PY) -m ecoorigem node

deploy: venv ## 2) Implanta o contrato e concede os perfis de demonstração
	$(VENV_PY) -m ecoorigem deploy --wait 10

app: venv ## 3) Inicia a interface web (http://127.0.0.1:5000)
	ECOORIGEM_LOG_COLOR=$(LOG_COLOR) $(VENV_PY) -m ecoorigem web

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
		ECOORIGEM_LOG_COLOR=$(LOG_COLOR) nohup $(VENV_PY) -m ecoorigem node > $(LOG_DIR)/node.log 2>&1 & echo $$! > $(RUN_DIR)/node.pid; \
	fi
	@$(VENV_PY) -m ecoorigem deploy --wait 20
	@if [ -f $(RUN_DIR)/web.pid ] && kill -0 $$(cat $(RUN_DIR)/web.pid) 2>/dev/null; then \
		echo "A interface já está em execução."; \
	else \
		ECOORIGEM_LOG_COLOR=$(LOG_COLOR) nohup $(VENV_PY) -m ecoorigem web > $(LOG_DIR)/web.log 2>&1 & echo $$! > $(RUN_DIR)/web.pid; \
	fi
	@sleep 1
	@printf "$(C_OK)Interface: http://127.0.0.1:5000   Nó: http://127.0.0.1:8545   Logs: make logs$(C_RESET)\n"

stop: ## Encerra o nó e a interface iniciados com make start
	@for name in web node; do \
		if [ -f $(RUN_DIR)/$$name.pid ]; then \
			kill $$(cat $(RUN_DIR)/$$name.pid) 2>/dev/null && echo "Encerrado: $$name" || true; \
			rm -f $(RUN_DIR)/$$name.pid; \
		fi; \
	done

demo: venv ## Sobe a demonstração do zero: limpa dados, inicia nó, contrato, interface e lotes
	@printf "$(C_STEP)[1/5] Encerrando execuções anteriores$(C_RESET)\n"
	@$(MAKE) --no-print-directory stop
	@printf "$(C_STEP)[2/5] Limpando a cadeia e as carteiras locais$(C_RESET)\n"
	@$(VENV_PY) -m ecoorigem reset --yes
	@printf "$(C_STEP)[3/5] Iniciando a blockchain, implantando o contrato e subindo a interface$(C_RESET)\n"
	@$(MAKE) --no-print-directory start
	@printf "$(C_STEP)[4/5] Criando lotes de demonstração$(C_RESET)\n"
	@$(VENV_PY) -m ecoorigem seed --wait 10
	@printf "$(C_STEP)[5/5] Verificando a integridade da cadeia$(C_RESET)\n"
	@$(VENV_PY) -m ecoorigem validate --wait 3 \
		&& printf "$(C_OK)Demonstração pronta. Abra http://127.0.0.1:5000 e rode make logs em outro terminal.$(C_RESET)\n" \
		|| { printf "$(C_BAD)Falha na verificação da cadeia. Veja make logs.$(C_RESET)\n"; exit 1; }

logs: ## Acompanha os logs coloridos do nó e da interface (Ctrl+C para sair)
	@mkdir -p $(LOG_DIR) && touch $(LOG_DIR)/node.log $(LOG_DIR)/web.log
	@printf "$(C_DIM)Verde: bloco confirmado. Vermelho: operação rejeitada. Amarelo: alerta de integridade.$(C_RESET)\n"
	@tail -n 20 -F $(LOG_DIR)/node.log $(LOG_DIR)/web.log

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
