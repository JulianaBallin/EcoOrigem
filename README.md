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
  <img alt="Testes" src="https://img.shields.io/badge/Testes-57_verificações-0A9EDC?style=for-the-badge&logo=node.js&logoColor=white">
</div>

---

<h2 align="center">Problema e solução</h2>

Produtos como açaí, castanha-do-Brasil, cupuaçu e murumuru passam por organizações diferentes antes de chegar ao consumidor. Cada participante mantém o próprio registro, o que dificulta verificar qual histórico é íntegro e quem executou cada etapa.

O **EcoOrigem** registra o ciclo do lote em um contrato inteligente público. A MetaMask identifica e autentica cada participante, o contrato aplica os perfis e a ordem obrigatória, e a Sepolia mantém transações e eventos consultáveis no Etherscan. Documentos permanecem fora da Ethereum: somente o hash SHA-256 e uma referência `ipfs://` são registrados.

Produtor &rarr; Beneficiador &rarr; Transportador &rarr; Distribuidor &rarr; Consumidor

Blockchain é adequada porque participantes independentes precisam compartilhar o mesmo histórico sem entregar a uma única organização o poder de reescrevê-lo. Ela prova que o registro confirmado não mudou, mas não garante que a informação enviada na origem era verdadeira.

---

<h2 align="center">Estado da publicação</h2>

Os artefatos locais estão prontos e validados. As três ações abaixo exigem a carteira MetaMask e as contas externas da equipe; por isso, não podem ser simuladas nem preenchidas com dados fictícios.

| Item obrigatório | Estado em 07/11/2026 | Dado final |
| --- | --- | --- |
| Contrato na Sepolia | Pendente de confirmação na MetaMask | Endereço: `PENDENTE` |
| Transação e bloco do deploy | Pendente do deploy | Hash: `PENDENTE` · bloco: `PENDENTE` |
| Código verificado no Etherscan | Pendente do deploy | URL: `PENDENTE` |
| dApp na Vercel | Pendente de vincular o repositório | URL: `PENDENTE` |
| Vídeo de 3 a 5 minutos | Pendente após a publicação | URL: `PENDENTE` |

O procedimento completo está em [Implantação na Sepolia e Vercel](docs/deploy-sepolia.md). Depois do deploy, um único comando registra endereço, bloco e hash no frontend:

```bash
make configure ADDRESS=0x... BLOCK=123456 TX=0x...
```

---

<h2 align="center">Arquitetura</h2>

```text
Pessoa usuária
    │
    ▼
Frontend estático na Vercel ── Web3.js 4.0.3 ── MetaMask
    │                                              │
    │ .call()                                      │ assinatura e .send()
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

| Componente | Responsabilidade |
| --- | --- |
| [Contrato Solidity](contracts/EcoOrigem.sol) | Perfis, custódia, máquina de estados, taxa de cadastro, documentos, eventos e administração |
| [Frontend](frontend/) | Conexão, autenticação por assinatura, troca de rede, consultas, transações, eventos e mensagens de erro |
| MetaMask | Mantém as chaves fora da aplicação, assina o desafio de sessão e confirma transações |
| Ethereum Sepolia | Executa o contrato, confirma transações e replica o estado público |
| IPFS | Armazena opcionalmente o documento; o contrato guarda somente hash e URI |
| Etherscan | Permite conferir contrato, transações, blocos e eventos |

### Autenticação e perfis

Não existe senha armazenada no navegador ou na blockchain. Em uma dApp estática, um formulário de usuário e senha poderia ser contornado e não protegeria o contrato. O EcoOrigem usa o modelo próprio da Ethereum:

1. a MetaMask conecta a conta;
2. a carteira assina um desafio único, sem gas;
3. o frontend recupera o endereço da assinatura e não persiste a assinatura;
4. o contrato consulta os perfis concedidos ao endereço;
5. cada escrita ainda precisa ser assinada e autorizada on-chain.

Esse fluxo autentica o controle da carteira. A autorização real sempre ocorre no contrato, e não apenas na interface.

---

<h2 align="center">Contrato inteligente</h2>

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
| `grantRole` | Proprietário | Concede perfil a uma carteira | `RoleUpdated` | `Unauthorized`, `InvalidData` |
| `revokeRole` | Proprietário | Revoga perfil | `RoleUpdated` | `Unauthorized` |
| `setPaused` | Proprietário | Pausa ou retoma escritas | `PauseChanged` | `Unauthorized`, `require` |
| `registerLot` | Produtor | Cadastro pagável e designação do beneficiador | `LotRegistered` | `WrongFee`, `Unauthorized`, `InvalidData` |
| `recordProcessing` | Beneficiador designado | Avança e designa transportador | `LotStatusChanged`, `DocumentAttached` | `InvalidStatus`, `DesignatedActorOnly` |
| `startTransport` | Transportador designado | Avança, registra temperatura e designa distribuidor | `LotStatusChanged` | `InvalidStatus`, `Unauthorized` |
| `confirmDelivery` | Distribuidor designado | Confirma entrega e custódia | `LotStatusChanged` | `DesignatedActorOnly` |
| `finalizeLot` | Distribuidor custodiante | Encerra o ciclo | `LotStatusChanged` | `InvalidStatus` |
| `attachDocument` | Custodiante atual | Registra SHA-256 e URI IPFS | `DocumentAttached` | `DuplicateDocument`, `InvalidData` |
| `withdrawFees` | Proprietário | Envia as taxas à tesouraria imutável | `FeesWithdrawn` | `TransferFailed`, `require` |

Consultas públicas: `hasRole`, `totalLots`, `getLot`, `getLots`, `getDocuments`, `getHistory` e `statusLabel`.

### Sete grupos obrigatórios de Solidity

Todos estão marcados no código com comentários `// [Recurso: ...]`.

| Grupo | Onde aparece | Justificativa |
| --- | --- | --- |
| Tipos de dados | Linhas 58 a 65; `Lot` nas linhas 25 a 41 | `uint256` mede quantidade e tempo, `int256` permite temperatura negativa, `bool` representa atividade/pausa, `address payable` recebe taxas, `string` guarda dados descritivos e `bytes32` guarda hashes. `constant` e `immutable` evitam alterações indevidas |
| Funções | `constructor` na linha 114; funções de negócio 157 a 361; consultas 374 a 437; internas 445 a 541 | `external`, `public`, `internal` e `private` reduzem a superfície de chamada. `view` e `pure` fazem leitura sem transação. `registerLot` é `payable` |
| Estruturas de controle | `registerLot` 192 a 221; `getLots` 394 a 414; `statusLabel` 437 a 443 | `if/else`, `require` e `for` implementam validação, paginação limitada a 50 e tradução de estados |
| Arrays e mappings | Linhas 67 a 74; `getLots` e `_storeDocument` | Array dinâmico lista IDs e históricos. Mappings ligam ID a struct, endereço a contagem e usam chaves aninhadas para perfis e documentos |
| Structs e enums | Linhas 8 a 56 | `Role` e `Status` restringem valores; `Lot`, `Document` e `HistoryEntry` organizam entidades com mais de três campos |
| Modificadores | Linhas 119 a 152 | `onlyOwner`, `onlyRole(role)`, `lotExists(id)`, `atStatus(id,status)` e `whenRunning` reutilizam acesso, existência, estado e pausa. Três recebem parâmetros |
| Eventos e erros | Linhas 76 a 111 | Seis eventos expõem histórico com parâmetros `indexed`; nove erros personalizados devolvem causas e argumentos que o frontend traduz |

### Segurança aplicada

- Chaves privadas e frases de recuperação nunca entram no projeto.
- Controle de acesso e custódia é repetido no contrato, mesmo quando o frontend oculta ações.
- A taxa precisa ser exata e o saque usa a tesouraria imutável.
- O laço público tem limite de 50 itens para evitar consumo sem limite.
- Arquivos e credenciais não são gravados on-chain.
- O saque segue checks-effects-interactions e só pode ser chamado pelo proprietário.
- Entradas têm limites de tamanho, quantidade, data, temperatura e formato de endereço.

---

<h2 align="center">Frontend e integração Web3</h2>

O frontend usa HTML, CSS e JavaScript puros. A Web3.js 4.0.3 é carregada por CDN e protegida por SRI, atendendo ao requisito de versão 4.x.

| Requisito | Implementação |
| --- | --- |
| Conectar carteira e saldo | `eth_requestAccounts`, endereço reduzido e `getBalance` |
| Conferir/trocar rede | `eth_chainId` e `wallet_switchEthereumChain`; opção de adicionar Sepolia |
| Leitura | totais, perfis, lotes, documentos e histórico com `.call()` |
| Escrita com ETH | `registerLot(...).send({ value: REGISTRATION_FEE })` |
| Estado da transação | diálogo para confirmação, pendência, bloco confirmado ou falha; hash abre no Etherscan |
| Erros | cancelamento, saldo insuficiente, `require` e erros personalizados traduzidos para português |
| Eventos | `getPastEvents("allEvents")` limitado ao bloco do deploy ou aos 50 mil blocos recentes |
| Interface do dono | aba Administração aparece somente para o endereço `owner` |
| Troca de conta/rede | listeners `accountsChanged` e `chainChanged` invalidam a sessão e recarregam os dados |
| Responsividade | validada em 1440 px, 768 px e 390 px, sem rolagem horizontal |

---

<h2 align="center">Estrutura do repositório</h2>

```text
EcoOrigem/
├── contracts/
│   └── EcoOrigem.sol
├── frontend/
│   ├── assets/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── utils.js
│   └── contract.js              # ABI + dados do deploy
├── tests/
│   ├── contract.test.mjs
│   └── frontend-utils.test.mjs
├── scripts/
│   ├── compile-contract.mjs
│   ├── sync-contract-config.mjs
│   ├── configure-contract.mjs
│   ├── validate-frontend.mjs
│   └── build_slides.py
├── docs/
│   ├── deploy-sepolia.md
│   ├── roteiro-testes.md
│   ├── demonstracao-local.md
│   ├── prints/
│   └── slides/
├── legacy/
│   └── entrega-1-python/          # protótipo local preservado, fora da dApp atual
├── Makefile
├── package.json
└── vercel.json
```

---

<h2 align="center">Executar localmente</h2>

### Requisitos

- Node.js 20 ou superior;
- Python 3 somente para o servidor estático e para regenerar os slides;
- navegador com [MetaMask](https://metamask.com/pt-BR);
- SepoliaETH de teste, nunca ETH real.

```bash
git clone https://github.com/JulianaBallin/EcoOrigem.git
cd EcoOrigem
npm ci
make check
make serve
```

Abra <http://127.0.0.1:8000>. O navegador precisa servir os arquivos por HTTP; a MetaMask não funciona corretamente ao abrir `index.html` por `file://`.

Comandos principais:

| Comando | Função |
| --- | --- |
| `make menu` | Exibe o menu interativo |
| `make compile` | Compila com Solidity 0.8.34, optimizer de 200 runs e EVM Paris |
| `make abi` | Compila e sincroniza a ABI em `frontend/contract.js` |
| `make test` | Executa o contrato em uma Ethereum local isolada e testa utilitários |
| `make check` | Compila, sincroniza ABI, valida o frontend e executa os testes |
| `make security` | Audita tudo, falha para achados fora das ferramentas locais e confirma que a publicação não tem dependências npm |
| `make slides` | Regera PPTX e PDF preservando o design da Entrega 1 |

---

<h2 align="center">Testes e demonstração</h2>

O teste automatizado implanta um contrato novo em uma Ethereum local e cobre o fluxo completo, sem usar saldo ou rede pública. São **57 verificações** entre as duas suítes:

- proprietário, concessão e revogação de quatro perfis;
- taxa ausente e cadastro pagável correto;
- ator sem perfil e ator não designado;
- cinco estados na ordem e tentativa de pular etapas;
- temperatura fora do limite;
- documento novo, repetido e anexado por carteira sem custódia;
- consulta, paginação e histórico;
- pausa, retomada, saque e tentativa de saque sem saldo;
- conversões de quantidade/data, URI IPFS e tuplas Web3.

O roteiro reproduzível para o avaliador está em [docs/roteiro-testes.md](docs/roteiro-testes.md). A demonstração de 5 minutos está em [docs/demonstracao-local.md](docs/demonstracao-local.md).

```bash
make check
```

Resultado local de 07/11/2026: contrato compilado com Solidity `0.8.34`, bytecode implantado de `13.592 bytes`, duas suítes aprovadas e frontend sem erros JavaScript em desktop, tablet e celular.

---

<h2 align="center">Documentação</h2>

| Documento | Conteúdo |
| --- | --- |
| [Implantação](docs/deploy-sepolia.md) | Remix, MetaMask, faucet, Etherscan, configuração do frontend e Vercel |
| [Contrato](docs/contrato-inteligente.md) | Regras, perfis, estados, eventos, erros e segurança |
| [Roteiro de testes](docs/roteiro-testes.md) | Preparação e cenários válidos e inválidos |
| [Demonstração](docs/demonstracao-local.md) | Sequência de 5 minutos para a apresentação ao vivo |
| [Apresentação PDF](docs/slides/apresentacao-ecoorigem.pdf) | 13 slides no design da Entrega 1 |
| [Apresentação editável](docs/slides/apresentacao-ecoorigem.pptx) | PPTX com notas de fala |
| [Roteiro da apresentação](docs/slides/roteiro-apresentacao.md) | Divisão dos 15 minutos e perguntas prováveis |
| [Evidências](docs/prints/README.md) | Checklist de capturas a produzir após o deploy |

---

<h2 align="center">Limitações e melhorias futuras</h2>

- A rede não confirma se o dado enviado é verdadeiro; confirma autoria da carteira e permanência do registro.
- Endereços, transações e dados on-chain são públicos. Não devem ser usados dados pessoais ou documentos sigilosos.
- A disponibilidade do arquivo no IPFS depende de pinning; o hash permanece verificável mesmo se o arquivo ficar indisponível.
- A taxa de cadastro é fixa no bytecode. Uma versão futura pode usar governança com atraso para alterar parâmetros.
- A lista do frontend mostra até 50 lotes por vez; paginação incremental é a próxima evolução.
- Perfis revogados podem deixar um lote sem o ator designado. Uma função administrativa de substituição, com evento e prazo, pode tratar contingências.
- Antes de uso produtivo seriam necessários auditoria independente, política de privacidade, oráculos e plano de resposta a incidentes.

---

<h2 align="center">Equipe</h2>

| Integrante | Papel principal na Entrega 2 |
| --- | --- |
| **Ana Beatriz Maciel Nunes** | Experiência do frontend e apresentação |
| **Fernando Luiz da Silva Freire** | Contrato Solidity e regras de negócio |
| **Juliana Ballin Lima** | Integração Web3, testes, documentação e implantação |

Todos os integrantes devem dominar contrato, frontend e fluxo de implantação para a arguição.

Professor: Prof. Dr. Fábio Santos.

### Declaração de uso de IA

Ferramentas de IA foram usadas como apoio na revisão de arquitetura, implementação, testes e documentação. A equipe revisou o código, validou os fluxos e permanece responsável pelas decisões técnicas e pelo conteúdo entregue.

Licença [MIT](LICENSE).
