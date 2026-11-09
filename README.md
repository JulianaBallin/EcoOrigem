<p align="center">
  <img src="frontend/assets/ecoorigem-logo.png" alt="EcoOrigem" width="620">
</p>

<p align="center">
  Rastreabilidade de produtos da bioeconomia amazônica com contrato inteligente na Ethereum Sepolia.
  <br>
  <em>Entrega 2 | Oficina de Desenvolvimento de Sistemas III | UEA</em>
</p>

<div align="center">
  <img alt="Solidity" src="https://img.shields.io/badge/Solidity-0.8.34-363636?style=for-the-badge&logo=solidity&logoColor=white">
  <img alt="Ethereum Sepolia" src="https://img.shields.io/badge/Ethereum-Sepolia-627EEA?style=for-the-badge&logo=ethereum&logoColor=white">
  <img alt="Web3.js" src="https://img.shields.io/badge/Web3.js-4.0.3-F16822?style=for-the-badge&logo=web3dotjs&logoColor=white">
  <img alt="MetaMask" src="https://img.shields.io/badge/MetaMask-carteira-F6851B?style=for-the-badge&logo=metamask&logoColor=white">
</div>

## Problema e solução

Produtos como açaí, castanha-do-Brasil, cupuaçu e murumuru passam por várias organizações antes de chegar ao consumidor. Registros isolados dificultam verificar a integridade do histórico e identificar quem executou cada etapa.

O EcoOrigem registra o ciclo do lote em um contrato inteligente público. A MetaMask identifica cada participante, o contrato aplica os perfis e a ordem obrigatória, e a Sepolia mantém transações e eventos consultáveis. Documentos ficam fora da Ethereum: somente o hash SHA-256 e uma referência `ipfs://` são registrados.

```text
Produtor → Beneficiador → Transportador → Distribuidor → Consumidor
```

A blockchain prova que um registro confirmado não foi alterado. Ela não garante que a informação enviada na origem era verdadeira.

## Estado da publicação

Os artefatos locais estão prontos e validados. As ações abaixo exigem a MetaMask e as contas externas da equipe.

| Item obrigatório | Estado em 07/11/2026 | Dado final |
| --- | --- | --- |
| Contrato na Sepolia | Pendente de confirmação na MetaMask | Endereço: `PENDENTE` |
| Transação e bloco do deploy | Pendente do deploy | Hash: `PENDENTE` · bloco: `PENDENTE` |
| Código verificado no Etherscan | Pendente do deploy | URL: `PENDENTE` |
| dApp na Vercel | Pendente de vincular o repositório | URL: `PENDENTE` |
| Vídeo de 3 a 5 minutos | Pendente após a publicação | URL: `PENDENTE` |

Depois do deploy confirmado pela equipe, registre endereço, bloco e hash públicos no frontend:

```bash
make configure ADDRESS=0x... BLOCK=123456 TX=0x...
```

## Arquitetura

```text
Pessoa usuária
    │
    ▼
Frontend estático na Vercel ── Web3.js 4.x ── MetaMask
    │                                              │
    │ consultas .call()                            │ assinatura e .send()
    └──────────────────────┬───────────────────────┘
                           ▼
                 Ethereum Sepolia
                           │
                           ▼
                 EcoOrigem.sol
             perfis · estados · eventos
                           │
             hash SHA-256 + URI ipfs://
                           │
                           ▼
                  conteúdo no IPFS
```

| Camada | Responsabilidade |
| --- | --- |
| [Backend Solidity](backend/contracts/EcoOrigem.sol) | Perfis, custódia, máquina de estados, taxa, documentos, eventos e administração |
| [Frontend](frontend/) | Conexão, autenticação por assinatura, consultas, transações, eventos e mensagens de erro |
| [Workspace Remix](remix/) | Cópia sincronizada do contrato, configuração reproduzível e testes Solidity |
| MetaMask | Mantém as chaves fora da aplicação, assina o desafio e confirma transações |
| Ethereum Sepolia | Executa o contrato, confirma transações e replica o estado público |
| IPFS | Armazena opcionalmente documentos; o contrato guarda somente hash e URI |
| Etherscan | Permite conferir contrato, transações, blocos e eventos |

### Autenticação e perfis

Não existe senha armazenada no navegador ou na blockchain. Em uma dApp estática, usuário e senha no frontend poderiam ser contornados e não protegeriam o contrato. O fluxo usa o modelo nativo da Ethereum:

1. a MetaMask conecta a conta;
2. a carteira assina um desafio único, sem gas;
3. o frontend recupera o endereço da assinatura e não persiste a assinatura;
4. o contrato consulta os perfis concedidos ao endereço;
5. cada escrita ainda precisa ser assinada e autorizada on-chain.

## Contrato inteligente

### Ciclo de vida

| Estado | Carteira autorizada | Efeito |
| --- | --- | --- |
| `Registered` | Produtor | Cadastra o lote com taxa de `0.00001 ether` e designa o beneficiador |
| `Processed` | Beneficiador designado | Registra o processamento e designa o transportador |
| `InTransit` | Transportador designado | Registra destino e temperatura e designa o distribuidor |
| `Distributed` | Distribuidor designado | Confirma o recebimento e assume a custódia |
| `Finalized` | Distribuidor custodiante | Encerra o lote; novas alterações são recusadas |

### Funções de negócio

| Função | Quem chama | Efeito | Evento principal | Erros esperados |
| --- | --- | --- | --- | --- |
| `grantRole` | Proprietário | Concede perfil | `RoleUpdated` | `Unauthorized`, `InvalidData` |
| `revokeRole` | Proprietário | Revoga perfil | `RoleUpdated` | `Unauthorized` |
| `setPaused` | Proprietário | Pausa ou retoma escritas | `PauseChanged` | `Unauthorized`, `require` |
| `registerLot` | Produtor | Cadastro pagável e designação do beneficiador | `LotRegistered` | `WrongFee`, `Unauthorized`, `InvalidData` |
| `recordProcessing` | Beneficiador designado | Avança e designa transportador | `LotStatusChanged`, `DocumentAttached` | `InvalidStatus`, `DesignatedActorOnly` |
| `startTransport` | Transportador designado | Registra transporte e designa distribuidor | `LotStatusChanged` | `InvalidStatus`, `Unauthorized` |
| `confirmDelivery` | Distribuidor designado | Confirma entrega e custódia | `LotStatusChanged` | `DesignatedActorOnly` |
| `finalizeLot` | Distribuidor custodiante | Encerra o ciclo | `LotStatusChanged` | `InvalidStatus` |
| `attachDocument` | Custodiante atual | Registra SHA-256 e URI IPFS | `DocumentAttached` | `DuplicateDocument`, `InvalidData` |
| `withdrawFees` | Proprietário | Envia taxas à tesouraria imutável | `FeesWithdrawn` | `TransferFailed`, `require` |

Consultas públicas: `hasRole`, `totalLots`, `getLot`, `getLots`, `getDocuments`, `getHistory` e `statusLabel`.

### Recursos obrigatórios de Solidity

Os sete grupos exigidos no trabalho aparecem com comentários `// [Recurso: ...]` no contrato e seguem os exemplos do material de apoio do professor.

| Grupo | Implementação no EcoOrigem | Justificativa |
| --- | --- | --- |
| Tipos de dados | `uint256`, `int256`, `bool`, `address payable`, `string`, `bytes32`, `constant`, `immutable` | Representam quantidade, temperatura, pausa, tesouraria, textos, hashes e valores imutáveis |
| Funções | `constructor`, funções `external`, `public`, `internal`, `private`, `view`, `pure` e `payable` | Restringem a superfície de chamada e distinguem leitura, escrita e recebimento de ETH |
| Estruturas de controle | `if/else`, `require` e `for` limitado a 50 itens | Validam entradas, controlam estados e evitam laços públicos sem limite |
| Arrays e mappings | IDs e históricos dinâmicos, perfis e documentos em mappings | Mantêm índices e relações eficientes por lote e carteira |
| Structs e enums | `Lot`, `Document`, `HistoryEntry`, `Role` e `Status` | Organizam as entidades e restringem os estados válidos |
| Modificadores | `onlyOwner`, `onlyRole`, `lotExists`, `atStatus`, `whenRunning` | Reutilizam autorização, existência, estado e pausa |
| Eventos e erros | Seis eventos e nove erros personalizados | Expõem histórico pesquisável e retornam causas específicas ao frontend |

Mais detalhes estão em [backend/README.md](backend/README.md).

## Frontend e integração Web3

O frontend usa HTML, CSS e JavaScript puros, como nos exemplos de Mural do material de apoio. A Web3.js 4.0.3 é carregada por CDN com SRI.

| Requisito | Implementação |
| --- | --- |
| Conectar carteira e saldo | `eth_requestAccounts`, endereço reduzido e `getBalance` |
| Conferir ou trocar rede | `eth_chainId`, `wallet_switchEthereumChain` e inclusão da Sepolia |
| Leitura | Totais, perfis, lotes, documentos e histórico com `.call()` |
| Escrita com ETH | `registerLot(...).send({ value: REGISTRATION_FEE })` |
| Estado da transação | Confirmação, pendência, bloco confirmado ou falha, com link para Etherscan |
| Erros | Cancelamento, saldo insuficiente, `require` e erros personalizados em português |
| Eventos | `getPastEvents("allEvents")` a partir do bloco de implantação |
| Administração | Funções administrativas visíveis somente ao endereço `owner` |
| Troca de conta ou rede | `accountsChanged` e `chainChanged` invalidam a sessão e recarregam os dados |

## Estrutura em camadas

```text
EcoOrigem/
├── backend/
│   ├── contracts/EcoOrigem.sol       # contrato atual da Entrega 2
│   ├── tests/contract.test.mjs        # integração local com Ganache
│   └── python/                        # implementação didática da Entrega 1
├── frontend/
│   ├── assets/
│   ├── tests/utils.test.mjs
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── utils.js
│   └── contract.js                    # ABI e dados do deploy
├── remix/
│   ├── contracts/EcoOrigem.sol        # cópia gerada do contrato principal
│   ├── tests/EcoOrigem_test.sol       # testes executáveis no Remix
│   ├── compiler_config.json
│   └── remix.config.json
├── scripts/                            # compilação, validação e segurança
├── docs/
│   ├── assets/
│   ├── relatorio/
│   └── slides/
├── TESTES.md
├── Makefile
├── package.json
└── vercel.json
```

O diretório `docs/` contém somente recursos visuais, relatório e apresentação. O roteiro de testes público permanece na raiz; os procedimentos operacionais pessoais de deploy e demonstração não são versionados.

## Executar localmente

Requisitos: Node.js 20 ou superior, Python 3 para o servidor estático e um navegador com [MetaMask](https://metamask.com/pt-BR).

```bash
git clone https://github.com/JulianaBallin/EcoOrigem.git
cd EcoOrigem
npm ci
make check
make serve
```

Abra <http://127.0.0.1:8000>. Não abra `index.html` por `file://`, pois a carteira precisa de uma origem HTTP ou HTTPS.

| Comando | Função |
| --- | --- |
| `make compile` | Compila com Solidity 0.8.34, optimizer de 200 runs e EVM Paris |
| `make remix` | Atualiza a pasta completa que pode ser importada no Remix |
| `make abi` | Compila e sincroniza a ABI em `frontend/contract.js` |
| `make test` | Testa o contrato em uma Ethereum local isolada e testa os utilitários |
| `make check` | Prepara o Remix, compila, sincroniza ABI, valida e testa |
| `make security` | Procura credenciais e audita as dependências locais |
| `make slides` | Regenera a apresentação PPTX e PDF |

## Testes e demonstração

Os testes automatizados implantam um contrato novo em uma Ethereum local, sem saldo nem rede pública. Cobrem perfis, taxa, fluxo completo, estados inválidos, custódia, documentos, paginação, pausa, saque, conversões do frontend e tratamento de dados Web3.

```bash
make check
make security
```

Use [TESTES.md](TESTES.md) para reproduzir os cenários. O ensaio da demonstração deve seguir as notas da apresentação e o guia operacional mantido somente no ambiente local.

## Segurança e dados sensíveis

- Nunca registre chave privada, frase de recuperação, senha, token ou credencial no Git, em URLs, em logs, no código ou no Docker Compose.
- Arquivos `.env` são ignorados. Quando uma configuração privada for realmente necessária, ela deve existir apenas no `.env` local ou no gerenciador seguro da plataforma.
- Arquivos `.env.example` contêm somente nomes e valores não sensíveis de exemplo.
- O frontend publicado é estático. Qualquer variável entregue ao navegador é pública, mesmo se tiver sido lida de um `.env` durante o build. Portanto, tokens e chaves secretas não pertencem ao frontend nem às variáveis públicas da Vercel.
- A MetaMask mantém a chave privada fora da aplicação. O EcoOrigem solicita conexão e assinatura, nunca a chave ou a frase de recuperação.
- `make security` falha se detectar formatos comuns de credenciais nos arquivos publicáveis.

## Documentação e entregáveis

| Item | Conteúdo |
| --- | --- |
| [Contrato](backend/README.md) | Regras, perfis, estados, eventos, erros e segurança |
| [Roteiro de testes](TESTES.md) | Cenários válidos, inválidos, administrativos e responsivos |
| [Apresentação PDF](docs/slides/apresentacao-ecoorigem.pdf) | Nove slides para a apresentação |
| [Apresentação editável](docs/slides/apresentacao-ecoorigem.pptx) | PPTX com notas de fala |
| [Relatório PDF](docs/relatorio/relatorio-desenvolvimento-ecoorigem.pdf) | Relatório técnico da Primeira Entrega preservado como evidência |
| [Relatório editável](docs/relatorio/relatorio-desenvolvimento-ecoorigem.docx) | Fonte editável do relatório técnico preservado |

## Limitações e melhorias futuras

- A rede confirma autoria da carteira e permanência do registro, não a veracidade do dado de origem.
- Endereços, transações e dados on-chain são públicos. Não devem conter dados pessoais ou documentos sigilosos.
- A disponibilidade de arquivos no IPFS depende de pinning; o hash continua verificável se o arquivo ficar indisponível.
- A taxa de cadastro é fixa no bytecode.
- Perfis revogados podem deixar um lote sem o ator designado. Uma substituição administrativa com evento e prazo é uma melhoria futura.
- Um uso produtivo exigiria auditoria independente, política de privacidade, oráculos e plano de resposta a incidentes.

## Equipe

| Integrante | Papel principal na Entrega 2 |
| --- | --- |
| Ana Beatriz Maciel Nunes | Experiência do frontend e apresentação |
| Fernando Luiz da Silva Freire | Contrato Solidity e regras de negócio |
| Juliana Ballin Lima | Integração Web3, testes, documentação e implantação |

Todos os integrantes devem dominar contrato, frontend e fluxo de implantação para a arguição.

Professor: Prof. Dr. Fábio Santos.

### Declaração de uso de IA

Ferramentas de IA foram usadas como apoio na revisão de arquitetura, implementação, testes e documentação. A equipe revisou o código, validou os fluxos e permanece responsável pelas decisões técnicas e pelo conteúdo entregue.

Licença [MIT](LICENSE).
