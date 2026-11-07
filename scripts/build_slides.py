"""Update the Delivery 1 deck while preserving its Canva visual identity."""

# pylint: disable=line-too-long,protected-access

from __future__ import annotations

import copy
import shutil
import subprocess
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "docs" / "slides"
TEMPLATE = SLIDES / "template-entrega-1.pptx"
OUTPUT = SLIDES / "apresentacao-ecoorigem.pptx"
PDF = SLIDES / "apresentacao-ecoorigem.pdf"
UEA_LOGO = ROOT / "docs" / "assets" / "uea.png"


def duplicate_slide(prs: Presentation, source_index: int, insert_index: int) -> None:
    """Duplicate a shapes-only slide and insert it at the requested position."""
    source = prs.slides[source_index]
    target = prs.slides.add_slide(prs.slide_layouts[6])
    for shape in source.shapes:
        element = copy.deepcopy(shape.element)
        target.shapes._spTree.insert_element_before(
            element, "p:extLst"
        )  # pylint: disable=protected-access

    slide_ids = prs.slides._sldIdLst  # pylint: disable=protected-access
    new_id = slide_ids[-1]
    slide_ids.remove(new_id)
    slide_ids.insert(insert_index, new_id)


def text_shapes(shapes):
    """Yield text shapes recursively, including shapes inside groups."""
    for shape in shapes:
        if getattr(shape, "has_text_frame", False):
            yield shape
        if hasattr(shape, "shapes"):
            yield from text_shapes(shape.shapes)


def shape_with_text(slide, current: str):
    """Find the first shape whose complete text matches the supplied value."""
    for shape in text_shapes(slide.shapes):
        if shape.text.strip() == current:
            return shape
    raise ValueError(f"Texto não encontrado no modelo: {current!r}")


def replace(slide, current: str, new: str, size: float | None = None) -> None:
    """Replace text while retaining the first run's visual formatting."""
    shape = shape_with_text(slide, current)
    runs = [run for paragraph in shape.text_frame.paragraphs for run in paragraph.runs]
    style = None
    if runs:
        font = runs[0].font
        style = {
            "name": font.name,
            "size": font.size,
            "bold": font.bold,
            "italic": font.italic,
        }
    shape.text = new
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            if style:
                run.font.name = style["name"]
                run.font.size = style["size"]
                run.font.bold = style["bold"]
                run.font.italic = style["italic"]
            if size is not None:
                run.font.size = Pt(size)


def set_notes(slide, text: str) -> None:
    """Replace speaker notes with the Delivery 2 guidance."""
    frame = slide.notes_slide.notes_text_frame
    frame.text = text


def update_deck(prs: Presentation) -> None:  # pylint: disable=too-many-statements
    """Replace the content and add two contract-resource slides."""
    duplicate_slide(prs, 5, 6)
    duplicate_slide(prs, 5, 7)

    # 1. Capa
    slide = prs.slides[0]
    replace(
        slide,
        "RASTREABILIDADE DE PRODUTOS DA BIOECONOMIA AMAZÔNICA COM BLOCKCHAIN",
        "DAPP DE RASTREABILIDADE DA BIOECONOMIA AMAZÔNICA NA ETHEREUM SEPOLIA",
        20,
    )
    set_notes(slide, "Apresentar a equipe, o tema e o objetivo da segunda entrega.")

    # 2. Problema
    slide = prs.slides[1]
    replace(
        slide,
        "O consumidor não tem como saber qual versão é a verdadeira, e quem administra o sistema pode alterar o histórico. Só o açaí extrativo movimentou R$ 853,1 milhões em 2023 (IBGE, PEVS 2023).",
        "O consumidor não tem como saber qual versão é a verdadeira, e uma base controlada por uma organização pode ser alterada. A rastreabilidade precisa ser compartilhada, verificável e independente de um único guardião.",
        20,
    )
    set_notes(
        slide,
        "Explicar o problema em cerca de um minuto e evitar prometer que a blockchain garante a verdade do dado de origem.",
    )

    # 3. Solução e justificativa
    slide = prs.slides[2]
    replace(slide, "Solução + por que Blockchain?", "Solução + por que Ethereum?")
    replace(
        slide,
        "O EcoOrigem registra cada etapa do lote em uma blockchain local. Faz sentido usar blockchain porque vários participantes que não confiam totalmente uns nos outros precisam compartilhar o mesmo histórico.",
        "O EcoOrigem registra cada etapa em um contrato inteligente na Sepolia. Participantes independentes compartilham o mesmo histórico público sem entregar o controle a uma única organização.",
        18,
    )
    replace(slide, "ENCADEADA", "PÚBLICA")
    replace(
        slide,
        "Cada operação leva a assinatura digital da carteira de quem executou.",
        "A MetaMask assina cada transação com a carteira de quem executou.",
        17,
    )
    replace(
        slide,
        "Cada bloco guarda o hash do anterior. Alterar um bloco invalida todos os seguintes.",
        "Transações, eventos e estado podem ser conferidos no Sepolia Etherscan.",
        17,
    )
    replace(
        slide,
        "O contrato inteligente confere o perfil e a ordem das etapas antes de gravar.",
        "O Solidity confere perfil, custódia e ordem das etapas antes de gravar.",
        17,
    )
    set_notes(
        slide,
        "Relacionar assinatura, transparência pública e validação do contrato com o problema apresentado.",
    )

    # 4. Fluxo
    slide = prs.slides[3]
    replace(
        slide,
        "Cada participante tem uma carteira com um perfil, e cada etapa define quem executa a próxima.",
        "Cada participante entra com a MetaMask. O endereço conectado determina o perfil e a etapa permitida.",
        17,
    )
    replace(
        slide,
        "O produtor cadastra o lote com produto, origem, quantidade e data da coleta, e escolhe o beneficiador.",
        "O produtor paga a taxa de teste, cadastra origem e quantidade e designa o beneficiador.",
        15,
    )
    replace(
        slide,
        "O beneficiador designado registra o processamento e escolhe o transportador.",
        "O beneficiador registra o processamento, o laudo e designa o transportador.",
        15,
    )
    replace(
        slide,
        "O transportador designado inicia o transporte e indica o distribuidor que vai receber.",
        "O transportador registra destino e temperatura e indica o distribuidor.",
        15,
    )
    replace(
        slide,
        "O distribuidor designado confirma o recebimento e finaliza o lote. Qualquer pessoa consulta o histórico sem precisar de carteira.",
        "O distribuidor confirma e finaliza. Qualquer pessoa consulta lotes, eventos, hashes e referências IPFS.",
        15,
    )
    set_notes(
        slide,
        "Percorrer a máquina de estados e destacar que a etapa anterior escolhe a próxima carteira.",
    )

    # 5. Arquitetura
    slide = prs.slides[4]
    replace(
        slide,
        "Tudo roda na máquina local, em Python, seguindo o modelo de DApp da Aula 01: interface, contrato e blockchain.",
        "A interface estática na Vercel usa Web3.js, a MetaMask assina e o contrato Solidity persiste o estado na Sepolia.",
        16,
    )
    replace(
        slide,
        "Interface e gateway: o usuário opera pela tela web, e o gateway assina a transação com a carteira ativa.",
        "Frontend na Vercel: HTML, CSS e JavaScript puros consultam a ABI e exibem lotes, perfis, transações e eventos.",
        14,
    )
    replace(
        slide,
        "Nó da blockchain: confere a assinatura, o nonce e a data, executa o contrato, minera o bloco com prova de trabalho e grava a cadeia.",
        "MetaMask + Web3.js: conectam a conta, conferem a rede, assinam desafios e enviam transações para a Sepolia.",
        14,
    )
    replace(
        slide,
        "Cadeia de blocos: cada bloco tem hash SHA-256, hash do bloco anterior, raiz de Merkle e nonce, como na implementação da Aula 02.",
        "Contrato + Sepolia: o Solidity aplica acesso e estados; a Ethereum confirma, replica e publica eventos no Etherscan.",
        14,
    )
    replace(
        slide, "Máquina local, em Python", "Vercel + MetaMask + Ethereum Sepolia", 13
    )
    set_notes(
        slide,
        "Explicar o caminho de uma escrita: formulário, Web3.js, MetaMask, Sepolia e evento retornando à tela.",
    )

    # 6. Regras do contrato
    slide = prs.slides[5]
    replace(slide, "Regras do contrato inteligente", "Contrato inteligente em Solidity")
    replacements = {
        "register_lot\nProdutor": "registerLot\nProdutor",
        "record_processing\nBeneficiador designado": "recordProcessing\nBeneficiador designado",
        "start_transport\nTransportador designado": "startTransport\nTransportador designado",
        "confirm_delivery\nDistribuidor designado": "confirmDelivery\nDistribuidor designado",
        "finalize_lot\nDistribuidor responsável": "finalizeLot\nDistribuidor responsável",
        "Cada etapa exige um perfil, e só a carteira designada pela etapa anterior pode executá-la. Qualquer outra recebe ACCESS_DENIED.": "Perfis ficam ligados ao endereço. Só o ator designado executa a etapa; os demais recebem erro personalizado.",
        "Cadastrado, beneficiado, em transporte, distribuído e finalizado. Pular ou repetir etapa gera INVALID_TRANSITION, e o lote finalizado não muda mais.": "Cinco estados em enum. Modificadores rejeitam lote inexistente, etapa fora de ordem e contrato pausado.",
        "Origem, quantidade, etapas, responsáveis, datas e o hash dos documentos. Arquivos e dados pessoais ficam fora.": "Estado, responsáveis, SHA-256 e URI IPFS ficam on-chain. Arquivos e credenciais ficam fora.",
        "Tudo é validado antes da mineração: uma operação inválida nunca vira bloco.": "Uma operação revertida não altera o estado, embora a tentativa possa consumir gas.",
        "Pular ou repetir etapa gera INVALID_TRANSITION": "Estado incorreto gera InvalidStatus",
        "Estado final: nenhuma alteração é aceita": "Finalizado: nenhuma nova alteração",
    }
    for current, new in replacements.items():
        replace(slide, current, new, 11 if "\n" in current else None)
    set_notes(
        slide,
        "Mostrar registerLot, os modificadores de perfil e estado e os erros InvalidStatus e DesignatedActorOnly.",
    )

    # 7. Recursos de Solidity I
    slide = prs.slides[6]
    replace(
        slide, "Regras do contrato inteligente", "Recursos Solidity I · base e coleções"
    )
    resource_one = {
        "register_lot\nProdutor": "uint256 · int256\nbool · address",
        "CADASTRADO": "TIPOS DE DADOS",
        "record_processing\nBeneficiador designado": "public · external\ninternal · private",
        "BENEFICIADO": "FUNÇÕES",
        "start_transport\nTransportador designado": "if/else · for\nrequire",
        "EM TRANSPORTE": "CONTROLE",
        "confirm_delivery\nDistribuidor designado": "arrays · mapping\nnested mapping",
        "DISTRIBUÍDO": "COLEÇÕES",
        "finalize_lot\nDistribuidor responsável": "view · pure\npayable",
        "FINALIZADO": "LEITURA + ETH",
        "Cada etapa exige um perfil, e só a carteira designada pela etapa anterior pode executá-la. Qualquer outra recebe ACCESS_DENIED.": "Tipos funcionais: taxa, dono imutável, temperatura com sinal, hashes e endereços.",
        "Cadastrado, beneficiado, em transporte, distribuído e finalizado. Pular ou repetir etapa gera INVALID_TRANSITION, e o lote finalizado não muda mais.": "Visibilidades com sentido, consultas sem gas e cadastro payable com taxa exata.",
        "Origem, quantidade, etapas, responsáveis, datas e o hash dos documentos. Arquivos e dados pessoais ficam fora.": "Paginação limita o for; mappings ligam IDs, perfis, documentos e contadores.",
        "QUEM PODE": "TIPOS DE DADOS",
        "EM QUE ORDEM": "FUNÇÕES",
        "O QUE FICA NA CADEIA": "CONTROLE + COLEÇÕES",
        "Tudo é validado antes da mineração: uma operação inválida nunca vira bloco.": "Os quatro grupos aparecem em regras usadas pelo frontend e pelos testes.",
        "Pular ou repetir etapa gera INVALID_TRANSITION": "Uso funcional, não decorativo",
        "Estado final: nenhuma alteração é aceita": "Recursos marcados no código",
    }
    for current, new in resource_one.items():
        replace(slide, current, new, 10 if "\n" in current or "\n" in new else None)
    set_notes(
        slide,
        "Apontar os comentários [Recurso] no código e dar um exemplo de cada um dos quatro primeiros grupos.",
    )

    # 8. Recursos de Solidity II
    slide = prs.slides[7]
    replace(
        slide,
        "Regras do contrato inteligente",
        "Recursos Solidity II · regras e segurança",
    )
    resource_two = {
        "register_lot\nProdutor": "Lot · Document\nHistoryEntry",
        "CADASTRADO": "STRUCTS",
        "record_processing\nBeneficiador designado": "Role · Status",
        "BENEFICIADO": "ENUMS",
        "start_transport\nTransportador designado": "onlyRole(role)\natStatus(id, status)",
        "EM TRANSPORTE": "MODIFICADORES",
        "confirm_delivery\nDistribuidor designado": "eventos indexed\nerros customizados",
        "DISTRIBUÍDO": "EVENTOS + ERROS",
        "finalize_lot\nDistribuidor responsável": "checks · effects\ninteractions",
        "FINALIZADO": "SEGURANÇA",
        "Cada etapa exige um perfil, e só a carteira designada pela etapa anterior pode executá-la. Qualquer outra recebe ACCESS_DENIED.": "Structs organizam lotes, documentos e histórico; enums impedem estados arbitrários.",
        "Cadastrado, beneficiado, em transporte, distribuído e finalizado. Pular ou repetir etapa gera INVALID_TRANSITION, e o lote finalizado não muda mais.": "Cinco modificadores reutilizam acesso, existência, estado esperado e pausa.",
        "Origem, quantidade, etapas, responsáveis, datas e o hash dos documentos. Arquivos e dados pessoais ficam fora.": "Eventos alimentam a timeline; erros são traduzidos pelo frontend em mensagens claras.",
        "QUEM PODE": "STRUCTS + ENUMS",
        "EM QUE ORDEM": "MODIFICADORES",
        "O QUE FICA NA CADEIA": "EVENTOS + ERROS",
        "Tudo é validado antes da mineração: uma operação inválida nunca vira bloco.": "NatSpec, paginação e checks-effects-interactions deixam o contrato explicável e seguro.",
        "Pular ou repetir etapa gera INVALID_TRANSITION": "Erros próprios mostram a causa",
        "Estado final: nenhuma alteração é aceita": "Eventos permitem auditoria",
    }
    for current, new in resource_two.items():
        replace(slide, current, new, 10 if "\n" in current or "\n" in new else None)
    set_notes(
        slide,
        "Mostrar struct Lot, enums Role/Status, modifiers com parâmetro e eventos indexed. Explicar o saque no padrão CEI.",
    )

    # 9. Separador da demonstração
    slide = prs.slides[8]
    replace(slide, "Demonstração", "Demonstração\nna Sepolia")
    set_notes(
        slide,
        "Reservar cinco minutos: conectar, ler, cadastrar com ETH, provocar erro, mostrar evento e abrir no Etherscan.",
    )

    # 10. Testes
    slide = prs.slides[9]
    replace(slide, "TESTES", "TESTES E SEGURANÇA")
    replace(
        slide,
        "251 testes automatizados aprovados, com 97% de cobertura, e 48 cenários documentados:",
        "Contrato, integração Web3 e interface foram verificados antes do deploy público:",
        18,
    )
    replace(
        slide,
        "16 operações válidas confirmadas em bloco.",
        "Solidity 0.8.34, optimizer com 200 runs e bytecode abaixo do limite da EVM.",
        16,
    )
    replace(
        slide,
        "27 entradas inválidas ou sem permissão rejeitadas, sem criar bloco.",
        "Fluxo completo e exceções executados em uma Ethereum local isolada.",
        16,
    )
    replace(
        slide,
        "5 adulterações de bloco detectadas pela validação da cadeia.",
        "Frontend validado sem erro JavaScript em desktop, tablet e celular.",
        16,
    )
    set_notes(
        slide,
        "Mencionar os testes de permissão, taxa incorreta, ator errado, etapa errada, documento repetido, pausa e saque.",
    )

    # 11. Lições e limitações
    slide = prs.slides[10]
    replace(slide, "limitações", "lições e limitações")
    replace(
        slide,
        "Nó único: a adulteração é detectada, mas não há outros nós para recusar a versão alterada.",
        "Dados on-chain são públicos e permanentes: arquivos e informações pessoais não devem ser gravados.",
        16,
    )
    replace(
        slide,
        "Prova de trabalho didática: a dificuldade é baixa para a demonstração rodar rápido.",
        "SepoliaETH não tem valor real, mas cada escrita exige saldo e pode levar alguns segundos.",
        16,
    )
    replace(
        slide,
        "Carteiras locais: as chaves de demonstração ficam no gateway, e não em uma carteira externa.",
        "O IPFS precisa de pinning para manter o arquivo disponível; o hash continua verificável.",
        16,
    )
    set_notes(
        slide,
        "Explicar que MetaMask resolve identidade, não verdade do dado; gas influencia o desenho e IPFS exige disponibilidade externa.",
    )

    # 12. Conclusão
    slide = prs.slides[11]
    replace(
        slide,
        "Histórico do lote verificável, do produtor ao consumidor",
        "Histórico público do lote, do produtor ao consumidor",
        18,
    )
    replace(
        slide,
        "Regras de negócio aplicadas antes de gravar",
        "Perfis e custódia validados pelo contrato Solidity",
        18,
    )
    replace(
        slide,
        "Adulteração detectada pela validação da cadeia",
        "MetaMask, eventos, Etherscan, hashes e IPFS integrados",
        18,
    )
    replace(
        slide,
        "Próximos passos: rede com vários nós e carteira externa",
        "Próximos passos: auditoria externa, oráculos e pinning redundante",
        18,
    )
    set_notes(
        slide,
        "Fechar retomando problema, solução completa e aprendizados. Todos devem estar prontos para a arguição.",
    )

    # 13. Encerramento
    slide = prs.slides[12]
    set_notes(
        slide,
        "Abrir para perguntas e deixar o repositório, a dApp e o Etherscan prontos para consulta.",
    )

    # Marca institucional nas páginas de abertura e encerramento.
    for branded_slide in (prs.slides[0], prs.slides[12]):
        branded_slide.shapes.add_picture(
            str(UEA_LOGO), Inches(17.1), Inches(9.75), width=Inches(2.2)
        )


def convert_to_pdf() -> None:
    """Convert the deck to PDF with LibreOffice when it is available."""
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise RuntimeError(
            "LibreOffice não encontrado; o PPTX foi gerado, mas o PDF não."
        )
    subprocess.run(
        [
            executable,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(SLIDES),
            str(OUTPUT),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if not PDF.exists():
        raise RuntimeError("O LibreOffice não produziu o PDF esperado.")


def main() -> None:
    """Build the updated PPTX and PDF."""
    prs = Presentation(TEMPLATE)
    prs.core_properties.title = "EcoOrigem - dApp Ethereum Sepolia"
    prs.core_properties.subject = (
        "Entrega 2 - Oficina de Desenvolvimento de Sistemas III"
    )
    update_deck(prs)
    prs.save(OUTPUT)
    convert_to_pdf()
    print(f"Apresentação atualizada: {OUTPUT.relative_to(ROOT)}")
    print(f"PDF atualizado: {PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
