# Contrato inteligente EcoOrigem

O contrato [`EcoOrigem.sol`](contracts/EcoOrigem.sol) implementa rastreabilidade por perfis, custódia designada e máquina de estados. A conta que implanta torna-se `owner` e `treasury`, ambas imutáveis.

## Organização do backend Solidity

```text
backend/
├── config/
│   └── solidity-compiler.json
├── contracts/
│   └── EcoOrigem.sol
└── tests/
    ├── contract.test.mjs
    └── solidity/
        └── EcoOrigem_test.sol
```

`contracts/EcoOrigem.sol` é a única fonte do contrato. O teste JavaScript implanta essa fonte em uma rede Ganache isolada; o teste Solidity importa o mesmo arquivo quando executado pelo plugin Solidity Unit Testing do Remix. Ao clonar o repositório pelo Git no Remix, o arquivo [`remix.config.json`](../remix.config.json) da raiz aplica optimizer de 200 runs e EVM Paris usando a configuração mantida em `backend/config/`.

## Perfis

| Valor | Perfil | Responsabilidade |
| --- | --- | --- |
| `0` | `None` | Valor reservado; também identifica uma falha de `onlyOwner` |
| `1` | `Producer` | Cadastra o lote e designa o beneficiador |
| `2` | `Processor` | Registra processamento e designa o transportador |
| `3` | `Carrier` | Registra transporte e designa o distribuidor |
| `4` | `Distributor` | Confirma o recebimento e finaliza |

O proprietário passa em `hasRole` para qualquer perfil, mas as regras de ator designado continuam válidas. O frontend mostra a administração somente ao proprietário; o contrato repete esse controle com `onlyOwner`.

## Estados

```text
Registered -> Processed -> InTransit -> Distributed -> Finalized
```

Cada transição exige:

1. contrato não pausado;
2. lote existente;
3. estado anterior exato;
4. perfil apropriado;
5. carteira designada pela etapa anterior;
6. entradas dentro dos limites.

Uma falha executa `revert`: o estado não muda e nenhum evento de sucesso é emitido. A tentativa pode consumir gas quando já foi enviada à rede.

## Dados do lote

| Campo | Tipo | Regra |
| --- | --- | --- |
| `id` | `uint256` | Sequencial a partir de 1 |
| `product` | `string` | 2 a 60 bytes |
| `origin` | `string` | 3 a 120 bytes |
| `quantityGrams` | `uint256` | 1 g a 100.000.000 g |
| `harvestedAt` | `uint256` | Entre 01/01/2000 e o bloco atual |
| `producer` | `address` | Remetente do cadastro |
| `custodian` | `address` | Carteira responsável atual |
| `processor`, `carrier`, `distributor` | `address` | Atores designados na sequência |
| `status` | `Status` | Um dos cinco estados |
| `transportTemperatureMilliC` | `int256` | -30.000 a 60.000, em milésimos de °C |
| `createdAt`, `updatedAt` | `uint256` | Timestamps dos blocos |
| `active` | `bool` | Marca a existência do lote |

Quantidade e temperatura usam inteiros para não depender de ponto flutuante, que não existe em Solidity.

## Documentos

`attachDocument` registra:

- SHA-256 em `bytes32`;
- URI `ipfs://` opcional de até 120 bytes;
- descrição de 3 a 120 bytes;
- carteira autora;
- timestamp do bloco.

O mapping aninhado `registeredDocuments[lotId][contentHash]` recusa o mesmo hash duas vezes no mesmo lote. Somente o custodiante atual pode anexar, e lotes finalizados não mudam.

## Taxa e tesouraria

`registerLot` exige exatamente `REGISTRATION_FEE = 0.00001 ether`. Na Sepolia esse valor é SepoliaETH sem valor comercial.

`withdrawFees`:

1. lê o saldo;
2. exige saldo positivo;
3. transfere tudo à `treasury` imutável;
4. reverte com `TransferFailed` se a chamada falhar;
5. emite `FeesWithdrawn`.

A tesouraria é a própria conta implantadora. O contrato não aceita pagamento direto; somente `registerLot` é `payable`.

## Eventos

| Evento | Parâmetros indexados | Quando ocorre |
| --- | --- | --- |
| `RoleUpdated` | `account`, `role` | Concessão ou revogação |
| `LotRegistered` | `lotId`, `producer`, `processor` | Cadastro pagável |
| `LotStatusChanged` | `lotId`, `status`, `actor` | Cada avanço de estado |
| `DocumentAttached` | `lotId`, `contentHash`, `author` | Registro de prova documental |
| `PauseChanged` | `actor` | Pausa ou retomada |
| `FeesWithdrawn` | `treasury` | Saque das taxas |

O frontend consulta até 100 eventos recentes com `getPastEvents` e cria links para as transações no Etherscan.

## Erros personalizados

| Erro | Significado |
| --- | --- |
| `Unauthorized(account, requiredRole)` | A carteira não tem o perfil ou não é proprietária |
| `InvalidStatus(lotId, current, expected)` | A etapa atual não permite a operação |
| `LotNotFound(lotId)` | O ID não existe |
| `InvalidData(field)` | Entrada fora das regras |
| `WrongFee(received, expected)` | Valor pagável diferente da taxa |
| `DesignatedActorOnly(caller, expected)` | Outra carteira, embora possa ter o perfil, foi designada |
| `DuplicateDocument(contentHash)` | Hash já registrado no lote |
| `FinalizedLot(lotId)` | Lote encerrado não aceita documentos ou novas alterações |
| `TransferFailed()` | Saque não transferido à tesouraria |

Também existem `require` para contrato pausado, perfil já no estado solicitado, limite da paginação e saldo vazio.

## Consultas

| Função | Retorno |
| --- | --- |
| `hasRole(account, role)` | Se a carteira possui o perfil |
| `totalLots()` | Quantidade de lotes |
| `getLot(lotId)` | Struct completa do lote |
| `getLots(offset, limit)` | Página com 1 a 50 lotes |
| `getDocuments(lotId)` | Documentos do lote |
| `getHistory(lotId)` | Sequência de estados, atores e observações |
| `statusLabel(status)` | Rótulo legível do enum |

## Segurança e limitações

- Não há função administrativa para editar ou apagar lotes.
- `private` não torna dados secretos; qualquer estado da Ethereum é público.
- Perfis revogados não substituem automaticamente um ator já designado.
- Um documento disponível no IPFS ainda depende de pinning.
- O contrato não usa oráculo; não confirma localização, temperatura física nem veracidade da origem.
- A versão acadêmica não passou por auditoria externa e não deve ser usada em produção.
