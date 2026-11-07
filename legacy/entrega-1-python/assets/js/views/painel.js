// Dashboard: overview of the chain, the contract and the recent activity.
import { api, clear, copyButton, EVENT_LABEL, formatDateTime, h, icon, shortHash, STATUS_LABEL, STATUS_ORDER } from "../lib.js";
import { nameOf, state } from "../state.js";

const kpi = (label, value, sub) =>
  h("div", { class: "card kpi" }, h("div", { class: "label" }, label), h("div", { class: "value" }, String(value)), h("div", { class: "sub" }, sub));

function pipeline(contract) {
  const counts = contract?.lots_by_status || {};
  return h(
    "div",
    { class: "pipeline", role: "list", "aria-label": "Lotes por etapa" },
    STATUS_ORDER.map((status) =>
      h(
        "div",
        { class: `stage${counts[status] ? " has" : ""}`, role: "listitem" },
        h("div", { class: "bubble" }, String(counts[status] || 0)),
        h("div", { class: "name" }, STATUS_LABEL[status]),
      ),
    ),
  );
}

function onChainExplainer() {
  const item = (text) => h("li", {}, text);
  return h(
    "div",
    { class: "card" },
    h("div", { class: "card-head" }, h("h2", {}, "Quais dados ficam na blockchain")),
    h(
      "div",
      { class: "two-cols" },
      h(
        "div",
        { class: "stack" },
        h("h3", {}, "Registrado na blockchain"),
        h(
          "ul",
          { class: "list-plain" },
          item("Identificador, produto, origem, quantidade e data de coleta do lote"),
          item("Status atual e cada mudança de etapa, com data e bloco"),
          item("Endereço da carteira responsável por cada operação"),
          item("Perfis concedidos e revogados pelo administrador"),
          item("Hash SHA-256 de documentos anexados (certificados, laudos)"),
          item("Assinatura digital de cada transação"),
        ),
      ),
      h(
        "div",
        { class: "stack" },
        h("h3", {}, "Mantido fora da blockchain"),
        h(
          "ul",
          { class: "list-plain" },
          item("Arquivos dos documentos: apenas o hash é gravado"),
          item("Dados pessoais de produtores e trabalhadores"),
          item("Chaves privadas das carteiras (ficam no keystore local)"),
          item("Registro das operações rejeitadas (log local do nó)"),
        ),
        h("p", { class: "hint" }, "O hash permite provar que um arquivo não foi alterado sem expô-lo publicamente."),
      ),
    ),
  );
}

async function recentActivity(list) {
  try {
    const { lots } = await api.get("contract/lots");
    const events = lots.flatMap((lot) => lot.history.map((event) => ({ ...event, product: lot.product })));
    events.sort((a, b) => b.timestamp - a.timestamp);
    clear(list);
    if (!events.length) {
      list.append(h("div", { class: "empty" }, "Nenhuma operação registrada ainda."));
      return;
    }
    const table = h(
      "table",
      {},
      h("thead", {}, h("tr", {}, ["Operação", "Lote", "Responsável", "Bloco", "Data"].map((t) => h("th", { scope: "col" }, t)))),
      h(
        "tbody",
        {},
        events.slice(0, 8).map((event) =>
          h(
            "tr",
            {},
            h("td", {}, EVENT_LABEL[event.name] || event.name),
            h("td", {}, h("a", { href: `#/consultar/${event.lot_id}` }, `${event.lot_id} ${event.product}`)),
            h("td", {}, nameOf(event.actor)),
            h("td", {}, event.block_index === null ? "pendente" : `#${event.block_index}`),
            h("td", {}, formatDateTime(event.timestamp)),
          ),
        ),
      ),
    );
    list.append(h("div", { class: "table-wrap" }, table));
  } catch {
    clear(list).append(h("div", { class: "empty" }, "Não foi possível carregar a atividade recente."));
  }
}

export const painel = {
  id: "painel",
  signature: () => JSON.stringify([state.status?.height, state.status?.pending, state.status?.rejections, state.contract?.lot_count, state.status?.integrity]),
  render(root) {
    const { status, contract } = state;
    clear(root);
    if (!status) {
      root.append(h("div", { class: "empty" }, "Aguardando a blockchain local."));
      return;
    }
    const activity = h("div", {}, h("div", { class: "empty" }, "Carregando…"));
    root.append(
      h("div", { class: "view-head" }, h("div", {}, h("h1", {}, "Painel"), h("p", {}, "Estado da blockchain local, do contrato inteligente e dos lotes rastreados."))),
      h(
        "div",
        { class: "grid cols-4" },
        kpi("Blocos", status.height, `Dificuldade ${status.difficulty} (zeros iniciais no hash)`),
        kpi("Transações", status.transactions, `${status.pending} pendente(s) para minerar`),
        kpi("Lotes", contract?.lot_count ?? 0, "Registrados no contrato"),
        kpi("Rejeitadas", status.rejections, "Operações barradas pelas regras"),
      ),
      h(
        "div",
        { class: "grid cols-2", style: "margin-top:18px" },
        h(
          "div",
          { class: "card" },
          h("div", { class: "card-head" }, h("h2", {}, "Ciclo de vida dos lotes"), h("span", { class: "hint" }, "Ordem obrigatória imposta pelo contrato")),
          pipeline(contract),
        ),
        h(
          "div",
          { class: "card" },
          h("div", { class: "card-head" }, h("h2", {}, "Integridade da cadeia")),
          status.integrity.valid
            ? h("div", { class: "notice ok" }, h("div", { class: "row" }, icon("shield", 18), h("strong", {}, "Cadeia íntegra."), h("span", {}, "Hashes, encadeamento, prova de trabalho e assinaturas conferem.")))
            : h("div", { class: "notice bad" }, h("div", { class: "row" }, icon("alert", 18), h("strong", {}, `Adulteração detectada a partir do bloco ${status.integrity.first_invalid_block}.`), h("span", {}, "Novas operações estão bloqueadas."))),
          status.last_mining
            ? h("p", { class: "hint", style: "margin-top:10px" }, `Último bloco minerado: #${status.last_mining.block_index}, ${status.last_mining.attempts.toLocaleString("pt-BR")} tentativas de nonce em ${status.last_mining.seconds.toLocaleString("pt-BR")} s.`)
            : null,
        ),
      ),
      h(
        "div",
        { class: "grid cols-2", style: "margin-top:18px" },
        h(
          "div",
          { class: "card" },
          h("div", { class: "card-head" }, h("h2", {}, "Contrato inteligente")),
          contract
            ? h(
                "dl",
                { class: "kv" },
                h("dt", {}, "Nome"),
                h("dd", {}, contract.name),
                h("dt", {}, "Endereço"),
                h("dd", {}, h("span", { class: "hash" }, contract.address), copyButton(contract.address)),
                h("dt", {}, "Administrador"),
                h("dd", {}, nameOf(contract.admin), " ", h("span", { class: "mono" }, shortHash(contract.admin, 6, 4))),
                h("dt", {}, "Implantado no"),
                h("dd", {}, `bloco #${contract.deployed_block}`),
                h("dt", {}, "Produtos aceitos"),
                h("dd", {}, h("div", { class: "pill-list" }, contract.allowed_products.map((p) => h("span", { class: "badge role" }, p)))),
              )
            : h("div", { class: "empty" }, "Contrato ainda não implantado."),
        ),
        onChainExplainer(),
      ),
      h("div", { class: "card", style: "margin-top:18px" }, h("div", { class: "card-head" }, h("h2", {}, "Atividade recente"), h("a", { class: "btn secondary small", href: "#/consultar" }, "Ver todos os lotes")), activity),
    );
    recentActivity(activity);
  },
};

