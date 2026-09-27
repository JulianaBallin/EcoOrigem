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
| 0:00 | Inicialização | Terminal 1: `make demo` | Etapas 1 a 5: limpa dados, inicia o nó, implanta o contrato, concede perfis, cria LOT-0001 a LOT-0005 e verifica a cadeia |
| 0:20 | Logs ao vivo | Terminal 2: `make logs` | Blocos verdes `BLOCO #N CONFIRMADO` |
| 0:30 | Blockchain local em execução | Terminal 1: `make chain LAST=2`. Navegador: <http://127.0.0.1:5000>, aba **Painel** | Hash anterior, timestamp, dados, hash e nonce de cada bloco. "Blockchain é válida? Sim" |
| 1:00 | Operação pela interface | Carteira **Produtor**, aba **Registrar**, **Registrar lote**. Preencher origem e quantidade. **Assinar e enviar à blockchain** | Painel verde na interface. Terminal 2: novo `BLOCO #N CONFIRMADO` com os dados do lote |
| 2:00 | Consulta e mudança de estado | Carteira **Beneficiador**, **Registrar beneficiamento**, lote `LOT-0006`, descrição, enviar. Aba **Consultar**, `LOT-0006` | CADASTRADO para BENEFICIADO na interface e na linha `Status` do terminal 2 |
| 2:50 | Operação inválida ou sem permissão | Aba **Registrar**, cenário **Carteira sem permissão**, enviar. Depois **Pular etapas**, enviar | Terminal 2: `OPERAÇÃO REJEITADA` em vermelho com motivo e código. Nenhum bloco novo. Aba **Rejeições** |
| 3:40 | Fechamento | Terminal 1: `make chain LAST=1` | Último bloco encadeado e "Blockchain é válida? Sim" |

## Campos de cada bloco

| Campo no log | Exemplo do professor | Significado |
| --- | --- | --- |
| Índice | `Block #` | Posição na cadeia |
| Timestamp | `timestamp` | Data e hora da mineração |
| Dados | `data` | Operação e argumentos gravados |
| Hash anterior | `previousHash` | Hash do bloco anterior |
| Hash | `hash` | SHA-256 do bloco, começa com zeros |
| Nonce | `nonce` | Número encontrado na prova de trabalho |
| Encadeamento | `isBlockChainValid` | Hash anterior confere com o bloco anterior |

## Cores dos logs

| Título | Cor |
| --- | --- |
| `BLOCO #N CONFIRMADO`, `CADEIA RESTAURADA` | Verde |
| `OPERAÇÃO REJEITADA` | Vermelho |
| `ADULTERAÇÃO DETECTADA` | Amarelo |

## Se algo falhar

| Falha | Comando |
| --- | --- |
| Porta 5000 ou 8545 ocupada | `make stop` ou `make docker-down` |
| Sem ambiente virtual | `make venv` |
| Plano B com Docker | `make docker-reset && make docker-up && make docker-seed`, depois `make docker-logs` e `make docker-chain LAST=2` |
| Interface fora do ar | Abrir `docs/slides/video/demonstracao.webm` |

## Depois

```bash
make stop
```
