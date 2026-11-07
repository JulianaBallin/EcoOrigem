# Guia completo da atividade - Entrega 2 do EcoOrigem

Este documento reúne, em uma única sequência, tudo o que precisa ser feito para concluir, testar, implantar, documentar e apresentar a Entrega 2 do EcoOrigem.

O projeto local já contém o contrato Solidity, o frontend, os testes, a documentação e os slides. As etapas que dependem de confirmação humana são o uso da MetaMask, a obtenção de SepoliaETH, o deploy na Sepolia, a verificação no Etherscan, a publicação na Vercel e a gravação das evidências.

> Importante: este arquivo foi criado apenas localmente. Nenhum commit, push, deploy ou publicação foi executado.

## 1. Resultado esperado

Ao final, você deverá ter:

- o contrato `EcoOrigem.sol` implantado na Ethereum Sepolia;
- o código do contrato verificado no Sepolia Etherscan;
- cinco contas de teste na MetaMask, com os perfis necessários;
- o frontend configurado com o endereço, bloco e hash reais do deploy;
- o fluxo completo de um lote executado pelo frontend;
- uma transação pagável com SepoliaETH confirmada;
- eventos e histórico consultáveis;
- pelo menos uma exceção demonstrada e tratada;
- um documento de teste com SHA-256 e, opcionalmente, CID do IPFS;
- a dApp publicada na Vercel por HTTPS;
- README atualizado sem campos `PENDENTE`;
- capturas reais, vídeo de 3 a 5 minutos e slides em PDF;
- uma apresentação de 15 minutos, seguida de 5 minutos de arguição.

Segundo o guia fornecido, a entrega deve ocorrer até **16/11/2026, às 23h59**. Confirme no ambiente da disciplina se a data não foi alterada.

## 2. Materiais que devem orientar a atividade

### 2.1 Documento principal do professor

- [Guia do Trabalho Prático - dApp na Ethereum](../../entrega-2/Guia%20do%20Trabalho%20Prático%20%E2%80%94%20dApp%20na%20Ethereum.pdf)

O documento exige Solidity 0.8.x, MetaMask, Sepolia, Web3.js 4.x, frontend em HTML/CSS/JavaScript puro, Vercel, testes, README, vídeo, slides e apresentação.

### 2.2 Exemplos do material de apoio usados no EcoOrigem

| Material | O que observar | Como aparece no EcoOrigem |
| --- | --- | --- |
| [Curso Solidity](../../entrega-2/material-apoio/curso-solidity/README.md) | Sequência didática dos recursos da linguagem | Organização e justificativa dos sete grupos obrigatórios |
| [Tipos de dados](../../entrega-2/material-apoio/curso-solidity/01-basico/02_TiposDeDados.sol) | `uint256`, `int256`, `bool`, `address`, `bytes32`, `constant` e `immutable` | Taxa, temperatura, proprietário, tesouraria e hashes |
| [Funções](../../entrega-2/material-apoio/curso-solidity/01-basico/03_Funcoes.sol) | Visibilidades, `view`, `pure`, `payable`, `memory` e `calldata` | Funções de negócio, consultas e cadastro pagável |
| [Estruturas de controle](../../entrega-2/material-apoio/curso-solidity/01-basico/04_EstruturasDeControle.sol) | `if/else`, laços e `require` | Validações, paginação e rótulos dos estados |
| [Arrays e mappings](../../entrega-2/material-apoio/curso-solidity/01-basico/05_ArraysEMappings.sol) | Array dinâmico, mapping simples e mapping aninhado | Lotes, documentos, histórico e perfis por carteira |
| [Structs e enums](../../entrega-2/material-apoio/curso-solidity/01-basico/06_StructsEEnums.sol) | Registros compostos e máquina de estados | `Lot`, `Document`, `HistoryEntry`, `Role` e `Status` |
| [Modificadores](../../entrega-2/material-apoio/curso-solidity/02-intermediario/07_Modificadores.sol) | Controle de acesso, pausa e modifier com parâmetro | `onlyOwner`, `onlyRole`, `lotExists`, `atStatus` e `whenRunning` |
| [Eventos e erros](../../entrega-2/material-apoio/curso-solidity/02-intermediario/08_EventosEErros.sol) | Eventos indexados, `require` e erros customizados | Eventos do ciclo e mensagens compreensíveis no frontend |
| [Ether e segurança](../../entrega-2/material-apoio/curso-solidity/02-intermediario/09_EnviandoERecebendoEther.sol) | `payable`, `msg.value`, `call` e checks-effects-interactions | Taxa de cadastro e saque pela tesouraria |
| [Mural de Mensagens](../../entrega-2/material-apoio/dApp/README.md) | Deploy no Remix, ABI, `.call()`, `.send()` e eventos | Integração Web3 completa do frontend |
| [Mural simples](../../entrega-2/material-apoio/mural-simples/README.md) | MetaMask, Sepolia, servidor HTTP e endereço do contrato | Fluxo básico de conexão e execução local |
| [Urna Ledger](../../entrega-2/material-apoio/urna-ledger-mvp-didatico/README.md) | Hash, integridade, ABI e limites do que a blockchain prova | SHA-256 dos documentos e histórico auditável |
| [Deploy da Urna Ledger](../../entrega-2/material-apoio/urna-ledger-mvp-didatico/docs/DEPLOY.md) | Sequência de deploy, teste e demonstração | Ordem operacional usada neste guia |

Os links dessa tabela apontam para o material local da disciplina. Eles servem para estudo e comparação e não exigem que os arquivos do professor sejam copiados para o repositório público.

Os exemplos do professor são didáticos e foram ampliados no EcoOrigem. O padrão central continua o mesmo:

```javascript
// Leitura gratuita, sem alterar o estado.
await contract.methods.totalLots().call();

// Escrita assinada pela MetaMask, com pagamento de gas.
await contract.methods.registerLot(...args).send({
  from: account,
  value: registrationFee,
});
```

## 3. Links oficiais e ferramentas

| Finalidade | Link |
| --- | --- |
| Remix já configurado para Solidity 0.8.34 | [Abrir Remix configurado](https://app.remix.live/#lang=en&optimize&runs=200&evmVersion&version=soljson-v0.8.34+commit.80d5c536.js) |
| Documentação de deploy do Remix | [Deploy & Run](https://remix-ide.readthedocs.io/en/latest/run.html) |
| MetaMask | [Instalar ou abrir MetaMask](https://metamask.com/pt-BR) |
| Exibir redes de teste na MetaMask | [Ajuda oficial da MetaMask](https://support.metamask.io/configure/networks/how-to-view-testnets-in-metamask/) |
| Sepolia PoW Faucet solicitado na atividade | [Obter SepoliaETH](https://sepolia-faucet.pk910.de/#) |
| Explorador da Sepolia | [Sepolia Etherscan](https://sepolia.etherscan.io) |
| Verificação de contrato no Remix | [Plugin de verificação](https://app.remix.live/?#activate=contract-verification) |
| IPFS Desktop | [Instalação oficial](https://docs.ipfs.tech/install/ipfs-desktop/) |
| Tutorial do IPFS Desktop | [Adicionar arquivo e copiar CID](https://docs.ipfs.tech/how-to/desktop-app/) |
| Vercel | [Painel da Vercel](https://vercel.com/new) |
| Deploy pela Vercel | [Documentação oficial](https://vercel.com/docs/deployments) |
| Web3.js | [Documentação do provider](https://docs.web3js.org/guides/web3_providers_guide/) |
| Solidity | [Documentação oficial](https://docs.soliditylang.org) |

Use somente os endereços oficiais ou os links indicados pelo professor. Não instale extensões a partir de anúncios ou links recebidos por mensagem.

## 4. Folha de registro da implantação

Preencha esta tabela enquanto realiza as etapas. Não registre frase de recuperação, chave privada, senha ou token.

| Dado | Valor a preencher |
| --- | --- |
| Endereço da conta Proprietário | `PENDENTE` |
| Endereço da conta Produtor | `PENDENTE` |
| Endereço da conta Beneficiador | `PENDENTE` |
| Endereço da conta Transportador | `PENDENTE` |
| Endereço da conta Distribuidor | `PENDENTE` |
| Endereço do contrato | `PENDENTE` |
| Hash da transação de deploy | `PENDENTE` |
| Bloco do deploy | `PENDENTE` |
| Link do contrato no Etherscan | `PENDENTE` |
| Data e hora do deploy | `PENDENTE` |
| URL da Vercel | `PENDENTE` |
| Link do vídeo | `PENDENTE` |

## 5. Etapa 1 - Abrir o projeto e conferir o ambiente local

Abra um terminal e execute:

```bash
cd /home/cronos-1226/Documentos/Uea/oficina-desenvolvimento-sistemas-iii/entrega-1/EcoOrigem
git branch --show-current
git status --short --branch
node --version
npm --version
make help
```

Resultados esperados:

- branch atual: `develop`;
- Node.js 20 ou superior;
- npm disponível;
- menu com os comandos `install`, `compile`, `abi`, `configure`, `test`, `validate`, `security`, `check`, `serve` e `slides`;
- alterações locais ainda não publicadas listadas pelo Git.

Não use `git reset`, `git checkout --`, `git clean` ou outro comando que descarte alterações. O projeto contém trabalho local da Entrega 2 que ainda não foi enviado.

## 6. Etapa 2 - Instalar e validar o projeto local

Execute:

```bash
npm ci
make check
make security
```

Resultado esperado do `make check`:

- contrato compilado com Solidity `0.8.34`;
- optimizer com `200` runs;
- EVM `paris`;
- bytecode implantado de aproximadamente `13.592` bytes, abaixo do limite da EVM;
- ABI sincronizada em `frontend/contract.js`;
- arquivos do frontend validados;
- duas suítes de teste aprovadas;
- 57 verificações internas cobertas pelos testes.

O `make security` deve informar que a publicação não possui dependências npm de produção. Alertas de Ganache, Solc ou ferramentas de teste permanecem no ambiente local e não são enviados para a Vercel.

Se `npm ci` falhar por conexão, tente novamente quando a internet estiver estável. Não use `npm audit fix --force`, pois isso pode trocar versões e quebrar a compatibilidade do projeto.

## 7. Etapa 3 - Preparar as contas da MetaMask

O fluxo completo usa cinco papéis. A forma mais simples é criar cinco contas dentro de uma carteira de teste da MetaMask.

| Nome sugerido na MetaMask | Papel no contrato | Responsabilidade |
| --- | --- | --- |
| EcoOrigem Proprietário | `owner` | Deploy, perfis, pausa e saque |
| EcoOrigem Produtor | `Producer` | Cadastra o lote e paga a taxa |
| EcoOrigem Beneficiador | `Processor` | Registra beneficiamento |
| EcoOrigem Transportador | `Carrier` | Inicia transporte |
| EcoOrigem Distribuidor | `Distributor` | Confirma e finaliza o lote |

Passo a passo:

1. Instale a [MetaMask](https://metamask.com/pt-BR) no navegador que será usado no Remix e na dApp.
2. Crie uma carteira exclusiva para a disciplina ou use uma carteira de teste já separada.
3. Guarde a frase de recuperação fora do computador e do repositório.
4. Nunca mostre a frase durante gravações ou compartilhamento de tela.
5. No seletor de redes da MetaMask, ative **Mostrar redes de teste**.
6. Selecione **Ethereum Sepolia**.
7. Confirme o Chain ID `11155111`, representado em hexadecimal por `0xaa36a7`.
8. Crie ou importe as cinco contas de teste.
9. Renomeie cada conta conforme a tabela.
10. Copie apenas os endereços públicos e preencha a folha de registro deste guia.

Não é necessário criar usuário e senha dentro da dApp. O exemplo do professor usa a MetaMask como provider e identidade. No EcoOrigem, a pessoa conecta a carteira e assina um desafio sem gas. A autorização real é conferida pelo contrato com o endereço e o perfil on-chain.

## 8. Etapa 4 - Obter SepoliaETH

SepoliaETH é moeda de teste e não possui valor real.

1. Selecione a conta **EcoOrigem Proprietário** na MetaMask.
2. Copie o endereço público da conta.
3. Abra o [Sepolia PoW Faucet](https://sepolia-faucet.pk910.de/#).
4. Cole o endereço público no campo solicitado.
5. Siga a etapa de mineração ou prova de trabalho exibida pelo faucet.
6. Solicite o envio quando o saldo mínimo exigido pelo site for alcançado.
7. Aguarde a transação aparecer na MetaMask ou no [Sepolia Etherscan](https://sepolia.etherscan.io).
8. Repita para as contas Produtor, Beneficiador, Transportador e Distribuidor.

Todas as cinco contas enviam transações e precisam de saldo para gas. A conta Produtor também envia a taxa de `0.00001 ether` no cadastro do lote.

Recomendação de preparação:

- coloque mais saldo na conta Proprietário, pois ela realiza deploy e quatro concessões de perfil;
- garanta saldo para pelo menos duas tentativas em cada conta operacional;
- prepare tudo antes da apresentação, pois faucets podem ficar lentos ou indisponíveis;
- nunca compre SepoliaETH e nunca informe chave privada ao faucet.

## 9. Etapa 5 - Fazer um ensaio no Remix VM

Esta etapa segue o padrão dos exemplos `Mural de Mensagens` e `Mural simples`. Ela serve para conferir o contrato no ambiente didático antes de gastar SepoliaETH.

1. Abra o [Remix configurado](https://app.remix.live/#lang=en&optimize&runs=200&evmVersion&version=soljson-v0.8.34+commit.80d5c536.js).
2. No explorador do Remix, crie a pasta `contracts` se ela não existir.
3. Crie o arquivo `contracts/EcoOrigem.sol`.
4. Abra o arquivo local [contracts/EcoOrigem.sol](contracts/EcoOrigem.sol).
5. Copie todo o conteúdo para o arquivo criado no Remix.
6. Abra **Solidity Compiler**.
7. Selecione `0.8.34+commit.80d5c536`.
8. Ative **Enable optimization**.
9. Defina `Runs` como `200`.
10. Em **Advanced Configurations**, escolha EVM `paris`.
11. Clique em **Compile EcoOrigem.sol**.
12. Confira que não há erro de compilação.
13. Abra **Deploy & Run Transactions**.
14. Escolha uma **Remix VM** apenas para este ensaio.
15. Mantenha **Value = 0**.
16. Selecione o contrato `EcoOrigem`.
17. Clique em **Deploy**.
18. Expanda o contrato em **Deployed Contracts**.
19. Consulte `owner`, `treasury`, `REGISTRATION_FEE`, `paused` e `totalLots`.

O valor de `owner` deve ser a primeira conta selecionada na Remix VM. `REGISTRATION_FEE` aparecerá em wei como `10000000000000`.

Para um ensaio rápido de controle de acesso:

1. Copie o endereço de outra conta da Remix VM.
2. Na conta proprietária, chame `grantRole` com o endereço e valor `1`.
3. Consulte `hasRole` com o mesmo endereço e valor `1`.
4. O retorno deve ser `true`.
5. Troque para essa conta.
6. Chame `registerLot` com os parâmetros do exemplo abaixo.
7. Antes de confirmar, defina **Value** como `0.00001` e a unidade como `ether`.

Exemplo de argumentos no Remix:

| Campo | Exemplo |
| --- | --- |
| `product` | `Acai` |
| `origin` | `Comunidade do Careiro, Amazonas` |
| `quantityGrams` | `250000` |
| `harvestedAt` | um timestamp Unix de uma data passada |
| `processor` | endereço da conta que será beneficiadora |

Este ensaio não substitui o deploy na Sepolia. O contrato da Remix VM existe apenas no navegador e não pode ser acessado pelo frontend conectado à Sepolia.

## 10. Etapa 6 - Compilar para o deploy real

Antes do deploy real, repita as configurações exatamente:

| Configuração | Valor correto |
| --- | --- |
| Arquivo | `contracts/EcoOrigem.sol` |
| Compilador | `0.8.34+commit.80d5c536` |
| Optimizer | habilitado |
| Runs | `200` |
| EVM version | `paris` |
| Constructor arguments | nenhum |
| Value do deploy | `0` |

Tire a captura `docs/prints/01-remix-compilacao.png` mostrando a versão, optimizer, runs e o sucesso da compilação.

Não faça alterações somente no Remix. Se o contrato precisar ser corrigido, altere primeiro o arquivo local, rode `make check` e depois copie novamente para o Remix.

## 11. Etapa 7 - Implantar na Ethereum Sepolia

1. Na MetaMask, selecione **EcoOrigem Proprietário**.
2. Confirme que a rede é **Ethereum Sepolia**.
3. Confirme que existe SepoliaETH suficiente para gas.
4. No Remix, abra **Deploy & Run Transactions**.
5. Em **Environment**, escolha **Browser Extension** ou **Injected Provider - MetaMask**.
6. Autorize a conexão do Remix na MetaMask, se solicitado.
7. Confira se o Remix mostra a rede `11155111`.
8. Em **Account**, confira o endereço do Proprietário.
9. Em **Contract**, selecione `EcoOrigem`.
10. Mantenha **Value = 0**.
11. Clique em **Deploy**.
12. Na MetaMask, revise a rede, o site solicitante e a estimativa de gas.
13. Confirme a transação.
14. Aguarde a confirmação. Não clique em Deploy novamente enquanto a primeira transação estiver pendente.
15. Em **Deployed Contracts**, copie o endereço do contrato.

O endereço do contrato não é o endereço da carteira. O contrato tem um endereço próprio com 42 caracteres, iniciado por `0x`.

Tire a captura `docs/prints/02-remix-deploy.png` mostrando o ambiente de browser, a rede e o contrato implantado, sem expor informações sensíveis.

## 12. Etapa 8 - Registrar os dados no Etherscan

1. Abra o [Sepolia Etherscan](https://sepolia.etherscan.io).
2. Pesquise o hash da transação de deploy ou o endereço do contrato.
3. Confirme que o status é **Success**.
4. Confirme que **From** é a conta Proprietário.
5. Confirme que **To** indica criação de contrato.
6. Copie o hash da transação.
7. Copie o número do bloco.
8. Copie o endereço do contrato criado.
9. Copie a URL da página do contrato.
10. Preencha a folha de registro deste guia.

Tire a captura `docs/prints/03-etherscan-contrato.png` mostrando endereço, criador, bloco e rede Sepolia.

## 13. Etapa 9 - Verificar o código do contrato

### Opção A - Plugin de verificação do Remix

1. Abra o [plugin Contract Verification](https://app.remix.live/?#activate=contract-verification).
2. Ative o plugin no Remix.
3. Se for solicitada uma chave de API do Etherscan, informe-a apenas na interface do plugin.
4. Não salve a chave no código, em `.env`, em comando de terminal ou neste guia.
5. Selecione o contrato implantado.
6. Envie o código e os metadados da compilação.
7. Aguarde a confirmação dos serviços de verificação.

### Opção B - Verificação pela página do Etherscan

1. Na página do contrato, abra **Contract**.
2. Clique em **Verify and Publish** se o código ainda não estiver verificado.
3. Escolha **Solidity (Single file)**.
4. Selecione `v0.8.34+commit.80d5c536`.
5. Marque optimizer **Yes**.
6. Informe `200` runs.
7. Selecione EVM `paris`.
8. Cole exatamente o conteúdo local de `contracts/EcoOrigem.sol`.
9. Não informe argumentos do construtor.
10. Conclua a verificação.

Resultado esperado:

- aba **Code** exibindo o código Solidity;
- opções **Read Contract** e **Write Contract** disponíveis;
- versão e configurações iguais às usadas no deploy.

Se a verificação falhar, não faça outro deploy imediatamente. Confira primeiro versão do compilador, optimizer, runs, EVM, conteúdo do arquivo e argumentos do construtor.

Tire a captura `docs/prints/04-etherscan-verificado.png`.

## 14. Etapa 10 - Configurar o frontend com o contrato real

No terminal, dentro da raiz do EcoOrigem, execute:

```bash
make abi
make configure \
  ADDRESS=0xENDERECO_DO_CONTRATO \
  BLOCK=NUMERO_DO_BLOCO \
  TX=0xHASH_DA_TRANSACAO_DE_DEPLOY
make check
```

Substitua os três valores pelos dados reais. Não mantenha os textos de exemplo.

O endereço deve ter 40 caracteres hexadecimais após `0x`. O hash deve ter 64 caracteres hexadecimais após `0x`. O bloco deve ser um número inteiro positivo.

Confira o resultado:

```bash
rg 'CONTRACT_ADDRESS|DEPLOYMENT_BLOCK|DEPLOYMENT_TX' frontend/contract.js
```

O arquivo [frontend/contract.js](frontend/contract.js) deve mostrar:

```javascript
export const CONTRACT_ADDRESS = "0xENDERECO_REAL";
export const DEPLOYMENT_BLOCK = 12345678;
export const DEPLOYMENT_TX = "0xHASH_REAL";
```

Não altere manualmente a ABI sem recompilar. Assim como nos exemplos `Mural de Mensagens` e `Urna Ledger`, ABI e contrato precisam corresponder exatamente.

## 15. Etapa 11 - Executar o frontend localmente

Inicie o servidor:

```bash
make serve
```

Abra no mesmo navegador em que a MetaMask está instalada:

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

Não abra `frontend/index.html` diretamente com `file://`. O material de apoio também usa um servidor HTTP porque a injeção do provider e os módulos JavaScript dependem do contexto do navegador.

Checklist inicial:

1. A página deve abrir sem banner de contrato não configurado.
2. O indicador deve mostrar MetaMask desconectada.
3. Clique em **Conectar e autenticar**.
4. Autorize apenas as contas de teste.
5. Se estiver em outra rede, clique no indicador e autorize a troca para Sepolia.
6. Assine o desafio de autenticação.
7. A assinatura não deve cobrar gas.
8. Confira endereço, saldo e perfil.
9. Confira o endereço do contrato com link para o Etherscan.
10. Abra **Visão geral** e confira taxa, total de lotes, pausa e saldo do contrato.

O frontend usa o mesmo fluxo conceitual dos exemplos:

- `window.ethereum` fornece o provider da MetaMask;
- `new Web3(window.ethereum)` cria a conexão;
- `.call()` consulta sem transação;
- `.send()` solicita uma transação assinada;
- `getPastEvents()` busca eventos;
- `accountsChanged` e `chainChanged` atualizam a interface.

## 16. Etapa 12 - Conceder os quatro perfis

O proprietário possui acesso administrativo pelo próprio contrato. Conecte a conta **EcoOrigem Proprietário**.

1. Abra a aba **Administração**.
2. Informe o endereço da conta Produtor.
3. Escolha **Produtor**.
4. Clique em **Conceder**.
5. Confirme na MetaMask e aguarde o bloco.
6. Repita para Beneficiador, Transportador e Distribuidor.

Valores do enum usados pelo contrato:

| Perfil | Valor |
| --- | --- |
| `None` | `0` |
| `Producer` | `1` |
| `Processor` | `2` |
| `Carrier` | `3` |
| `Distributor` | `4` |

Se preferir fazer a configuração inicial pelo Remix, chame `grantRole(account, role)` quatro vezes na conta Proprietário. Depois de cada transação, consulte `hasRole(account, role)`. O retorno deve ser `true`.

Na aba **Eventos**, confirme quatro eventos `RoleUpdated`.

## 17. Etapa 13 - Executar o fluxo principal completo

Use dados fictícios. Não use documentos pessoais, dados sensíveis ou informações comerciais reais.

### 17.1 Cadastrar o lote como Produtor

1. Troque para a conta **EcoOrigem Produtor** na MetaMask.
2. A dApp deve invalidar a sessão anterior.
3. Clique em **Autenticar carteira** e assine o novo desafio.
4. Abra **Cadastrar lote**.
5. Preencha:

| Campo | Valor de exemplo |
| --- | --- |
| Produto | `Açaí` |
| Origem | `Comunidade do Careiro, Amazonas` |
| Quantidade | `250` kg |
| Data da coleta | uma data passada |
| Carteira do beneficiador | endereço da conta Beneficiador |

6. Clique em **Revisar e cadastrar lote**.
7. Confira na MetaMask que existe `value` de `0.00001 SepoliaETH`, além do gas.
8. Confirme a transação.
9. Na janela da dApp, observe o estado pendente.
10. Depois da confirmação, copie ou abra o hash no Etherscan.
11. Abra **Lotes** e localize o lote `#1`, ou o próximo ID disponível.
12. Confira produto, origem, quantidade, produtor, beneficiador e estado **Cadastrado**.

Este passo é a transação pagável exigida pelo professor. O frontend obtém a taxa do próprio contrato e a envia em `value`.

### 17.2 Anexar uma prova documental como custodiante

Enquanto o Produtor ainda é o custodiante:

1. Crie um arquivo de texto fictício, por exemplo `declaracao-lote-1.txt`.
2. Não coloque dados pessoais no arquivo.
3. Abra **Documentos**.
4. Informe o ID do lote.
5. Use a descrição `Declaração fictícia de origem`.
6. Selecione o arquivo.
7. Deixe o CID vazio neste primeiro teste, se ainda não tiver usado IPFS.
8. Clique em **Calcular hash e registrar**.
9. Confirme a transação.
10. Abra o detalhe do lote e confira o SHA-256, autor e horário.

O navegador calcula o hash. O arquivo não é enviado para a blockchain. Essa separação segue a ideia de integridade demonstrada no exemplo `Urna Ledger`.

### 17.3 Registrar beneficiamento como Beneficiador

1. Troque para **EcoOrigem Beneficiador**.
2. Autentique a nova conta.
3. Abra **Operações**.
4. No formulário **Registrar beneficiamento**, informe:
   - ID do lote;
   - descrição `Polpa beneficiada e lote inspecionado`;
   - carteira da conta Transportador;
   - laudo fictício e CID opcional.
5. Clique em **Registrar beneficiamento**.
6. Confirme na MetaMask.
7. Confira o estado **Beneficiado** e o evento `LotStatusChanged`.

Somente o beneficiador designado no cadastro pode executar esta etapa, e a carteira do transportador precisa possuir o perfil `Carrier`.

### 17.4 Iniciar transporte como Transportador

1. Troque para **EcoOrigem Transportador**.
2. Autentique a carteira.
3. Abra **Operações**.
4. No formulário **Iniciar transporte**, informe:
   - ID do lote;
   - carteira da conta Distribuidor;
   - destino `Manaus, Amazonas`;
   - temperatura `24` graus Celsius.
5. Confirme a transação.
6. Confira o estado **Em transporte**.
7. Confira temperatura, destino, transportador e distribuidor.

O frontend converte `24` para `24000`, pois o contrato armazena milésimos de grau sem usar números decimais.

### 17.5 Confirmar recebimento como Distribuidor

1. Troque para **EcoOrigem Distribuidor**.
2. Autentique a carteira.
3. Abra **Operações**.
4. Em **Confirmar recebimento**, informe o ID do lote.
5. Use a observação `Recebido sem avarias`.
6. Confirme a transação.
7. Confira o estado **Distribuído**.

### 17.6 Finalizar o lote como Distribuidor

1. Ainda na conta Distribuidor, abra **Operações**.
2. Em **Finalizar lote**, informe o ID.
3. Use a observação `Cadeia de custódia concluída`.
4. Confirme a transação.
5. Abra o detalhe do lote.
6. Confira o estado **Finalizado**.
7. Confira as cinco entradas do histórico:
   - Cadastrado;
   - Beneficiado;
   - Em transporte;
   - Distribuído;
   - Finalizado.

Depois da finalização, o lote não aceita novos documentos ou mudanças de estado.

## 18. Etapa 14 - Adicionar um documento no IPFS

O contrato aceita o CID como referência opcional. Para demonstrar IPFS sem colocar token no frontend, use o IPFS Desktop.

1. Instale o [IPFS Desktop](https://docs.ipfs.tech/install/ipfs-desktop/).
2. Abra o aplicativo e confirme o estado conectado.
3. Entre na aba **Files**.
4. Clique em **Import** e depois em **File**.
5. Selecione um documento fictício de teste.
6. Aguarde a importação.
7. No menu do arquivo, clique em **Copy CID**.
8. No EcoOrigem, informe o CID no formato `ipfs://CID` ou cole somente o CID.
9. Selecione exatamente o mesmo arquivo para que o frontend calcule o SHA-256.
10. Registre o documento.
11. Abra o detalhe do lote e use o link **Abrir IPFS**.

O CID do IPFS e o SHA-256 calculado pelo frontend podem ser diferentes. O CID inclui informações de versão, codec e estrutura de conteúdo do IPFS. O SHA-256 do EcoOrigem é uma prova direta dos bytes selecionados no navegador.

Manter um arquivo apenas no IPFS Desktop não garante disponibilidade permanente quando o seu computador estiver desligado. Para disponibilidade contínua, seria necessário manter um nó ou usar um serviço de pinning. Se usar pinning, não coloque token no repositório ou no frontend.

## 19. Etapa 15 - Testar as exceções obrigatórias

Execute pelo menos uma exceção durante a apresentação e todas durante a preparação.

| ID | Teste | Como executar | Resultado esperado |
| --- | --- | --- | --- |
| E01 | Conta sem perfil | Tentar cadastrar com uma sexta conta | Mensagem de carteira sem perfil Produtor |
| E02 | Cancelamento | Iniciar uma escrita e clicar em rejeitar na MetaMask | Solicitação cancelada e estado inalterado |
| E03 | Ator diferente | Processar com outro Beneficiador | Mensagem indicando a carteira designada |
| E04 | Estado incorreto | Confirmar entrega antes do transporte | Estado atual e estado esperado na mensagem |
| E05 | Temperatura inválida | Informar `70` graus | Validação entre `-30` e `60` graus |
| E06 | Documento duplicado | Anexar o mesmo arquivo duas vezes | Documento já registrado |
| E07 | Lote finalizado | Tentar anexar documento depois da finalização | Operação bloqueada |
| E08 | Contrato pausado | Proprietário pausa e Produtor tenta cadastrar | Mensagem de contrato pausado |
| E09 | Administração indevida | Conta comum tenta chamar função de proprietário | Carteira não autorizada |
| E10 | Saque vazio | Proprietário saca duas vezes sem novo cadastro | Mensagem de ausência de taxas |

Depois de cada erro:

1. leia a mensagem apresentada pela dApp;
2. feche a janela de transação;
3. consulte novamente o lote;
4. confirme que o estado não mudou;
5. lembre que uma transação revertida já enviada à rede pode consumir gas.

Para o vídeo e a apresentação, a exceção mais simples é usar uma conta sem perfil para tentar cadastrar um lote ou tentar uma operação fora da ordem.

## 20. Etapa 16 - Testar administração, conta e rede

### Administração

1. Conecte o Proprietário.
2. Pause o contrato.
3. Confira `paused = true` e o evento `PauseChanged`.
4. Faça uma consulta para demonstrar que leituras continuam disponíveis.
5. Tente uma escrita e confira o bloqueio.
6. Retome o contrato.
7. Use **Sacar taxas**.
8. Confira `FeesWithdrawn` e o saldo do contrato zerado.

### Troca de conta

1. Com a dApp aberta, troque de conta na MetaMask.
2. Confira que a autenticação anterior foi invalidada.
3. Autentique a nova conta.
4. Confira que o perfil exibido mudou.

### Troca de rede

1. Troque temporariamente para outra rede na MetaMask.
2. Confira o aviso da dApp.
3. Clique no indicador de rede.
4. Autorize `wallet_switchEthereumChain` para Sepolia.
5. Confira que as consultas voltaram a funcionar.

## 21. Etapa 17 - Conferir eventos e Etherscan

1. Abra a aba **Eventos**.
2. Clique em **Buscar eventos**.
3. Localize `RoleUpdated`, `LotRegistered`, `LotStatusChanged`, `DocumentAttached`, `PauseChanged` e `FeesWithdrawn`, conforme as ações executadas.
4. Abra o link de uma transação no Etherscan.
5. Compare o hash, bloco e remetente com a dApp.
6. Confira que os parâmetros `indexed` podem ser usados como tópicos de pesquisa.

Assim como explicado no exemplo `Urna Ledger`, `indexed` melhora a filtragem de logs, mas não torna a informação verdadeira. A blockchain comprova que determinado endereço registrou os dados naquela transação. Ela não comprova sozinha que a origem física do produto é verdadeira.

## 22. Etapa 18 - Conferir responsividade e acessibilidade

No navegador, abra as ferramentas de desenvolvimento e teste:

- celular com largura de `390 px`;
- tablet com largura de `768 px`;
- desktop com largura de `1440 px`.

Confira:

- ausência de rolagem horizontal;
- campos e botões legíveis;
- navegação por teclado;
- foco visível;
- mensagens compreensíveis sem depender somente de cor;
- tabelas e cartões sem sobreposição;
- animações reduzidas quando o sistema solicita redução de movimento.

Tire a captura `docs/prints/12-mobile.png`.

## 23. Etapa 19 - Publicar na Vercel somente quando estiver pronta

> Não execute esta etapa agora se você ainda está revisando localmente. Ela é a etapa futura de publicação exigida pelo professor.

Antes de publicar:

```bash
make check
make security
git status --short --branch
git diff --check
git diff
```

Confirme que `frontend/contract.js` possui o contrato definitivo. Não publique com `CONTRACT_ADDRESS` vazio.

Quando a revisão estiver concluída e houver autorização para enviar:

1. Revise cada arquivo mostrado por `git status`.
2. Confirme que não há segredo, `.env`, chave, frase de recuperação ou token.
3. Faça o commit conforme o fluxo da equipe.
4. Envie a versão final ao GitHub.
5. Abra o [painel de novo projeto da Vercel](https://vercel.com/new).
6. Entre com a conta autorizada da equipe.
7. Importe `JulianaBallin/EcoOrigem`.
8. Escolha **Other** como framework.
9. Use a raiz do repositório como **Root Directory**.
10. O arquivo `vercel.json` já define:
    - Build Command: `npm run build`;
    - Output Directory: `frontend`;
    - URLs limpas.
11. Não crie variáveis de ambiente. A dApp não usa segredo ou backend.
12. Clique em **Deploy**.
13. Aguarde o status **Ready**.
14. Abra a URL `https://<projeto>.vercel.app` no navegador com MetaMask.
15. Repita conexão, leitura, cadastro pagável, evento, erro e link do Etherscan.

Cada push futuro para a branch conectada pode gerar outro deploy. Por isso, faça a publicação somente depois de revisar os dados do contrato.

Tire a captura `docs/prints/05-vercel-inicio.png` com a URL HTTPS, rede Sepolia e carteira conectada.

## 24. Etapa 20 - Produzir as capturas

Salve capturas reais em [docs/prints](docs/prints/README.md):

| Arquivo | Conteúdo |
| --- | --- |
| `01-remix-compilacao.png` | Solidity 0.8.34, optimizer e 200 runs |
| `02-remix-deploy.png` | Browser Extension e contrato implantado |
| `03-etherscan-contrato.png` | Endereço, criador e bloco |
| `04-etherscan-verificado.png` | Código verificado |
| `05-vercel-inicio.png` | URL HTTPS e Sepolia |
| `06-cadastro-pendente.png` | Transação pendente |
| `07-cadastro-confirmado.png` | Hash e bloco confirmados |
| `08-lote-historico.png` | Estado, atores e histórico |
| `09-eventos.png` | Eventos do contrato |
| `10-erro-tratado.png` | Exceção compreensível |
| `11-documento-ipfs.png` | SHA-256 e CID |
| `12-mobile.png` | Interface com 390 px |

Regras para as imagens:

- mantenha visível a informação que comprova o contexto;
- nunca capture frase de recuperação, chave privada, token ou QR de backup;
- oculte dados pessoais que não fazem parte da atividade;
- não edite hashes ou endereços;
- use a mesma instância de contrato informada no README.

## 25. Etapa 21 - Atualizar toda a documentação final

Depois do deploy e da publicação, substitua os campos `PENDENTE`.

### README

No [README.md](README.md), preencha:

- endereço do contrato;
- hash e bloco do deploy;
- link do Sepolia Etherscan;
- URL da Vercel;
- link do vídeo;
- integrantes e papéis definitivos, caso ainda estejam genéricos.

### Guia de deploy

No arquivo [docs/deploy-sepolia.md](docs/deploy-sepolia.md), preencha:

- contrato;
- transação;
- bloco;
- proprietário;
- Etherscan;
- data e hora;
- URL e commit da Vercel.

### Evidências

No arquivo [docs/prints/README.md](docs/prints/README.md):

1. confirme a presença das 12 capturas;
2. remova o aviso de evidências pendentes;
3. confira se nenhuma imagem expõe informação sensível.

### Verificação de pendências

Execute:

```bash
rg -n 'PENDENTE|CONTRACT_ADDRESS = ""|DEPLOYMENT_BLOCK = 0|DEPLOYMENT_TX = ""' \
  README.md docs frontend/contract.js
```

Antes da entrega, esse comando não deve encontrar campos obrigatórios sem preenchimento.

## 26. Etapa 22 - Gravar o vídeo de 3 a 5 minutos

Use a URL da Vercel e o contrato definitivo. Não faça deploy durante a gravação.

Roteiro recomendado:

| Tempo | Ação | Explicação |
| --- | --- | --- |
| 0:00 | Abrir a Vercel | Frontend estático conectado à Sepolia |
| 0:20 | Conectar e autenticar | Provider MetaMask e assinatura sem gas |
| 0:50 | Mostrar saldo e perfil | Identidade pelo endereço e papel on-chain |
| 1:10 | Consultar lotes | Leitura por `.call()` |
| 1:35 | Cadastrar lote | Escrita por `.send()` e taxa em `value` |
| 2:15 | Mostrar pendente e confirmado | Hash, bloco e link do Etherscan |
| 2:50 | Abrir detalhes e histórico | Struct, enum e máquina de estados |
| 3:20 | Mostrar eventos | Logs indexados com `getPastEvents()` |
| 3:45 | Provocar um erro | Perfil ou estado inválido tratado |
| 4:20 | Mostrar documento | SHA-256 e referência IPFS |
| 4:45 | Encerrar | Contrato aplica regras e blockchain preserva registros |

Se a gravação precisar ser mais curta, mantenha conexão, leitura, transação pagável, confirmação, evento e erro.

Publique o vídeo em um local acessível ao professor e teste o link em uma janela anônima.

## 27. Etapa 23 - Ensaiar a apresentação de 15 minutos

Use os arquivos:

- [apresentacao-ecoorigem.pdf](docs/slides/apresentacao-ecoorigem.pdf);
- [apresentacao-ecoorigem.pptx](docs/slides/apresentacao-ecoorigem.pptx);
- [roteiro-apresentacao.md](docs/slides/roteiro-apresentacao.md);
- [demonstracao-local.md](docs/demonstracao-local.md).

Divisão sugerida pelo professor:

| Bloco | Tempo | Conteúdo |
| --- | --- | --- |
| Problema e solução | 2 min | Bioeconomia, atores e necessidade de rastreabilidade |
| Arquitetura | 2 min | Contrato, MetaMask, Sepolia, Web3.js, IPFS e Vercel |
| Contrato | 4 min | Sete grupos de Solidity, acesso, eventos, erros e segurança |
| Demonstração | 5 min | Conexão, leitura, cadastro pagável, evento e erro |
| Lições aprendidas | 2 min | Gas, limites, segurança e melhorias |
| Arguição | 5 min | Respostas individuais |

Todos os integrantes precisam falar e entender contrato e frontend, não apenas a própria parte.

Prepare antes da apresentação:

- MetaMask aberta na Sepolia;
- pelo menos duas contas com saldo;
- Vercel, Etherscan e slides em abas separadas;
- um lote pronto para consulta;
- dados de um novo lote já anotados;
- vídeo e capturas como plano B;
- notificações antigas da MetaMask fechadas.

## 28. O que explicar na arguição

### Por que blockchain?

Os atores pertencem a organizações diferentes e registram etapas sucessivas. O contrato mantém um histórico público, ordenado e auditável das declarações assinadas por cada carteira. A blockchain reduz a dependência de um banco controlado por um único participante, mas não comprova sozinha que o produto físico ou a informação de origem são verdadeiros.

### Por que MetaMask em vez de usuário e senha?

O frontend é estático e não possui um servidor confiável para guardar senhas e sessões. Uma senha implementada apenas em JavaScript poderia ser contornada. A MetaMask prova o controle da carteira por assinatura, e o contrato valida os perfis pelo endereço.

### Diferença entre leitura e escrita

- `.call()` consulta estado e não cria transação;
- `.send()` altera estado, solicita assinatura e paga gas;
- assinar o desafio de autenticação não altera a blockchain e não paga gas.

### Por que ABI e endereço são necessários?

O endereço identifica a instância do contrato na Sepolia. A ABI descreve as funções, parâmetros, retornos, eventos e erros. Se a ABI não corresponder ao contrato implantado, o frontend pode codificar ou interpretar os dados de forma incorreta.

### Por que usar eventos?

Eventos são logs eficientes para interfaces e indexadores. O frontend usa `getPastEvents()` para exibir o histórico recente e vincular cada evento à transação no Etherscan.

### Por que armazenar hash e CID, não o arquivo?

Arquivos grandes são caros para armazenar na Ethereum. O EcoOrigem registra SHA-256, descrição, autor e URI IPFS. O conteúdo permanece fora da blockchain. Uma alteração nos bytes produz outro hash.

### O que `indexed` significa?

Um parâmetro `indexed` fica nos tópicos do log e pode ser filtrado com eficiência. Isso não valida a veracidade do valor.

### Como o contrato evita etapas fora de ordem?

O enum `Status` representa a máquina de estados. O modifier `atStatus` exige o estado esperado, e cada função confere o perfil e a carteira designada.

### Como o saque segue segurança?

O contrato consulta o saldo, faz a interação externa com `call`, verifica o retorno e emite `FeesWithdrawn`. Não existe saldo interno por usuário sendo atualizado depois da chamada. O padrão foi inspirado na aula de envio e recebimento de Ether.

## 29. Mapa dos requisitos obrigatórios no contrato

| Grupo | Implementação no EcoOrigem | Justificativa |
| --- | --- | --- |
| Tipos de dados | `uint256`, `int256`, `bool`, `address`, `address payable`, `string`, `bytes32`, `constant`, `immutable` | Representar valores, identidades, texto, hashes e configuração imutável |
| Funções | `external`, `public`, `internal`, `private`, `view`, `pure`, `payable`, constructor | Separar API, consultas, utilitários, pagamento e inicialização |
| Estruturas de controle | `if/else`, `for`, `require` | Validar dados, estados, paginação e regras |
| Arrays e mappings | `lotIds`, documentos, histórico, lotes e perfis aninhados | Guardar coleções e acesso eficiente por chave |
| Structs e enums | `Lot`, `Document`, `HistoryEntry`, `Role`, `Status` | Modelar o domínio e a máquina de estados |
| Modificadores | `onlyOwner`, `onlyRole`, `lotExists`, `atStatus`, `whenRunning` | Reutilizar validações e controle de acesso |
| Eventos e erros | seis eventos e nove erros customizados | Permitir auditoria, filtros e mensagens específicas |

Funções de negócio públicas ou externas:

- `grantRole`;
- `revokeRole`;
- `setPaused`;
- `registerLot`;
- `recordProcessing`;
- `startTransport`;
- `confirmDelivery`;
- `finalizeLot`;
- `attachDocument`;
- `withdrawFees`.

Consultas principais:

- `hasRole`;
- `totalLots`;
- `getLot`;
- `getLots`;
- `getDocuments`;
- `getHistory`;
- `statusLabel`.

## 30. Solução de problemas

### MetaMask não aparece no Remix

1. Confirme que a extensão está instalada e desbloqueada.
2. Recarregue o Remix.
3. Escolha **Browser Extension**.
4. Autorize o domínio do Remix na MetaMask.
5. Use Chrome, Firefox ou Brave atualizado.

### Remix está na rede errada

1. Troque a MetaMask para Ethereum Sepolia.
2. Feche e reabra o seletor de ambiente do Remix.
3. Confirme Chain ID `11155111` antes do deploy.

### Deploy fica pendente

1. Abra a atividade da MetaMask.
2. Copie o hash e consulte o Etherscan.
3. Aguarde a rede.
4. Não envie vários deploys iguais.
5. Se falhar, leia o motivo antes de repetir.

### Verificação do contrato falha

Confira:

- compilador `v0.8.34+commit.80d5c536`;
- optimizer habilitado;
- `200` runs;
- EVM `paris`;
- arquivo completo e sem alteração posterior;
- ausência de argumentos no construtor.

### Frontend mostra contrato não configurado

Execute novamente:

```bash
make configure ADDRESS=0x... BLOCK=123 TX=0x...
make check
```

Depois, pare e reinicie `make serve` e recarregue a página.

### MetaMask não conecta em `file://`

Use:

```bash
make serve
```

Abra `http://127.0.0.1:8000`.

### Aba Administração não aparece

1. Confirme que a conta conectada é a mesma que fez o deploy.
2. Confira `owner` no Etherscan ou Remix.
3. Troque para a conta Proprietário.
4. Autentique novamente.

### Perfil não aparece

1. Confirme o endereço exato.
2. Consulte `hasRole(address, role)` no Remix.
3. Confira o evento `RoleUpdated`.
4. Troque de conta e autentique novamente.

### Operação retorna carteira designada

A carteira possui o perfil, mas não foi escolhida para aquele lote. Consulte o lote e use exatamente o endereço registrado como beneficiador, transportador ou distribuidor.

### Eventos não carregam

1. Confira `DEPLOYMENT_BLOCK` em `frontend/contract.js`.
2. Confira a rede Sepolia.
3. Confirme que o endereço do contrato é o definitivo.
4. Verifique no Etherscan se existem transações depois do bloco configurado.

### IPFS não abre

1. Confira o CID copiado.
2. Mantenha o IPFS Desktop online.
3. Aguarde a propagação.
4. Teste o link compartilhado pelo próprio IPFS Desktop.
5. Para disponibilidade permanente, use pinning sem expor token.

### Vercel publica uma tela errada

Confira no projeto Vercel:

- Root Directory na raiz do EcoOrigem;
- Framework Preset como `Other`;
- Build Command `npm run build`;
- Output Directory `frontend`;
- presença do `vercel.json` no repositório.

## 31. Checklist final antes de entregar

### Contrato e Sepolia

- [ ] Contrato compilado com Solidity 0.8.34.
- [ ] Optimizer habilitado com 200 runs.
- [ ] EVM `paris`.
- [ ] Deploy confirmado na Sepolia.
- [ ] Endereço, hash e bloco registrados.
- [ ] Código verificado no Etherscan.
- [ ] Quatro perfis concedidos.

### Frontend

- [ ] Endereço, bloco e hash configurados.
- [ ] MetaMask conecta e mostra saldo.
- [ ] Troca para Sepolia funciona.
- [ ] Assinatura de autenticação funciona.
- [ ] Leituras por `.call()` funcionam.
- [ ] Escritas por `.send()` funcionam.
- [ ] Cadastro envia `value`.
- [ ] Estados pendente, confirmado e falhou aparecem.
- [ ] Eventos são exibidos.
- [ ] Administração aparece somente para o proprietário.
- [ ] Troca de conta e rede atualiza a interface.
- [ ] Layout funciona em celular e desktop.

### Fluxos e erros

- [ ] Lote percorreu os cinco estados.
- [ ] Custódia mudou para os atores designados.
- [ ] Documento com SHA-256 foi registrado.
- [ ] CID do IPFS foi testado, se utilizado.
- [ ] Conta sem perfil foi bloqueada.
- [ ] Estado incorreto foi bloqueado.
- [ ] Documento duplicado foi bloqueado.
- [ ] Pausa e retomada foram testadas.
- [ ] Saque das taxas foi testado.

### Publicação e documentação

- [ ] Vercel publicada por HTTPS.
- [ ] URL final testada com MetaMask.
- [ ] README sem campos `PENDENTE`.
- [ ] Dados de deploy documentados.
- [ ] 12 capturas reais adicionadas.
- [ ] Vídeo de 3 a 5 minutos acessível.
- [ ] Slides finais em PDF.
- [ ] Integrantes e papéis informados.
- [ ] Declaração de uso de IA mantida no README.

### Segurança

- [ ] Nenhuma frase de recuperação foi gravada.
- [ ] Nenhuma chave privada foi copiada.
- [ ] Nenhum token foi incluído no Git.
- [ ] Apenas contas e fundos de teste foram usados.
- [ ] Nenhum dado pessoal foi registrado na blockchain ou no IPFS.
- [ ] `make check` passou.
- [ ] `make security` passou.
- [ ] `git diff --check` passou.

## 32. Sequência resumida de comandos

Use esta sequência somente depois de ler as etapas detalhadas:

```bash
cd /home/cronos-1226/Documentos/Uea/oficina-desenvolvimento-sistemas-iii/entrega-1/EcoOrigem

npm ci
make check
make security

# Depois do deploy confirmado na Sepolia:
make abi
make configure \
  ADDRESS=0xENDERECO_REAL \
  BLOCK=NUMERO_REAL \
  TX=0xHASH_REAL

make check
make serve
```

Em outro terminal, para uma conferência final:

```bash
cd /home/cronos-1226/Documentos/Uea/oficina-desenvolvimento-sistemas-iii/entrega-1/EcoOrigem

rg 'CONTRACT_ADDRESS|DEPLOYMENT_BLOCK|DEPLOYMENT_TX' frontend/contract.js
rg -n 'PENDENTE' README.md docs frontend/contract.js
git diff --check
git status --short --branch
```

## 33. Regra de encerramento

Não considere a atividade pronta apenas porque o código funciona localmente. O guia do professor limita a nota quando o contrato não está na Sepolia e exige a URL da Vercel. A conclusão real ocorre quando contrato, frontend, documentação, evidências e apresentação usam a mesma instância implantada e todos os links foram testados.

Até esse momento, mantenha o trabalho local, preserve as alterações existentes e não publique dados incompletos.
