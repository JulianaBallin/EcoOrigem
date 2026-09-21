# Cenários de teste: operações realizadas, resultados esperados e obtidos

Execução automatizada em 21/09/2026 12:26 contra uma blockchain local nova (dificuldade 4). Cada linha é uma operação real, assinada e enviada ao nó.

**Resultado: 48 de 48 cenários conforme o esperado.**

Reprodução: `make scenarios`.

## Operação válida

| ID | Operação realizada | Resultado esperado | Resultado obtido | Status |
| --- | --- | --- | --- | --- |
| V01 | Implantar o contrato com a carteira Administrador | confirmada em um novo bloco | confirmada no bloco 1 | Aprovado |
| V02 | Administrador concede o perfil PRODUCER a produtor | confirmada em um novo bloco | confirmada no bloco 2 | Aprovado |
| V03 | Administrador concede o perfil PROCESSOR a beneficiador | confirmada em um novo bloco | confirmada no bloco 3 | Aprovado |
| V04 | Administrador concede o perfil CARRIER a transportador | confirmada em um novo bloco | confirmada no bloco 4 | Aprovado |
| V05 | Administrador concede o perfil DISTRIBUTOR a distribuidor | confirmada em um novo bloco | confirmada no bloco 5 | Aprovado |
| V06 | Administrador concede o perfil DISTRIBUTOR a distribuidor2 | confirmada em um novo bloco | confirmada no bloco 6 | Aprovado |
| V07 | Produtor registra o lote LOT-0001 com hash do documento de origem | confirmada em um novo bloco | confirmada no bloco 7 | Aprovado |
| V08 | Beneficiador registra o beneficiamento de LOT-0001 | confirmada em um novo bloco | confirmada no bloco 8 | Aprovado |
| V09 | Transportador inicia o transporte designando o distribuidor | confirmada em um novo bloco | confirmada no bloco 9 | Aprovado |
| V10 | Distribuidor designado confirma o recebimento | confirmada em um novo bloco | confirmada no bloco 10 | Aprovado |
| V11 | Distribuidor finaliza o lote | confirmada em um novo bloco | confirmada no bloco 11 | Aprovado |
| V12 | Consultar LOT-0001: status e histórico completo | FINALIZED com 5 eventos | FINALIZED com 5 eventos | Aprovado |
| V13 | Responsável anexa documento ao lote LOT-0002 | confirmada em um novo bloco | confirmada no bloco 13 | Aprovado |
| V14 | Verificar documento com hash correto | registrado | registrado | Aprovado |
| V15 | Validar a cadeia inteira | íntegra | íntegra | Aprovado |
| V16 | Reiniciar o nó e reconstruir o estado do disco | 2 lotes, cadeia íntegra | 2 lotes, cadeia íntegra | Aprovado |

## Entrada inválida ou sem permissão

| ID | Operação realizada | Resultado esperado | Resultado obtido | Status |
| --- | --- | --- | --- | --- |
| I01 | Carteira sem perfil tenta registrar lote | rejeitada (ACCESS_DENIED) | rejeitada (ACCESS_DENIED) | Aprovado |
| I02 | Quantidade negativa | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I03 | Quantidade zero | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I04 | Data de coleta no futuro | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I05 | Produto fora da lista aceita | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I06 | Origem vazia | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I07 | Campo desconhecido no cadastro | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I08 | Finalizar lote CADASTRADO (pular etapas) | rejeitada (INVALID_TRANSITION) | rejeitada (INVALID_TRANSITION) | Aprovado |
| I09 | Repetir o beneficiamento de lote já beneficiado | rejeitada (INVALID_TRANSITION) | rejeitada (INVALID_TRANSITION) | Aprovado |
| I10 | Beneficiar lote inexistente | rejeitada (LOT_NOT_FOUND) | rejeitada (LOT_NOT_FOUND) | Aprovado |
| I11 | Identificador de lote em formato inválido | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I12 | Alterar lote FINALIZADO (reprocessar) | rejeitada (LOT_FINALIZED) | rejeitada (LOT_FINALIZED) | Aprovado |
| I13 | Anexar documento a lote FINALIZADO | rejeitada (LOT_FINALIZED) | rejeitada (LOT_FINALIZED) | Aprovado |
| I14 | Produtor tenta conceder perfil (não é administrador) | rejeitada (ACCESS_DENIED) | rejeitada (ACCESS_DENIED) | Aprovado |
| I15 | Conceder perfil já existente | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I16 | Destinatário do transporte sem perfil Distribuidor | rejeitada (INVALID_INPUT) | rejeitada (INVALID_INPUT) | Aprovado |
| I17 | Método inexistente no contrato | rejeitada (UNKNOWN_METHOD) | rejeitada (UNKNOWN_METHOD) | Aprovado |
| I18 | Anexar documento sem ser o responsável atual | rejeitada (ACCESS_DENIED) | rejeitada (ACCESS_DENIED) | Aprovado |
| I19 | Nenhum bloco foi criado pelas 18 operações rejeitadas | 0 blocos novos | 0 blocos novos | Aprovado |
| I20 | Outro distribuidor tenta confirmar o recebimento | rejeitada (ACCESS_DENIED) | rejeitada (ACCESS_DENIED) | Aprovado |
| I21 | Transação com remetente falsificado | rejeitada (INVALID_SIGNATURE) | rejeitada (INVALID_SIGNATURE) | Aprovado |
| I22 | Transação alterada depois de assinada | rejeitada (INVALID_SIGNATURE) | rejeitada (INVALID_SIGNATURE) | Aprovado |
| I23 | Reenvio da mesma transação (replay) | rejeitada (DUPLICATE_TRANSACTION) | rejeitada (DUPLICATE_TRANSACTION) | Aprovado |
| I24 | Nonce fora de sequência | rejeitada (NONCE_MISMATCH) | rejeitada (NONCE_MISMATCH) | Aprovado |
| I25 | Transação com data muito antiga | rejeitada (TIMESTAMP_OUT_OF_RANGE) | rejeitada (TIMESTAMP_OUT_OF_RANGE) | Aprovado |
| I26 | Reimplantar o contrato | rejeitada (CONTRACT_ALREADY_DEPLOYED) | rejeitada (CONTRACT_ALREADY_DEPLOYED) | Aprovado |
| I27 | Verificar arquivo alterado (hash diferente) | não registrado | não registrado | Aprovado |

## Integridade

| ID | Operação realizada | Resultado esperado | Resultado obtido | Status |
| --- | --- | --- | --- | --- |
| A01 | Alterar dado gravado no bloco 18 (sem refazer hashes) | inválida a partir do bloco 18 | inválida a partir do bloco 18 | Aprovado |
| A02 | Nova operação com a cadeia comprometida | rejeitada (CHAIN_COMPROMISED) | rejeitada (CHAIN_COMPROMISED) | Aprovado |
| A03 | Alterar o bloco 17 e refazer a prova de trabalho dele | encadeamento quebrado (BROKEN_LINK) | encadeamento quebrado (BROKEN_LINK) | Aprovado |
| A04 | Restaurar a cadeia a partir do disco | íntegra | íntegra | Aprovado |
| A05 | Operação volta a ser aceita após a restauração | confirmada em um novo bloco | confirmada no bloco 19 | Aprovado |
