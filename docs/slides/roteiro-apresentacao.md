# Roteiro da apresentação

Dez minutos no total. A divisão de falas abaixo é uma sugestão e pode ser ajustada
pela equipe. Todos os integrantes participam e devem dominar o projeto.

| Tempo | Conteúdo | Slides | Sugestão de fala |
| --- | --- | --- | --- |
| 2 min | Contexto, problema, dados e solução (problema, objetivo e justificativa do uso de blockchain) | 1 a 5 | Ana |
| 2 min | Arquitetura e funcionamento do contrato inteligente | 6 e 7 | Fernando |
| 4 min | Demonstração prática na blockchain local | 8 | Juliana, Fernando e Ana |
| 2 min | Testes, limitações e conclusão | 9 e 10 | Juliana |
| Reserva | Bônus: relatório, laboratório de integridade e execução reproduzível | 11 a 14 | Perguntas |

Os slides 11 a 14 mostram o que foi feito além do pedido e ficam para o caso de sobrar tempo
ou para responder perguntas. Os dados do slide 4 vêm do IBGE (PEVS 2023) e as fotos têm
créditos em `docs/assets/produtos/CREDITOS.md`.

## Antes de começar

1. Confirmar que a máquina tem Docker ou o ambiente virtual criado.
2. Subir a stack limpa: `make docker-reset && make docker-up && make docker-seed`.
3. Abrir <http://127.0.0.1:5000> e a apresentação em `docs/slides/apresentacao-ecoorigem.pdf`.
4. Deixar `docs/slides/video/demonstracao.webm` aberto em outra janela como plano B.

## Demonstração em quatro passos

| Passo | O que fazer | O que mostrar |
| --- | --- | --- |
| 1. Blockchain em execução | Mostrar `make docker-status` (ou o terminal do nó) e o Painel | Nó saudável, bloco atual, dificuldade e integridade da cadeia |
| 2. Operação pela interface | Carteira Produtor, aba Registrar, Registrar lote, preencher origem e quantidade, enviar | Confirmação com hash da transação, bloco minerado e tentativas de nonce |
| 3. Consulta e mudança de estado | Carteira Beneficiador, Registrar beneficiamento do lote criado, depois aba Consultar | Status passando de CADASTRADO para BENEFICIADO e a linha do tempo com bloco e autor |
| 4. Operação rejeitada | Aba Registrar, cenário "Carteira sem permissão" (ou "Pular etapas"), enviar | Mensagem ACCESS_DENIED, nenhum bloco criado e a entrada na aba Rejeições |

Extras se sobrar tempo: aba Blockchain com a prova de Merkle e aba Integridade com
"Adulterar dado gravado", que bloqueia novas operações até "Restaurar".

## Plano de contingência

| Falha | Ação |
| --- | --- |
| Docker não sobe | Usar `make start` (sem Docker) |
| Porta ocupada | `make stop` ou `make docker-down` e repetir |
| Interface fora do ar | Exibir `docs/slides/video/demonstracao.webm` |
| Estado sujo entre ensaios | `make docker-reset && make docker-up && make docker-seed` |

## Perguntas prováveis

- Por que não um banco de dados? Vários participantes, ninguém reescreve o histórico sozinho.
- A blockchain garante que a informação é verdadeira? Não. Garante que o registro não muda depois de gravado.
- Quem assina as transações? A carteira ativa, no gateway, com chave Ed25519. Em produção seria uma carteira externa.
- O que impede pular etapas? O contrato, que valida a ordem antes de alterar o estado.
- O que acontece se alguém alterar o arquivo da cadeia? A validação detecta e o nó bloqueia escritas.
