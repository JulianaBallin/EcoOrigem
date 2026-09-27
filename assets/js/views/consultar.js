// Lot lookup: list, filters, traceability timeline and document verification.
import { api, ApiError, clear, copyButton, EVENT_LABEL, formatDateTime, formatKg, h, icon, prettyJson, sha256File, shortHash, statusBadge, STATUS_LABEL, STATUS_ORDER, toast } from "../lib.js";
import { addressLabel, nameOf } from "../state.js";
import { showTransaction } from "../txdialog.js";

let allLots = [];
let selectedId = null;
let listSlot = null;
let detailSlot = null;
const filters = { text: "", status: "" };

function matches(lot) {
  const text = filters.text.toLowerCase();
  const hay = `${lot.lot_id} ${lot.product} ${lot.origin}`.toLowerCase();
  return (!text || hay.includes(text)) && (!filters.status || lot.status === filters.status);
}

function renderList() {
  const rows = allLots.filter(matches);
  clear(listSlot);
  if (!rows.length) {
    listSlot.append(h("div", { class: "empty" }, allLots.length ? "Nenhum lote corresponde ao filtro." : "Nenhum lote registrado ainda."));
    return;
  }
  listSlot.append(
    h(
      "div",
      { class: "table-wrap" },
      h(
        "table",
        {},
        h("thead", {}, h("tr", {}, ["Lote", "Produto", "Quantidade", "Status"].map((t) => h("th", { scope: "col" }, t)))),
        h(
          "tbody",
          {},
          rows.map((lot) =>
            h(
              "tr",
              {
                class: `clickable${lot.lot_id === selectedId ? " selected" : ""}`,
                tabIndex: 0,
                onclick: () => open(lot.lot_id),
                onkeydown: (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), open(lot.lot_id)),
              },
              h("td", {}, h("strong", {}, lot.lot_id)),
              h("td", {}, lot.product, h("div", { class: "hint" }, lot.origin)),
              h("td", {}, formatKg(lot.quantity_kg)),
              h("td", {}, statusBadge(lot.status)),
            ),
          ),
        ),
      ),
    ),
  );
}

async function open(lotId) {
  selectedId = lotId;
  history.replaceState(null, "", `#/consultar/${lotId}`);
  renderList();
  clear(detailSlot).append(h("div", { class: "empty" }, "Consultando o contrato…"));
  try {
    renderLot(await api.get(`contract/lots/${encodeURIComponent(lotId)}`));
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    clear(detailSlot).append(h("div", { class: "notice bad" }, h("strong", {}, error.code), ` ${error.message}`));
  }
}

function stepper(lot) {
  const current = STATUS_ORDER.indexOf(lot.status);
  return h(
    "div",
    { class: "stepper", role: "list", "aria-label": "Etapas do lote" },
    STATUS_ORDER.map((status, index) =>
      h(
        "div",
        { class: `step${index < current ? " done" : ""}${index === current ? " current" : ""}${index === current && status === "FINALIZED" ? " done" : ""}`, role: "listitem" },
        h("div", { class: "node" }, index < current || (index === current && status === "FINALIZED") ? icon("check", 16) : String(index + 1)),
        STATUS_LABEL[status],
      ),
    ),
  );
}

function verifier(lot) {
  const result = h("div", { "aria-live": "polite" });
  const input = h("input", {
    type: "file",
    "aria-label": "Arquivo a verificar",
    onchange: async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      const digest = await sha256File(file);
      try {
        const answer = await api.post("contract/documents/verify", { lot_id: lot.lot_id, hash: digest });
        clear(result).append(
          answer.registered
            ? h("div", { class: "notice ok" }, h("strong", {}, "Documento autêntico. "), `O hash do arquivo coincide com o registrado (${answer.document.description}, bloco #${answer.document.block_index}).`)
            : h("div", { class: "notice bad" }, h("strong", {}, "Documento não registrado ou alterado. "), "O hash do arquivo não consta neste lote.", h("div", { class: "hash" }, digest)),
        );
      } catch (error) {
        clear(result).append(h("div", { class: "notice bad" }, error.message));
      }
    },
  });
  return h("div", { class: "dropzone" }, h("strong", {}, "Verificar autenticidade de um arquivo"), input, h("span", { class: "field-hint" }, "O hash é calculado no navegador e comparado com os hashes gravados no lote."), result);
}

function renderLot(lot) {
  clear(detailSlot).append(
    h(
      "div",
      { class: "card stack" },
      h("div", { class: "card-head" }, h("div", {}, h("h2", {}, `${lot.lot_id} · ${lot.product}`), h("span", { class: "hint" }, lot.origin)), statusBadge(lot.status)),
      stepper(lot),
      h(
        "dl",
        { class: "kv" },
        h("dt", {}, "Quantidade"),
        h("dd", {}, formatKg(lot.quantity_kg)),
        h("dt", {}, "Data da coleta"),
        h("dd", {}, lot.harvest_date.split("-").reverse().join("/")),
        h("dt", {}, "Produtor"),
        h("dd", {}, addressLabel(lot.producer)),
        h("dt", {}, "Responsável atual"),
        h("dd", {}, addressLabel(lot.custodian)),
        lot.recipient ? [h("dt", {}, "Distribuidor designado"), h("dd", {}, addressLabel(lot.recipient)), h("dt", {}, "Destino"), h("dd", {}, lot.destination)] : null,
        h("dt", {}, "Última atualização"),
        h("dd", {}, formatDateTime(lot.updated_at)),
      ),
    ),
    h(
      "div",
      { class: "card stack", style: "margin-top:18px" },
      h("h2", {}, "Histórico de rastreabilidade"),
      h(
        "ol",
        { class: "timeline" },
        lot.history.map((event) =>
          h(
            "li",
            {},
            h("div", { class: "when" }, formatDateTime(event.timestamp)),
            h("div", { class: "what" }, EVENT_LABEL[event.name] || event.name),
            h(
              "div",
              { class: "meta" },
              h("span", {}, "por ", h("strong", {}, nameOf(event.actor))),
              event.to_status ? [event.from_status ? statusBadge(event.from_status) : null, event.from_status ? "→" : null, statusBadge(event.to_status)] : null,
              event.block_index !== null ? h("a", { href: `#/blockchain/${event.block_index}` }, `bloco #${event.block_index}`) : null,
              h("button", { type: "button", class: "linkish", onclick: () => showTransaction(event.tx_hash) }, `transação ${shortHash(event.tx_hash, 8, 4)}`),
            ),
            event.data?.description || event.data?.note ? h("div", { class: "hint" }, event.data.description || event.data.note) : null,
          ),
        ),
      ),
    ),
    h(
      "div",
      { class: "card stack", style: "margin-top:18px" },
      h("h2", {}, "Documentos registrados"),
      lot.documents.length
        ? h(
            "div",
            { class: "stack" },
            lot.documents.map((doc) =>
              h("div", { class: "tx-item" }, h("strong", {}, doc.description), h("div", {}, h("span", { class: "hash" }, doc.hash), copyButton(doc.hash)), h("span", { class: "hint" }, `Registrado por ${nameOf(doc.added_by)} no bloco #${doc.block_index} em ${formatDateTime(doc.timestamp)}`)),
            ),
          )
        : h("p", { class: "hint" }, "Nenhum documento anexado a este lote."),
      verifier(lot),
    ),
    h("details", { class: "card", style: "margin-top:18px" }, h("summary", {}, "Dados brutos lidos do contrato (JSON)"), h("pre", { class: "json", style: "margin-top:10px" }, prettyJson(lot))),
  );
}

export const consultar = {
  id: "consultar",
  async render(root, params) {
    const search = h("input", { type: "search", placeholder: "Identificador do lote, por exemplo LOT-0001", "aria-label": "Identificador do lote" });
    const status = h(
      "select",
      { "aria-label": "Filtrar por status", onchange: (e) => ((filters.status = e.target.value), renderList()) },
      h("option", { value: "" }, "Todos os status"),
      STATUS_ORDER.map((s) => h("option", { value: s }, STATUS_LABEL[s])),
    );
    status.value = filters.status;
    listSlot = h("div", {});
    detailSlot = h("div", {}, h("div", { class: "card" }, h("div", { class: "empty" }, "Selecione um lote na lista ou consulte pelo identificador para ver o histórico completo.")));
    clear(root).append(
      h("div", { class: "view-head" }, h("div", {}, h("h1", {}, "Consultar lotes"), h("p", {}, "Leitura direta do contrato. Qualquer pessoa, inclusive o consumidor, pode consultar sem carteira."))),
      h(
        "form",
        {
          class: "row",
          style: "margin-bottom:18px",
          onsubmit: (event) => {
            event.preventDefault();
            const value = search.value.trim().toUpperCase();
            if (value) open(value);
          },
        },
        h("div", { style: "flex:1; min-width:240px" }, search),
        h("button", { class: "btn", type: "submit" }, "Consultar lote"),
      ),
      h(
        "div",
        { class: "grid split" },
        h("div", { class: "card stack" }, h("div", { class: "row" }, h("input", { type: "search", placeholder: "Filtrar por produto ou origem", "aria-label": "Filtrar lista", value: filters.text, oninput: (e) => ((filters.text = e.target.value), renderList()) }), status), listSlot),
        detailSlot,
      ),
    );
    try {
      allLots = (await api.get("contract/lots")).lots;
    } catch {
      allLots = [];
      toast("Não foi possível carregar os lotes.", true);
    }
    const wanted = params[0] || selectedId;
    selectedId = wanted || null;
    renderList();
    if (wanted) open(wanted);
  },
};
