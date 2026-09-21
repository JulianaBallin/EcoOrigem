# Contrato inteligente EcoOrigem

Implementado em [ecoorigem/contract/eco_origem.py](../ecoorigem/contract/eco_origem.py).
O estado do contrato é uma função das transações gravadas na cadeia: reexecutar
os blocos desde o gênesis reconstrói o mesmo estado. Cada método verifica
permissões e entradas antes de alterar o estado. Uma falha equivale a um `revert`
e retorna um código estável.

## Implantação

A transação de implantação é assinada pela conta que se torna administradora. O
endereço do contrato é derivado do endereço do implantador e do nonce. Só é
possível implantar uma vez por blockchain.

| Argumento | Tipo | Descrição |
| --- | --- | --- |
| `allowed_products` | lista de textos, opcional | Produtos aceitos no cadastro. O padrão é açaí, castanha-do-brasil, murumuru, cupuaçu, andiroba, copaíba, guaraná, óleo vegetal e artesanato |

## Perfis

| Perfil | Valor no contrato |
| --- | --- |
| Produtor | `PRODUCER` |
| Beneficiador | `PROCESSOR` |
| Transportador | `CARRIER` |
| Distribuidor | `DISTRIBUTOR` |

O administrador não é um perfil: é a conta que implantou o contrato.

## Ciclo de vida

`REGISTERED` (CADASTRADO) &rarr; `PROCESSED` (BENEFICIADO) &rarr; `IN_TRANSIT`
(EM_TRANSPORTE) &rarr; `DISTRIBUTED` (DISTRIBUIDO) &rarr; `FINALIZED` (FINALIZADO).

## Métodos

| Método | Quem executa | Argumentos | Efeito |
| --- | --- | --- | --- |
| `grant_role` | Administrador | `account`, `role` | Concede o perfil |
| `revoke_role` | Administrador | `account`, `role` | Revoga o perfil |
| `register_lot` | Produtor | `product`, `origin`, `quantity_kg`, `harvest_date`, `document_hash` (opcional) | Cria o lote em CADASTRADO |
| `record_processing` | Beneficiador | `lot_id`, `description`, `document_hash` (opcional) | CADASTRADO para BENEFICIADO |
| `start_transport` | Transportador | `lot_id`, `recipient`, `destination` | BENEFICIADO para EM_TRANSPORTE. O destinatário precisa ter o perfil Distribuidor |
| `confirm_delivery` | Distribuidor designado | `lot_id`, `note` (opcional) | EM_TRANSPORTE para DISTRIBUIDO |
| `finalize_lot` | Distribuidor responsável | `lot_id`, `note` (opcional) | DISTRIBUIDO para FINALIZADO |
| `attach_document` | Responsável atual | `lot_id`, `document_hash`, `description` | Registra o hash de um documento |

## Validações de entrada

| Campo | Regra |
| --- | --- |
| `product` | Da lista aceita, ignorando caixa e acentos |
| `origin` | Entre 3 e 120 caracteres, sem caracteres de controle |
| `quantity_kg` | Número positivo, finito e de no máximo 100 000 |
| `harvest_date` | `AAAA-MM-DD`, válida, não futura e a partir de 2000-01-01 |
| `lot_id` | Formato `LOT-0001` |
| `document_hash` | 64 caracteres hexadecimais (SHA-256) |
| `recipient`, `account` | Endereço no formato `0x` seguido de 40 hexadecimais |
| Campos extras | Rejeitados |

## Códigos de erro

| Código | Camada | Significado |
| --- | --- | --- |
| `ACCESS_DENIED` | contrato | A carteira não tem o perfil ou não é a responsável |
| `INVALID_INPUT` | contrato | Campo ausente, com tipo errado ou fora dos limites |
| `INVALID_TRANSITION` | contrato | A etapa pula ou repete um passo obrigatório |
| `LOT_NOT_FOUND` | contrato | O lote não existe |
| `LOT_FINALIZED` | contrato | O lote finalizado não aceita alterações |
| `UNKNOWN_METHOD` | contrato | Método inexistente |
| `INVALID_SIGNATURE` | transação | Assinatura, hash ou remetente não conferem |
| `NONCE_MISMATCH`, `DUPLICATE_TRANSACTION` | transação | Repetição ou nonce fora de sequência |
| `TIMESTAMP_OUT_OF_RANGE` | transação | Data distante do relógio do nó |
| `CONTRACT_NOT_DEPLOYED`, `CONTRACT_ALREADY_DEPLOYED` | transação | Estado da implantação |
| `CHAIN_COMPROMISED` | nó | Integridade falhou e as escritas estão bloqueadas |

## Eventos

`CONTRACT_DEPLOYED`, `ROLE_GRANTED`, `ROLE_REVOKED`, `LOT_REGISTERED`,
`LOT_PROCESSED`, `TRANSPORT_STARTED`, `DELIVERY_CONFIRMED`, `LOT_FINALIZED` e
`DOCUMENT_ATTACHED`. Cada evento guarda o autor, a data, o hash da transação e, no
caso de lotes, os status de origem e destino.
