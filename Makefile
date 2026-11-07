# EcoOrigem - automações da dApp Ethereum.

NODE        ?= node
NPM         ?= npm
PYTHON      ?= python3
PORT        ?= 8000
DOCS_VENV   ?= .venv-docs
DOCS_PY     := $(DOCS_VENV)/bin/python

ifdef NO_COLOR
C_OK :=
C_STEP :=
C_WARN :=
C_RESET :=
else
C_OK := \033[1;32m
C_STEP := \033[1;36m
C_WARN := \033[1;33m
C_RESET := \033[0m
endif

.DEFAULT_GOAL := help

.PHONY: help menu install compile abi configure test validate security check serve slides clean

help: ## Lista os comandos disponíveis
	@printf "$(C_OK)EcoOrigem - dApp Ethereum Sepolia$(C_RESET)\n\n"
	@printf "Uso: make <comando>\n\n"
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

menu: ## Abre um menu interativo com as tarefas do projeto
	@bash scripts/menu.sh

install: ## Instala exatamente as dependências registradas no lockfile
	$(NPM) ci

compile: ## Compila contracts/EcoOrigem.sol com Solidity 0.8.34
	$(NPM) run compile

abi: ## Compila o contrato e sincroniza a ABI do frontend
	$(NPM) run sync:abi

configure: ## Registra o deploy. Uso: make configure ADDRESS=0x... BLOCK=123 TX=0x...
	@test -n "$(ADDRESS)" -a -n "$(BLOCK)" -a -n "$(TX)" || { printf "$(C_WARN)Informe ADDRESS, BLOCK e TX.$(C_RESET)\n"; exit 1; }
	$(NPM) run configure:contract -- "$(ADDRESS)" "$(BLOCK)" "$(TX)"

test: ## Executa contrato em blockchain local e testes do frontend
	$(NPM) test

validate: ## Valida os arquivos exigidos para a publicação estática
	$(NPM) run build

security: ## Audita e separa as ferramentas locais do frontend publicado
	$(NPM) run security

check: ## Compila, sincroniza ABI, valida e testa todos os fluxos automatizados
	$(NPM) run check

serve: ## Serve o frontend em http://127.0.0.1:8000 (altere com PORT=...)
	@printf "$(C_STEP)Abra http://127.0.0.1:$(PORT) em um navegador com MetaMask.$(C_RESET)\n"
	$(PYTHON) -m http.server $(PORT) --directory frontend --bind 127.0.0.1

$(DOCS_PY):
	$(PYTHON) -m venv $(DOCS_VENV)
	$(DOCS_PY) -m pip install --quiet --upgrade pip
	$(DOCS_PY) -m pip install --quiet -r requirements-docs.txt

slides: $(DOCS_PY) ## Atualiza PPTX e PDF usando o design da Entrega 1
	$(DOCS_PY) scripts/build_slides.py

clean: ## Remove artefatos reproduzíveis e caches locais
	rm -rf build node_modules $(DOCS_VENV)
