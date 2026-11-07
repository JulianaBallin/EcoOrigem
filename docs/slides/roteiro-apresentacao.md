# Roteiro da apresentação

Tempo: 15 minutos de apresentação e 5 minutos de arguição. Os slides mantêm o design da Entrega 1 e foram atualizados para a dApp Ethereum.

| Tempo | Slides | Conteúdo | Fala sugerida |
| --- | --- | --- | --- |
| 0:00 a 2:00 | 1 a 3 | Equipe, problema, solução e justificativa da Ethereum | Ana |
| 2:00 a 4:00 | 4 e 5 | Fluxo dos atores e arquitetura Vercel, MetaMask, Web3.js e Sepolia | Juliana |
| 4:00 a 8:00 | 6 a 8 | Máquina de estados e sete grupos obrigatórios de Solidity | Fernando |
| 8:00 a 13:00 | 9 | Demonstração ao vivo pela Vercel | Juliana opera; todos explicam sua parte |
| 13:00 a 15:00 | 10 a 12 | Testes, segurança, lições, limitações e conclusão | Ana e Fernando |
| Encerramento | 13 | Perguntas | Equipe |

## O que mostrar no contrato

Abra `contracts/EcoOrigem.sol` antes da apresentação e deixe marcados:

1. linhas 8 a 74: enums, structs, tipos, constantes, immutable, arrays e mappings;
2. linhas 76 a 152: eventos, erros e modificadores;
3. linhas 185 a 221: `registerLot` externo e pagável;
4. linhas 225 a 358: máquina de estados e custódia;
5. linhas 361 a 371: saque e interação externa;
6. linhas 394 a 414: paginação com `if`, `require` e `for` limitado;
7. linhas 437 a 541: funções `public pure`, `internal` e `private`.

Não leia o código inteiro. Para cada grupo, explique uma decisão do domínio.

## Demonstração de 5 minutos

Use o roteiro detalhado em [../demonstracao-local.md](../demonstracao-local.md):

1. conectar e autenticar;
2. mostrar perfil e saldo;
3. cadastrar lote com SepoliaETH;
4. acompanhar hash pendente e confirmação;
5. consultar lote e evento;
6. provocar erro de perfil ou estado;
7. abrir a transação no Etherscan.

## Perguntas prováveis

### Por que não usar usuário e senha?

O frontend é estático e não possui servidor confiável para guardar sessões. Uma senha no JavaScript seria contornável e não protegeria o contrato. A MetaMask prova o controle do endereço por assinatura, e o contrato aplica o perfil on-chain.

### O que é pago?

Toda escrita paga gas. Além do gas, `registerLot` envia a taxa didática fixa de `0.00001 SepoliaETH`, acumulada no contrato até o saque do proprietário.

### Qual a diferença entre `.call()` e `.send()`?

`.call()` consulta o estado localmente e não cria transação. `.send()` solicita assinatura à MetaMask, consome gas e pode alterar o estado depois da confirmação.

### Por que usar `bytes32` para documentos?

O SHA-256 tem 32 bytes. Guardar o hash é muito mais barato e evita publicar o arquivo. O CID do IPFS localiza o conteúdo externo.

### `private` deixa o dado secreto?

Não. `private` limita o acesso por outros contratos no código Solidity, mas o storage da blockchain continua público.

### O que impede pular uma etapa?

O modificador `atStatus(lotId, expected)` compara o enum atual com o esperado. Se for diferente, `InvalidStatus` reverte a operação sem alterar o estado.

### Uma carteira com o mesmo perfil pode agir no lote?

Não necessariamente. Além do perfil, o contrato compara `msg.sender` com o endereço designado pela etapa anterior e retorna `DesignatedActorOnly`.

### Como o contrato trata reentrância?

A única interação externa é o saque para a tesouraria imutável, restrito ao proprietário e executado depois das verificações. O contrato não chama endereços fornecidos por usuários durante as etapas do lote.

### A blockchain garante que o lote veio daquela origem?

Não. Ela registra quem declarou, quando declarou e preserva o histórico. Veracidade física exige auditoria, sensores, certificadores ou oráculos.

### O que acontece se o IPFS perder o arquivo?

O hash on-chain continua existindo e permite verificar uma cópia recuperada, mas a disponibilidade da URI depende de pinning. Uma evolução é usar pinning redundante.

## Checklist antes de apresentar

- [ ] URL Vercel e contrato Sepolia preenchidos no README.
- [ ] Fonte verificado no Etherscan.
- [ ] MetaMask aberta na Sepolia, nunca na Mainnet.
- [ ] Contas Produtor e conta sem perfil com saldo.
- [ ] Endereço do beneficiador copiado.
- [ ] Lote de demonstração ainda não usado ou ID conhecido.
- [ ] Etherscan do contrato aberto.
- [ ] Vídeo e capturas reais abertos como plano B.
- [ ] Cronômetro ensaiado em 15 minutos.
