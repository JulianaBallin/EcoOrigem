# Demonstração local (4 min)

## Roteiro

| Tempo | Requisito | Ação | Mostrar |
| --- | --- | --- | --- |
| 0:00 | Inicialização | Terminal: `make demo` | Etapas 1 a 5: limpa dados, inicia o nó, implanta o contrato, concede perfis, cria LOT-0001 a LOT-0005 e verifica a cadeia |
| 0:20 | Logs contínuos | Terminal: `make logs` (deixar rodando até o fim) | A partir daqui, cada ação na interface aparece aqui como um bloco |
| 0:30 | Blockchain local em execução | Navegador: <http://127.0.0.1:5000>, aba **Painel** | Altura da cadeia, dificuldade e "Cadeia íntegra" |
| 1:00 | Operação pela interface | Carteira **Produtor**, aba **Registrar**, **Registrar lote**. Preencher origem e quantidade. **Assinar e enviar à blockchain** | Painel verde na interface. No terminal, novo `BLOCO #N CONFIRMADO` com os dados do lote |
| 2:00 | Consulta e mudança de estado | Carteira **Beneficiador**, **Registrar beneficiamento**, lote `LOT-0006`, descrição, enviar. Aba **Consultar**, `LOT-0006` | CADASTRADO para BENEFICIADO na interface e na linha `Status` do terminal |
| 2:50 | Operação inválida ou sem permissão | Aba **Registrar**, cenário **Carteira sem permissão**, enviar. Depois **Pular etapas**, enviar | No terminal, `OPERAÇÃO REJEITADA` com motivo e código. Nenhum bloco novo. Aba **Rejeições** |
| 3:40 | Fechamento | Apontar para o terminal | O último `BLOCO #N CONFIRMADO` já mostra o encadeamento com o bloco anterior |

## Extra: integridade da cadeia corrompida (opcional)

Não é um dos quatro itens pedidos pelo professor, mas mostra a imutabilidade
na prática. Cabe em uns 30 segundos, se sobrar tempo. A alteração acontece só
em memória, então pode repetir quantas vezes quiser sem afetar a cadeia real.

| Ação | Mostrar |
| --- | --- |
| Aba **Integridade**, deixar bloco e campos padrão, **Adulterar dado gravado** | Selo no topo muda para "Cadeia adulterada no bloco N". A própria aba mostra "Adulteração detectada a partir do bloco N" com o motivo (raiz de Merkle e assinatura não conferem). No terminal, `ADULTERAÇÃO DETECTADA` |
| Trocar de aba, por exemplo **Registrar** | Faixa vermelha no topo: "Integridade comprometida. Novas operações estão bloqueadas." Qualquer envio é recusado com `CHAIN_COMPROMISED` |
| Aba **Integridade**, **Restaurar da cópia em disco** | Selo volta a "Blockchain local ativa" e a aba mostra "Cadeia íntegra" de novo. No terminal, `CADEIA RESTAURADA` |

## Depois

```bash
make reset
```

Encerra o nó e a interface e apaga a cadeia e as carteiras locais (pede
confirmação). Para começar uma nova demonstração do zero, basta `make demo`
de novo.

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
| Raiz de Merkle | Hash que resume todas as transações do bloco e entra no hash dele. Com uma transação só, é o próprio hash dela. | `ebaf7617d48f...cae6e8` |
| Prova de trabalho | Esforço para achar o nonce: tentativas, tempo e zeros exigidos. | `90.901 tentativas em 0,52 s, hash começa com 4 zeros` |
| Encadeamento (`isBlockChainValid`) | Confirma se o hash anterior bate com o bloco de trás. | `hash anterior confere com o hash do bloco #21` |
