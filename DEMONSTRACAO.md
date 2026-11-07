# Demonstração da dApp em 5 minutos

A apresentação oficial deve usar a URL publicada na Vercel e o contrato já implantado na Sepolia. Este roteiro também funciona em `http://127.0.0.1:8000` para ensaio, desde que o frontend esteja configurado com o mesmo contrato.

## Preparação

1. Deixar a MetaMask na Sepolia com as contas Produtor e uma conta sem perfil prontas.
2. Garantir SepoliaETH suficiente para a taxa de cadastro e o gas.
3. Abrir a dApp, o Etherscan do contrato e a apresentação.
4. Limpar notificações antigas da MetaMask.
5. Escolher uma data passada e copiar o endereço do beneficiador.
6. Ter o vídeo de contingência já aberto.

## Sequência ao vivo

| Tempo | Ação | O que explicar |
| --- | --- | --- |
| 0:00 | Abrir a URL Vercel | É HTML/CSS/JavaScript puro, servido por HTTPS, conectado à Sepolia |
| 0:20 | Clicar em **Conectar e autenticar** | A conexão expõe o endereço; a assinatura do desafio prova controle sem gas e sem senha armazenada |
| 0:55 | Mostrar endereço, saldo e perfil | O perfil vem de `hasRole`; a autorização real permanece no contrato |
| 1:20 | Abrir **Cadastrar lote** e preencher | Produto, origem, quantidade, data e beneficiador designado |
| 2:00 | Enviar e abrir a MetaMask | Mostrar a rede, o contrato, a taxa `value` e o gas antes de confirmar |
| 2:30 | Acompanhar pendente e confirmada | O frontend mostra o hash e o bloco; abrir a transação no Etherscan |
| 3:10 | Abrir **Lotes** e o lote criado | Estado Cadastrado, custódia, beneficiador e histórico retornam por `.call()` |
| 3:40 | Abrir **Eventos** | `LotRegistered` tem parâmetros indexados e aponta para a mesma transação |
| 4:05 | Trocar para conta sem perfil e repetir cadastro | O frontend traduz `Unauthorized` e o estado não muda |
| 4:45 | Fechar | Contrato decide, MetaMask assina, Sepolia confirma e Etherscan permite auditoria |

## Exceção alternativa

Se não quiser depender de outra conta, use um lote em estado Cadastrado e tente confirmar o recebimento. O contrato deve retornar `InvalidStatus`, informando o estado atual e o esperado.

## Plano de contingência

| Falha | Ação |
| --- | --- |
| Faucet lento | Não faça deploy nem dependa de saldo novo durante a apresentação; prepare as contas antes |
| Sepolia congestionada | Mostre o estado pendente, abra o hash no Etherscan e avance para uma consulta |
| MetaMask na rede errada | Clique no indicador de rede e autorize a troca para Sepolia |
| Transação cancelada | Explique o tratamento de erro e repita somente uma vez |
| Vercel fora do ar | Execute `make serve` e use o mesmo contrato; informe que o plano principal é a URL HTTPS |
| Rede indisponível | Use o vídeo de 3 a 5 minutos e as capturas reais de `docs/assets/evidencias/` |

## Não fazer durante a apresentação

- Não implantar um novo contrato.
- Não obter saldo no faucet.
- Não revelar frase de recuperação ou chave privada.
- Não gravar dados pessoais ou documentos reais.
- Não deixar a MetaMask em Ethereum Mainnet.
- Não prometer que a blockchain confirma a veracidade da informação de origem.
