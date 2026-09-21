<p align="center">
  <img src="assets/ecoorigem-logo.png" alt="EcoOrigem" width="650" style="border-radius: 10%;">
</p>

<p align="center">
  Plataforma de rastreabilidade baseada em <strong>Blockchain</strong> para produtos da bioeconomia amazônica.<br>
  <em>Da origem ao consumidor, com transparência e integridade.</em>
</p>

---

<h2 align="center">🌿 Sobre o EcoOrigem</h2>

O **EcoOrigem** é uma aplicação baseada em Blockchain desenvolvida para registrar e acompanhar as diferentes etapas da cadeia produtiva de produtos da bioeconomia amazônica.

A proposta é permitir que informações sobre **origem, produção, beneficiamento, transporte e distribuição** sejam registradas de forma rastreável e resistente a alterações, criando um histórico confiável para cada lote.

Entre os produtos que podem ser rastreados estão **açaí, castanha, murumuru, cupuaçu, óleos vegetais e produtos artesanais**.

---

<h2 align="center">🛠️ Tecnologias Utilizadas</h2>

<p align="center">
  <img alt="Solidity" src="https://img.shields.io/badge/Solidity-Smart%20Contracts-363636?style=for-the-badge&logo=solidity&logoColor=white">
  <img alt="Hardhat" src="https://img.shields.io/badge/Hardhat-Blockchain_Local-FFF100?style=for-the-badge">
  <img alt="Ethereum" src="https://img.shields.io/badge/Ethereum-Blockchain-3C3C3D?style=for-the-badge&logo=ethereum&logoColor=white">
</p>

<p align="center">
  <img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black">
  <img alt="Node.js" src="https://img.shields.io/badge/Node.js-Runtime-339933?style=for-the-badge&logo=nodedotjs&logoColor=white">
  <img alt="Ethers.js" src="https://img.shields.io/badge/Ethers.js-Web3-2535A0?style=for-the-badge">
  <img alt="MetaMask" src="https://img.shields.io/badge/MetaMask-Wallet-F6851B?style=for-the-badge&logo=metamask&logoColor=white">
</p>

<p align="center">
  <img alt="React" src="https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black">
  <img alt="Git" src="https://img.shields.io/badge/Git-Versionamento-F05032?style=for-the-badge&logo=git&logoColor=white">
  <img alt="GitHub" src="https://img.shields.io/badge/GitHub-Repositório-181717?style=for-the-badge&logo=github&logoColor=white">
</p>

---

<h2 align="center">🎯 Problema</h2>

Produtos provenientes da bioeconomia amazônica passam por diversos participantes antes de chegar ao consumidor.

Durante esse processo, informações sobre **origem, responsáveis e etapas da cadeia produtiva** podem ficar dispersas em diferentes sistemas ou documentos, dificultando a rastreabilidade e a verificação das informações.

O EcoOrigem busca responder:

> **Como garantir um histórico confiável e rastreável da origem e das movimentações de produtos da bioeconomia amazônica?**

---

<h2 align="center">⛓️ Por que Blockchain?</h2>

A Blockchain permite criar um histórico de registros **imutável, rastreável, auditável, cronológico e compartilhado entre diferentes participantes**.

Cada movimentação passa a fazer parte permanentemente do histórico do lote, dificultando alterações indevidas em informações já registradas.

Além disso, o uso de **Smart Contracts** permite definir automaticamente quem pode realizar determinadas operações e quais mudanças de estado são permitidas.

---

<h2 align="center">👥 Participantes da Cadeia</h2>

| Perfil            | Responsabilidade                    |
| ----------------- | ----------------------------------- |
| **Produtor**      | Registra a origem e cria o lote     |
| **Beneficiador**  | Registra etapas de processamento    |
| **Transportador** | Registra movimentações do produto   |
| **Distribuidor**  | Confirma recebimento e distribuição |
| **Administrador** | Gerencia usuários e permissões      |
| **Consumidor**    | Consulta a rastreabilidade do lote  |

---

<h2 align="center">🔄 Fluxo de Rastreabilidade</h2>

```text
PRODUTOR
    ↓
COLETA / PRODUÇÃO
    ↓
BENEFICIAMENTO
    ↓
TRANSPORTE
    ↓
DISTRIBUIÇÃO
    ↓
CONSUMIDOR
```

Cada etapa gera um novo registro associado ao lote, mantendo o histórico das movimentações anteriores.

---

<h2 align="center">📦 Dados Registrados na Blockchain</h2>

Entre as informações armazenadas estão:

```text
ID do lote
Produto
Origem
Data de produção
Responsável atual
Status
Etapa da cadeia produtiva
Data da movimentação
Carteira responsável
```

Dados pessoais ou documentos extensos não precisam ser armazenados diretamente na Blockchain.

Quando necessário, pode ser registrado apenas o **hash de um documento**, permitindo verificar posteriormente se o arquivo foi alterado.

---

<h2 align="center">📜 Smart Contract</h2>

O Smart Contract do EcoOrigem é responsável por aplicar as regras de negócio e controlar o ciclo de vida de cada lote.

Um lote pode seguir, por exemplo, os seguintes estados:

```text
CADASTRADO
     ↓
BENEFICIADO
     ↓
EM_TRANSPORTE
     ↓
DISTRIBUIDO
     ↓
FINALIZADO
```

O contrato impede alterações incompatíveis com o fluxo definido.

Por exemplo:

```text
CADASTRADO → FINALIZADO
```

A operação deverá ser rejeitada por tentar ignorar etapas obrigatórias.

Também serão aplicadas regras de **controle de acesso**, impedindo que uma carteira sem autorização realize determinadas operações.

---

<h2 align="center">🏗️ Arquitetura</h2>

```text
┌─────────────────────────┐
│      Interface Web      │
│         React           │
└────────────┬────────────┘
             │
             │ Ethers.js
             ▼
┌─────────────────────────┐
│      Smart Contract     │
│        Solidity         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    Blockchain Local     │
│        Hardhat          │
└─────────────────────────┘
             ▲
             │
┌────────────┴────────────┐
│        MetaMask         │
│ Carteiras dos usuários │
└─────────────────────────┘
```

---

<h2 align="center">📁 Estrutura do Projeto</h2>

```text
EcoOrigem/
│
├── assets/
│   └── ecoorigem-logo.png
│
├── contracts/
│   └── EcoOrigem.sol
│
├── scripts/
│   └── deploy.js
│
├── test/
│   └── EcoOrigem.test.js
│
├── frontend/
│   └── ...
│
├── hardhat.config.js
├── package.json
└── README.md
```

---

<h2 align="center">▶️ Como Executar</h2>

### 1. Clonar o repositório

```bash
git clone https://github.com/JulianaBallin/EcoOrigem.git
cd EcoOrigem
```

### 2. Instalar as dependências

```bash
npm install
```

### 3. Iniciar a Blockchain local

```bash
npx hardhat node
```

### 4. Implantar o Smart Contract

Em outro terminal:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

### 5. Executar a aplicação

```bash
cd frontend
npm install
npm run dev
```

A aplicação poderá então interagir com o contrato implantado na Blockchain local utilizando as carteiras configuradas no MetaMask.

---

<h2 align="center">🧪 Testes</h2>

O projeto contempla testes de operações válidas, entradas inválidas e tentativas de acesso sem autorização.

### ✅ Operações válidas

```text
Cadastrar produto
Registrar beneficiamento
Iniciar transporte
Registrar distribuição
Consultar histórico do lote
```

### ❌ Operações inválidas

```text
Alterar lote finalizado
Avançar etapas fora da ordem
Executar operação sem permissão
Manipular lote inexistente
```

Para executar os testes:

```bash
npx hardhat test
```

---

<h2 align="center">🖥️ Funcionalidades</h2>

A interface do EcoOrigem permitirá:

* Cadastrar novos lotes;
* Consultar produtos registrados;
* Atualizar a etapa de um produto;
* Registrar movimentações;
* Visualizar todo o histórico de rastreabilidade;
* Identificar a carteira responsável por cada operação;
* Visualizar informações registradas na Blockchain;
* Demonstrar transações rejeitadas pelo Smart Contract.

---

<h2 align="center">⚠️ Limitações</h2>

O EcoOrigem é desenvolvido como **protótipo acadêmico** utilizando uma Blockchain local.

Nesta versão:

* Não existe integração com uma Blockchain pública;
* Os participantes são simulados por carteiras locais;
* A veracidade do primeiro registro ainda depende do participante responsável pela informação;
* Não existe integração direta com sistemas reais de cooperativas ou produtores;
* Recursos externos, como sensores e certificadoras, não fazem parte do protótipo inicial.

---

<h2 align="center">🚀 Evoluções Futuras</h2>

O projeto poderá futuramente incorporar:

* QR Code para rastrear cada lote;
* Página pública de consulta para consumidores;
* Certificação digital de produtores;
* Registro aproximado da origem geográfica;
* Integração com cooperativas;
* Registro de documentos através de hash;
* Aplicativo mobile;
* Integração com sensores IoT;
* Blockchain permissionada para organizações participantes.

---

<h2 align="center">👥 Equipe</h2>

<div align="center">

| Integrante                        |
| :-------------------------------- |
| **Ana Beatriz Maciel Nunes**      |
| **Fernando Luiz Da Silva Freire** |
| **Juliana Ballin Lima**           |

</div>

---

<h2 align="center">🔗 Repositório</h2>

<p align="center">
  <a href="https://github.com/JulianaBallin/EcoOrigem">
    <img src="https://img.shields.io/badge/GitHub-EcoOrigem-181717?style=for-the-badge&logo=github&logoColor=white">
  </a>
</p>

<p align="center">
  <a href="https://github.com/JulianaBallin/EcoOrigem">
    github.com/JulianaBallin/EcoOrigem
  </a>
</p>

---

<h3 align="center">🌿 EcoOrigem</h3>

<p align="center">
  <strong>Da floresta ao futuro.</strong><br>
  Blockchain • Bioeconomia • Amazônia • Rastreabilidade
</p>
