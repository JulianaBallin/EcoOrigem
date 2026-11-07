# Roteiro de testes da dApp

Execute os cenários primeiro em ambiente local e depois pela URL final da Vercel. Use somente a Ethereum Sepolia e carteiras de teste.

## Preparação

1. Confirme que o contrato foi implantado e configurado conforme [deploy-sepolia.md](deploy-sepolia.md).
2. Deixe cinco contas MetaMask prontas: Proprietário, Produtor, Beneficiador, Transportador e Distribuidor.
3. Garanta SepoliaETH em todas as contas que enviarão transações.
4. Abra a dApp publicada por HTTPS ou execute `make serve`.
5. Abra o Sepolia Etherscan em outra aba.
6. Não coloque dados pessoais ou documentos reais.

## Verificações automatizadas

```bash
npm ci
make check
make security
```

Resultado esperado: compilação 0.8.34, frontend validado e duas suítes aprovadas. A publicação não possui dependências npm; a Web3.js 4.0.3 da CDN está fixada com SRI. Ganache, solc e os pacotes de teste são somente de desenvolvimento; `make security` falha se aparecer qualquer achado fora dessas ferramentas locais isoladas.

## Fluxo principal

| ID | Conta | Ação | Resultado esperado |
| --- | --- | --- | --- |
| V01 | Proprietário | Conectar e assinar o desafio | Endereço, saldo e perfil Administrador aparecem; sem gas |
| V02 | Proprietário | Conceder os quatro perfis | Quatro transações confirmadas e eventos `RoleUpdated` |
| V03 | Produtor | Conectar, autenticar e abrir Cadastrar lote | Perfil Produtor e taxa carregados |
| V04 | Produtor | Cadastrar açaí, origem, 250 kg, data passada e beneficiador | MetaMask mostra `value`; hash pendente e confirmação `LotRegistered` |
| V05 | Consulta | Abrir Lotes e detalhes do lote #1 | Estado Cadastrado, produtor, beneficiador e histórico público |
| V06 | Produtor | Anexar um arquivo de teste e CID opcional | SHA-256 calculado no navegador e evento `DocumentAttached` |
| V07 | Beneficiador | Registrar processamento e designar transportador | Estado Beneficiado e custodiante atualizado |
| V08 | Transportador | Iniciar transporte a 24 °C e designar distribuidor | Estado Em transporte, temperatura 24.000 e evento |
| V09 | Distribuidor | Confirmar recebimento | Estado Distribuído e custódia do distribuidor |
| V10 | Distribuidor | Finalizar | Estado Finalizado e histórico com cinco entradas |
| V11 | Qualquer conta | Abrir Eventos | Eventos recentes e links válidos para o Etherscan |

## Exceções obrigatórias para a demonstração

| ID | Conta | Ação | Mensagem esperada | Estado muda? |
| --- | --- | --- | --- |
| E01 | Conta sem perfil | Tentar cadastrar | Carteira sem perfil Produtor | Não |
| E02 | Produtor | Cadastrar sem saldo suficiente | Saldo de SepoliaETH insuficiente | Não |
| E03 | Produtor | Cancelar na MetaMask | Solicitação cancelada | Não |
| E04 | Beneficiador diferente | Processar lote #1 | Etapa pertence à carteira designada | Não |
| E05 | Transportador | Tentar transportar lote ainda Cadastrado | Estado atual e estado esperado | Não |
| E06 | Transportador | Informar 70 °C | Campo de temperatura inválido | Não |
| E07 | Custodiante | Anexar novamente o mesmo arquivo | Documento já registrado | Não |
| E08 | Distribuidor diferente | Confirmar entrega | Carteira designada exibida | Não |
| E09 | Distribuidor | Alterar lote Finalizado | Estado incompatível | Não |
| E10 | Proprietário | Pausar e tentar nova escrita | Contrato pausado | Não |
| E11 | Não proprietário | Tentar conceder perfil | Carteira não autorizada | Não |

Depois de cada exceção, consulte o lote e confirme que o estado não mudou. Uma transação revertida já enviada pode consumir gas.

## Administração

| ID | Ação | Resultado esperado |
| --- | --- |
| A01 | Acessar Administração com conta comum | Aba não aparece; chamada direta ainda seria recusada pelo contrato |
| A02 | Pausar com proprietário | `paused = true`, evento `PauseChanged`, consultas continuam |
| A03 | Retomar com proprietário | Escritas voltam a ser aceitas |
| A04 | Sacar taxas | Saldo do contrato vai a zero e `FeesWithdrawn` aponta para a tesouraria |
| A05 | Sacar novamente sem saldo | Mensagem “sem taxas acumuladas” |
| A06 | Revogar perfil | `hasRole` retorna `false` e evento é exibido |

## Troca de conta e rede

1. Com a dApp aberta, troque a conta na MetaMask.
2. Confirme que a autenticação anterior é invalidada e o novo perfil é carregado.
3. Troque para outra rede.
4. Confirme o aviso e clique no indicador de rede.
5. Autorize `wallet_switchEthereumChain`.
6. Confirme que os dados da Sepolia voltam a aparecer.

## Responsividade e acessibilidade

- Conferir 390 px, 768 px e desktop sem rolagem horizontal.
- Navegar por teclado e verificar foco visível.
- Confirmar rótulos em todos os campos.
- Confirmar contraste e mensagens que não dependem somente de cor.
- Ativar redução de movimento do sistema e conferir que animações são minimizadas.

## Registro das evidências

Após o deploy definitivo, salve as capturas previstas em [prints/README.md](prints/README.md). Não reutilize prints do protótipo Python da Entrega 1.
