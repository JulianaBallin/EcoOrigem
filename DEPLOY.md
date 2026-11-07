# Implantação na Sepolia e publicação na Vercel

Este guia usa as ferramentas definidas pelo professor. O deploy precisa ser confirmado pela MetaMask de uma integrante da equipe. Nunca cole chave privada ou frase de recuperação no Remix, no terminal ou no repositório.

## 1. Preparar as contas

Prepare ao menos cinco contas de teste na MetaMask, preferencialmente sem fundos reais:

| Conta | Uso |
| --- | --- |
| Proprietário | Implanta o contrato, concede perfis, pausa e saca taxas |
| Produtor | Cadastra o lote e paga a taxa de `0.00001 ether` |
| Beneficiador | Registra processamento e designa transportador |
| Transportador | Registra transporte e designa distribuidor |
| Distribuidor | Confirma o recebimento e finaliza |

1. Instale ou atualize a [MetaMask](https://metamask.com/pt-BR).
2. Ative a rede **Ethereum Sepolia**, chain ID `11155111` (`0xaa36a7`).
3. Obtenha somente ETH de teste no [Sepolia PoW Faucet](https://sepolia-faucet.pk910.de/#).
4. Coloque saldo na conta proprietária e na conta produtora. As demais contas também precisam de gas para suas etapas.
5. Nunca use uma carteira com fundos reais nesta demonstração.

## 2. Preparar o workspace do Remix

```bash
npm ci
make remix
```

O comando atualiza `remix/contracts/EcoOrigem.sol` com uma cópia idêntica do contrato principal. A pasta `remix/` contém o contrato, o teste Solidity e as configurações necessárias para importação direta.

## 3. Importar e compilar no Remix

1. Abra o [Remix configurado para Solidity 0.8.34](https://app.remix.live/#lang=en&optimize&runs=200&evmVersion=paris&version=soljson-v0.8.34+commit.80d5c536.js).
2. Importe o conteúdo completo da pasta `remix/` para um workspace chamado `EcoOrigem`. Nesse modo, abra `contracts/EcoOrigem.sol`. Como alternativa, ative o plugin **Git**, clone o repositório na branch `develop` e abra `remix/contracts/EcoOrigem.sol`.
3. Em **Solidity Compiler**, confirme a versão `0.8.34`.
4. Confirme **Enable optimization**, `200` runs e EVM `paris`. O arquivo `compiler_config.json` mantém esses parâmetros reproduzíveis.
5. Compile o arquivo `EcoOrigem.sol` que está aberto.
6. Não continue se houver erro ou aviso não compreendido.

As configurações precisam coincidir com `scripts/compile-contract.mjs`; isso permite reproduzir o bytecode e verificar o fonte no Etherscan.

Antes do deploy público, execute também:

```bash
make check
make security
```

Resultado esperado:

- compilador `0.8.34+commit.80d5c536`;
- optimizer habilitado, `runs = 200`;
- EVM `paris`;
- bytecode implantado abaixo de 24.576 bytes;
- duas suítes locais aprovadas;
- verificação de credenciais aprovada.

## 4. Implantar pela MetaMask

1. Na MetaMask, selecione a conta **Proprietário** e a rede Sepolia.
2. No Remix, abra **Deploy & Run Transactions**.
3. Em **Environment**, escolha **Browser Extension** ou **Injected Provider - MetaMask**, conforme o nome exibido.
4. Confirme `Custom (11155111) network` ou `Sepolia (11155111)`.
5. Em **Contract**, selecione `EcoOrigem`.
6. Mantenha **Value = 0**. O construtor não recebe argumentos.
7. Clique em **Deploy**, revise a rede e confirme na MetaMask.
8. Aguarde a confirmação e não faça um segundo deploy enquanto a primeira transação estiver pendente.

Registre os dados imediatamente:

| Dado | Valor |
| --- | --- |
| Endereço do contrato | `PENDENTE` |
| Hash da transação | `PENDENTE` |
| Bloco | `PENDENTE` |
| Carteira proprietária | `PENDENTE` |
| Link do Etherscan | `PENDENTE` |
| Data e hora | `PENDENTE` |

No [Sepolia Etherscan](https://sepolia.etherscan.io), pesquise o hash da transação, abra a criação do contrato e confira se a rede, o remetente e o status estão corretos.

## 5. Verificar o código no Etherscan

1. Na página do contrato, abra **Contract > Verify and Publish**.
2. Selecione **Solidity (Single file)**.
3. Escolha a versão exata `v0.8.34+commit.80d5c536`.
4. Marque optimizer **Yes** e `200` runs.
5. Em EVM version, escolha `paris`.
6. Cole o conteúdo de `backend/contracts/EcoOrigem.sol`.
7. Não informe argumentos do construtor.
8. Conclua e confira as abas **Code**, **Read Contract** e **Write Contract**.

Se o bytecode não coincidir, verifique primeiro versão, optimizer, runs e EVM. Não altere o código apenas no Remix; toda correção deve voltar ao repositório, ser testada e gerar um novo deploy documentado.

## 6. Conceder os perfis

O enum `Role` usa os valores abaixo:

| Perfil | Valor |
| --- | --- |
| `Producer` | `1` |
| `Processor` | `2` |
| `Carrier` | `3` |
| `Distributor` | `4` |

No contrato implantado do Remix, execute `grantRole(account, role)` quatro vezes com a conta proprietária:

1. carteira Produtor, valor `1`;
2. carteira Beneficiador, valor `2`;
3. carteira Transportador, valor `3`;
4. carteira Distribuidor, valor `4`.

Depois de cada confirmação, consulte `hasRole(account, role)`. O retorno deve ser `true`. Registre os endereços sem registrar chaves privadas.

## 7. Configurar o frontend

Copie o endereço, o bloco e o hash do deploy e execute:

```bash
make abi
make configure \
  ADDRESS=0xENDERECO_DO_CONTRATO \
  BLOCK=NUMERO_DO_BLOCO \
  TX=0xHASH_DA_TRANSACAO
make check
```

O comando atualiza somente as constantes de implantação em `frontend/contract.js`. Confirme:

```bash
rg 'CONTRACT_ADDRESS|DEPLOYMENT_BLOCK|DEPLOYMENT_TX' frontend/contract.js
```

Inicie o frontend:

```bash
make serve
```

Abra <http://127.0.0.1:8000> no navegador com MetaMask e execute o [roteiro de testes](TESTES.md).

## 8. Documentos e IPFS

O frontend calcula o SHA-256 localmente. Para também registrar uma URI IPFS:

1. envie o arquivo por um cliente IPFS ou provedor de pinning escolhido pela equipe;
2. copie somente o CID retornado;
3. no EcoOrigem, informe o arquivo local, a descrição e o CID;
4. confira na MetaMask que o arquivo não faz parte dos dados da transação;
5. após a confirmação, abra a URI pela lista de documentos.

Não coloque token de provedor IPFS no código. O pinning é externo à dApp estática.

## 9. Publicar na Vercel

1. Envie a versão validada para a branch `develop` e faça a integração definida pela equipe.
2. Entre na Vercel com a conta autorizada pela equipe.
3. Importe `JulianaBallin/EcoOrigem` do GitHub.
4. Escolha **Other** como framework.
5. Mantenha a raiz do repositório. O `vercel.json` já define:
   - build command: `npm run build`;
   - output directory: `frontend`;
   - clean URLs.
6. Não cadastre variáveis secretas; esta dApp não usa backend nem credenciais.
7. Faça o deploy e abra a URL HTTPS em um navegador com MetaMask.
8. Teste conexão, troca de rede, leitura, transação pagável, erro tratado, evento e Etherscan.

Registre a URL final no README e nesta tabela:

| Ambiente | URL | Commit |
| --- | --- | --- |
| Produção Vercel | `PENDENTE` | `PENDENTE` |
| Contrato Etherscan | `PENDENTE` | `PENDENTE` |

## 10. Capturas e vídeo

Produza as evidências em `docs/assets/evidencias/` somente depois de configurar o endereço final. Grave um vídeo de 3 a 5 minutos pela URL da Vercel mostrando:

1. conexão e autenticação da carteira;
2. leitura dos totais;
3. cadastro com SepoliaETH;
4. hash pendente e confirmação;
5. erro por carteira ou etapa incorreta;
6. evento e transação no Etherscan.

Publique o vídeo em local acessível ao professor e atualize o link no README.

## Checklist final

- [ ] Contrato implantado na Sepolia.
- [ ] Fonte verificado no Etherscan.
- [ ] Quatro perfis concedidos e conferidos.
- [ ] `frontend/contract.js` contém endereço, bloco e hash reais.
- [ ] `make check` aprovado depois da configuração.
- [ ] Fluxo principal reproduzido por duas contas da MetaMask.
- [ ] Vercel publicada por HTTPS.
- [ ] Capturas reais adicionadas em `docs/assets/evidencias/`.
- [ ] Vídeo de 3 a 5 minutos publicado e vinculado.
- [ ] README sem campos `PENDENTE`.
- [ ] Nenhuma chave, senha, token ou frase de recuperação no Git.
