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

## Campos dos blocos

Nomes entre parênteses seguem o exemplo do professor.

| Campo | O que é | Exemplo |
| --- | --- | --- |
| Quem | Perfil e endereço da carteira que assinou a operação. | `Beneficiador (0x7ab7...fb25)` |
| Ação | O que a operação fez, em português. | `registrou o beneficiamento do lote LOT-0006` |
| Status | Etapa do lote antes e depois da operação. | `CADASTRADO para BENEFICIADO` |
| Índice (`Block #`) | Posição do bloco na cadeia. O gênesis é o 0. | `22` |
| Timestamp (`timestamp`) | Data e hora em que o bloco foi minerado. Entre parênteses, em milissegundos. | `27/09/2026 15:45:02 (1790538302418)` |
| Dados (`data`) | Operação gravada e seus argumentos. É o conteúdo do bloco. | `record_processing` com `lot_id: LOT-0006` |
| Hash anterior (`previousHash`) | Hash do bloco anterior. É o que liga um bloco ao outro. | `0000643f1a71...c40316` |
| Hash (`hash`) | Impressão digital SHA-256 do bloco. Qualquer mudança nos dados muda o hash. | `0000d112a0a3...5bfdb9` |
| Nonce (`nonce`) | Número testado até o hash começar com os zeros exigidos. | `90900` |
| Raiz de Merkle | Resumo único de todas as transações do bloco. | `ebaf7617d48f...cae6e8` |
| Prova de trabalho | Esforço para achar o nonce: tentativas, tempo e zeros exigidos. | `90.901 tentativas em 0,52 s, hash começa com 4 zeros` |
| Encadeamento (`isBlockChainValid`) | Confirma se o hash anterior bate com o bloco de trás. | `hash anterior confere com o hash do bloco #21` |
