# Demonstração local (4 min)

## Antes da apresentação

```bash
cd entrega-1/EcoOrigem
make venv                     # ambiente virtual .venv-ecoorigem
make test                     # testes devem passar
```

Deixar dois terminais abertos na pasta do projeto e o navegador pronto.

## Roteiro

| Tempo | Requisito | Ação | Mostrar |
| --- | --- | --- | --- |
| 0:00 | Inicialização | Terminal 1: `make demo` | Etapas 1 a 5 em ciano: limpa dados, inicia o nó, implanta o contrato, concede perfis, cria LOT-0001 a LOT-0005 e verifica a cadeia |
| 0:20 | Logs ao vivo | Terminal 2: `make logs` | Linhas verdes `BLOCO` de cada bloco minerado |
| 0:30 | Blockchain local em execução | Terminal 1: `make status`. Navegador: <http://127.0.0.1:5000>, aba **Painel** | `height`, `difficulty`, `integrity.valid: true`, contrato implantado. Cabeçalho "Blockchain local ativa" |
| 1:00 | Operação pela interface | Carteira **Produtor**, aba **Registrar**, **Registrar lote**. Preencher origem e quantidade. **Assinar e enviar à blockchain** | Painel verde com hash, bloco e nonce. Terminal 2: `ENVIO`, `BLOCO`, `CONFIRMADA` |
| 2:00 | Consulta e mudança de estado | Carteira **Beneficiador**, **Registrar beneficiamento**, lote `LOT-0006`, descrição, enviar. Aba **Consultar**, `LOT-0006` | CADASTRADO para BENEFICIADO. Histórico com bloco, autor e transação |
| 2:50 | Operação inválida ou sem permissão | Aba **Registrar**, cenário **Carteira sem permissão**, enviar. Depois **Pular etapas**, enviar | `ACCESS_DENIED` e `INVALID_TRANSITION`. Terminal 2: linhas vermelhas `REJEITADA`, nenhum `BLOCO`. Aba **Rejeições** |
| 3:40 | Fechamento | Terminal 1: `make validate` | Cadeia íntegra após as operações |

## Cores dos logs

| Rótulo | Cor | Significado |
| --- | --- | --- |
| `ENVIO` | Ciano | Carteira assinou e enviou a operação |
| `BLOCO`, `CONFIRMADA` | Verde | Bloco minerado e operação gravada |
| `REJEITADA` | Vermelho | Contrato ou nó recusou, nenhum bloco criado |
| `INTEGRIDADE` | Amarelo | Adulteração detectada na aba Integridade |

## Se algo falhar

| Falha | Comando |
| --- | --- |
| Porta 5000 ou 8545 ocupada | `make stop` ou `make docker-down` |
| Sem ambiente virtual | `make venv` |
| Plano B com Docker | `make docker-reset && make docker-up && make docker-seed`, depois `make docker-logs` |
| Interface fora do ar | Abrir `docs/slides/video/demonstracao.webm` |

## Depois

```bash
make stop
```
