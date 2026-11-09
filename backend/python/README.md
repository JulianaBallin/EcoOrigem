# Implementação didática da Primeira Entrega

Esta camada preserva a blockchain local em Python que fundamentou o EcoOrigem. Ela continua executável e cobre blocos, prova de trabalho, raiz de Merkle, carteiras Ed25519, contrato didático, nó HTTP e interface web.

Ela não participa do deploy da Entrega 2 na Vercel. O contrato atual está em `backend/contracts/EcoOrigem.sol` e o frontend atual está em `frontend/`.

## Estrutura

| Diretório ou arquivo | Responsabilidade |
| --- | --- |
| `ecoorigem/blockchain/` | Blocos, cadeia, transações, hashes, Merkle e carteiras |
| `ecoorigem/contract/` | Regras de rastreabilidade da implementação local |
| `ecoorigem/node/` | Persistência, mineração e API do nó |
| `ecoorigem/web/` | Aplicação Flask da demonstração local |
| `assets/` | CSS, JavaScript e imagens usados pela aplicação Flask |
| `tests/` | Testes unitários, de integração, HTTP e interface |
| `scripts/run_scenarios.py` | Executa 48 cenários válidos, inválidos e de integridade |
| `Dockerfile` e `docker-compose.yml` | Execução isolada do nó, deploy, interface e testes |

## Preparar o ambiente

Execute a partir da raiz do repositório:

```bash
python3 -m venv .venv-ecoorigem
.venv-ecoorigem/bin/python -m pip install -r backend/python/requirements-dev.txt
```

O ambiente virtual é local e ignorado pelo Git.

## Executar os testes

```bash
cd backend/python
../../.venv-ecoorigem/bin/python -m pytest -q
```

## Simular todos os cenários

```bash
cd backend/python
../../.venv-ecoorigem/bin/python scripts/run_scenarios.py --difficulty 2
```

O resultado é gravado em `backend/python/data/cenarios-de-teste.md`. Esse diretório é gerado localmente e ignorado pelo Git.

## Executar com Docker

O Compose lê automaticamente `backend/python/.env` quando o comando é executado nessa pasta. Comece pelo exemplo sem credenciais:

```bash
cd backend/python
cp .env.example .env
docker compose config
docker compose up --build
```

O arquivo `.env` nunca deve ser versionado. O Compose contém somente nomes de variáveis e valores locais não sensíveis. Senhas, tokens e chaves privadas não pertencem ao arquivo YAML.
