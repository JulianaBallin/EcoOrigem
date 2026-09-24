// Operations: forms that sign and submit transactions to the smart contract.
import { api, ApiError, clear, copyButton, EVENT_LABEL, h, icon, LAYER_LABEL, powHash, setBusy, sha256File, STATUS_LABEL, toast } from "../lib.js";
import { activeWallet, hasRole, onChange, refreshCore, setActiveWallet, state } from "../state.js";

const ROLE_NAME = { PRODUCER: "Produtor", PROCESSOR: "Beneficiador", CARRIER: "Transportador", DISTRIBUTOR: "Distribuidor" };

const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

const OPERATIONS = [
  {
    id: "register_lot",
    title: "Registrar lote",
    role: "PRODUCER",
    summary: "Cria o lote, registra sua origem e designa o beneficiador responsável.",
    fields: [
      { name: "product", label: "Produto", type: "product", required: true },
      { name: "origin", label: "Origem (comunidade e município)", type: "text", placeholder: "Comunidade do Rio Negro, Novo Airão", required: true, wide: true },
      { name: "quantity_kg", label: "Quantidade (kg)", type: "number", placeholder: "250", required: true },
      { name: "harvest_date", label: "Data da coleta", type: "date", required: true },
      { name: "processor", label: "Beneficiador responsável", type: "wallet", walletRole: "PROCESSOR", required: true },
      { name: "document_hash", label: "Documento de origem", type: "document", wide: true },
    ],
  },
  {
    id: "record_processing",
    title: "Registrar beneficiamento",
    role: "PROCESSOR",
    summary: "O beneficiador designado registra o processamento e indica o transportador responsável.",
    fields: [
      { name: "lot_id", label: "Lote", type: "lot", required: true },
      { name: "description", label: "Descrição do beneficiamento", type: "textarea", placeholder: "Despolpamento, pasteurização e congelamento.", required: true, wide: true },
      { name: "carrier", label: "Transportador responsável", type: "wallet", walletRole: "CARRIER", required: true },
      { name: "document_hash", label: "Laudo de beneficiamento", type: "document", wide: true },
    ],
  },
  {
    id: "start_transport",
    title: "Iniciar transporte",
    role: "CARRIER",
    summary: "O transportador designado inicia o transporte e informa o distribuidor destinatário.",
    fields: [
      { name: "lot_id", label: "Lote", type: "lot", required: true },
      { name: "recipient", label: "Distribuidor destinatário", type: "wallet", walletRole: "DISTRIBUTOR", required: true },
      { name: "destination", label: "Destino", type: "text", placeholder: "Centro de distribuição, Manaus", required: true, wide: true },
    ],
  },
  {
    id: "confirm_delivery",
    title: "Confirmar recebimento",
    role: "DISTRIBUTOR",
    summary: "Lote EM_TRANSPORTE passa para DISTRIBUIDO. Só o distribuidor designado confirma.",
    fields: [
      { name: "lot_id", label: "Lote", type: "lot", required: true },
      { name: "note", label: "Observação", type: "textarea", optional: true, wide: true },
    ],
  },
  {
    id: "finalize_lot",
    title: "Finalizar lote",
    role: "DISTRIBUTOR",
    summary: "Lote DISTRIBUIDO passa para FINALIZADO e não aceita mais alterações.",
    fields: [
      { name: "lot_id", label: "Lote", type: "lot", required: true },
      { name: "note", label: "Observação", type: "textarea", optional: true, wide: true },
    ],
  },
  {
    id: "attach_document",
    title: "Anexar documento",
    role: null,
    summary: "O responsável atual registra o hash de um novo documento no lote.",
    fields: [
      { name: "lot_id", label: "Lote", type: "lot", required: true },
      { name: "document_hash", label: "Documento", type: "document", required: true, wide: true },
      { name: "description", label: "Descrição do documento", type: "text", placeholder: "Certificado orgânico 2026", required: true, wide: true },
    ],
  },
];

let lots = [];
let selectedOp = OPERATIONS[0];
let controls = {};
let noticeSlot = null;
let outcomeSlot = null;
let formSlot = null;

async function loadLots() {
  try {
    lots = (await api.get("contract/lots")).lots;
  } catch {
    lots = [];
  }
}

// ------------------------------------------------------------ controls
function buildControl(field) {
  const id = `f-${selectedOp.id}-${field.name}`;
  const optional = field.optional || field.type === "document" && !field.required;
  const label = (input, extra) =>
    h("label", { class: `field${field.wide ? " wide" : ""}`, htmlFor: id }, h("span", {}, field.label, optional ? h("span", { class: "opt" }, " (opcional)") : null), input, extra);

  switch (field.type) {
    case "textarea": {
      const el = h("textarea", { id, placeholder: field.placeholder || "", rows: 3 });
      return { root: label(el), el, get: () => el.value.trim(), set: (v) => (el.value = v) };
    }
    case "product": {
      const options = state.contract?.allowed_products || [];
      const el = h("select", { id }, options.map((p) => h("option", { value: p }, p)));
      return { root: label(el), el, get: () => el.value, set: (v) => (el.value = v) };
    }
    case "wallet": {
      const wallets = field.walletRole
        ? state.wallets.filter((w) => w.roles.includes(field.walletRole))
        : state.wallets;

      const options = wallets.length
        ? wallets.map((w) => h("option", { value: w.address }, `${w.name}${w.role_labels.length ? ` (${w.role_labels.join(", ")})` : ""}`))
        : [h("option", { value: "" }, `Nenhuma carteira com perfil ${ROLE_NAME[field.walletRole] || "necessário"}`)];

      const el = h("select", { id }, options);
      return { root: label(el), el, get: () => el.value, set: (v) => (el.value = v) };
    }
    case "lot": {
      const listId = `${id}-list`;
      const el = h("input", { id, type: "text", placeholder: "LOT-0001", autocomplete: "off", list: listId });
      el.setAttribute("list", listId);
      const datalist = h("datalist", { id: listId }, lots.map((l) => h("option", { value: l.lot_id }, `${l.product} - ${STATUS_LABEL[l.status]}`)));
      return { root: label(el, datalist), el, get: () => el.value.trim().toUpperCase(), set: (v) => (el.value = v) };
    }
    case "document":
      return buildDocumentControl(field, id, label);
    default: {
      const el = h("input", {
        id,
        type: field.type === "number" ? "number" : field.type,
        placeholder: field.placeholder || "",
        step: field.type === "number" ? "any" : false,
        autocomplete: "off",
      });
      return { root: label(el), el, get: () => el.value.trim(), set: (v) => (el.value = v) };
    }
  }
}

function buildDocumentControl(field, id, label) {
  const hashInput = h("input", { id, type: "text", placeholder: "Hash SHA-256 (64 caracteres hexadecimais)", autocomplete: "off", class: "mono" });
  const info = h("div", { class: "field-hint" }, "Selecione um arquivo: o hash é calculado no navegador. O arquivo não é enviado nem gravado.");
  const file = h("input", {
    type: "file",
    "aria-label": `Arquivo para ${field.label}`,
    onchange: async (event) => {
      const chosen = event.target.files[0];
      if (!chosen) return;
      hashInput.value = await sha256File(chosen);
      info.textContent = `Arquivo ${chosen.name} (${chosen.size.toLocaleString("pt-BR")} bytes). Somente o hash será gravado.`;
    },
  });
  const zone = h("div", { class: "dropzone" }, file, hashInput, info);
  return { root: label(zone), el: hashInput, get: () => hashInput.value.trim(), set: (v) => (hashInput.value = v) };
}

// ---------------------------------------------------------------- form
function renderForm() {
  controls = {};
  clear(formSlot);
  const grid = h("div", { class: "form-grid" });
  for (const field of selectedOp.fields) {
    const control = buildControl(field);
    controls[field.name] = control;
    grid.append(control.root);
  }
  if (controls.harvest_date) controls.harvest_date.set(today());
  const submit = h("button", { type: "submit", class: "btn" }, icon("check", 16), "Assinar e enviar à blockchain");
  formSlot.append(
    h("h2", {}, selectedOp.title),
    h("p", { class: "hint" }, selectedOp.summary),
    noticeSlot,
    h(
      "form",
      { novalidate: true, class: "stack", onsubmit: (event) => submit_(event, submit) },
      grid,
      h("div", { class: "row" }, submit, h("span", { class: "hint" }, "A validação dos dados é feita pelo contrato inteligente.")),
    ),
  );
  updateNotice();
}

function updateNotice() {
  if (!noticeSlot) return;
  clear(noticeSlot);
  const wallet = activeWallet();
  if (!wallet) return;
  if (!state.contract) {
    noticeSlot.append(h("div", { class: "notice warn" }, "O contrato ainda não foi implantado."));
    return;
  }
  const role = selectedOp.role;
  if (role && !hasRole(wallet, role)) {
    noticeSlot.append(
      h("div", { class: "notice warn" }, `A carteira ativa (${wallet.name}) não possui o perfil ${ROLE_NAME[role]}. O contrato rejeitará esta operação. Troque a carteira no topo da página.`),
    );
  } else {
    noticeSlot.append(h("div", { class: "notice info" }, `Assinando como ${wallet.name}${role ? ` (perfil ${ROLE_NAME[role]})` : ", que precisa ser o responsável atual pelo lote"}.`));
  }
}

function collectArgs() {
  const args = {};
  for (const field of selectedOp.fields) {
    const raw = controls[field.name].get();
    if (raw === "" || raw === undefined) continue;
    if (field.type === "number") {
      const parsed = Number(raw);
      args[field.name] = Number.isNaN(parsed) ? raw : parsed;
    } else args[field.name] = raw;
  }
  return args;
}

async function submit_(event, button) {
  event.preventDefault();
  Object.values(controls).forEach((c) => c.el.classList.remove("invalid"));
  setBusy(button, true);
  clear(outcomeSlot);
  try {
    const receipt = await api.post("send", { wallet: state.active, method: selectedOp.id, args: collectArgs() });
    showSuccess(receipt);
    toast(receipt.status === "confirmed" ? `Confirmado no bloco #${receipt.block_index}.` : "Transação pendente de mineração.");
    await Promise.all([refreshCore(), loadLots()]);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    showRejection(error);
    toast("Operação rejeitada.", true);
    await refreshCore();
  } finally {
    setBusy(button, false);
  }
}

function showSuccess(receipt) {
  const lotId = receipt.events.find((e) => e.lot_id)?.lot_id;
  const confirmed = receipt.status === "confirmed";
  clear(outcomeSlot).append(
    h(
      "div",
      { class: "outcome ok", role: "status" },
      h("h3", {}, icon("check", 20), confirmed ? "Operação confirmada na blockchain" : "Operação aceita e aguardando mineração"),
      h(
        "dl",
        { class: "kv" },
        h("dt", {}, "Transação"),
        h("dd", {}, h("span", { class: "hash" }, receipt.tx_hash), copyButton(receipt.tx_hash)),
        confirmed ? [h("dt", {}, "Bloco"), h("dd", {}, `#${receipt.block_index} `, powHash(receipt.block_hash))] : null,
        confirmed && receipt.mining ? [h("dt", {}, "Prova de trabalho"), h("dd", {}, `${receipt.mining.attempts.toLocaleString("pt-BR")} tentativas de nonce em ${receipt.mining.seconds.toLocaleString("pt-BR")} s`)] : null,
        h("dt", {}, "Eventos do contrato"),
        h("dd", {}, receipt.events.map((e) => h("span", { class: "badge ok", style: "margin-right:6px" }, EVENT_LABEL[e.name] || e.name))),
      ),
      h(
        "div",
        { class: "row" },
        lotId ? h("a", { class: "btn secondary small", href: `#/consultar/${lotId}` }, `Consultar ${lotId}`) : null,
        confirmed ? h("a", { class: "btn secondary small", href: `#/blockchain/${receipt.block_index}` }, `Ver bloco #${receipt.block_index}`) : null,
      ),
    ),
  );
}

function showRejection(error) {
  const field = error.details?.field;
  if (field && controls[field]) controls[field].el.classList.add("invalid");
  clear(outcomeSlot).append(
    h(
      "div",
      { class: "outcome bad", role: "alert" },
      h("h3", {}, icon("x", 20), "Operação rejeitada"),
      h("p", {}, error.message),
      h(
        "div",
        { class: "row" },
        h("span", { class: "badge bad" }, LAYER_LABEL[error.layer] || error.layer),
        h("span", { class: "badge bad mono" }, error.code),
        h("span", { class: "hint" }, "Nenhum bloco foi criado e o estado do contrato não mudou."),
      ),
      h("a", { class: "btn secondary small", href: "#/rejeicoes", style: "justify-self:start" }, "Ver registro de rejeições"),
    ),
  );
}

// ----------------------------------------------------------- scenarios
function selectOperation(id) {
  selectedOp = OPERATIONS.find((op) => op.id === id);
  renderList();
  renderForm();
}

const firstLotWith = (status) => lots.find((l) => l.status === status)?.lot_id || "";

const SCENARIOS = [
  {
    label: "Carteira sem permissão",
    apply: () => {
      setActiveWallet("intruso");
      selectOperation("register_lot");
      controls.origin.set("Comunidade do Rio Negro, Novo Airão");
      controls.quantity_kg.set("120");
    },
  },
  {
    label: "Quantidade negativa",
    apply: () => {
      setActiveWallet("produtor");
      selectOperation("register_lot");
      controls.origin.set("Reserva Extrativista do Rio Cajari");
      controls.quantity_kg.set("-5");
    },
  },
  {
    label: "Data de coleta no futuro",
    apply: () => {
      setActiveWallet("produtor");
      selectOperation("register_lot");
      controls.origin.set("Assentamento Tupé, Manaus");
      controls.quantity_kg.set("80");
      const next = new Date(Date.now() + 3 * 86400000);
      controls.harvest_date.set(next.toISOString().slice(0, 10));
    },
  },
  {
    label: "Pular etapas (finalizar lote cadastrado)",
    apply: () => {
      setActiveWallet("distribuidor");
      selectOperation("finalize_lot");
      controls.lot_id.set(firstLotWith("REGISTERED") || "LOT-0001");
    },
  },
  {
    label: "Alterar lote finalizado",
    apply: () => {
      setActiveWallet("beneficiador");
      selectOperation("record_processing");
      controls.lot_id.set(firstLotWith("FINALIZED") || "LOT-0001");
      controls.description.set("Tentativa de reprocessar lote encerrado.");
    },
  },
  {
    label: "Lote inexistente",
    apply: () => {
      setActiveWallet("beneficiador");
      selectOperation("record_processing");
      controls.lot_id.set("LOT-9999");
      controls.description.set("Beneficiamento de lote que não existe.");
    },
  },
];

// ---------------------------------------------------------------- view
let listSlot = null;
function renderList() {
  if (!listSlot) return;
  clear(listSlot).append(
    ...OPERATIONS.map((op) =>
      h(
        "button",
        { type: "button", class: "op-item", "aria-pressed": String(op.id === selectedOp.id), onclick: () => selectOperation(op.id) },
        h("span", { class: "op-title" }, op.title, op.role ? h("span", { class: "badge role" }, ROLE_NAME[op.role]) : h("span", { class: "badge role" }, "Responsável")),
        h("span", { class: "op-desc" }, op.summary),
      ),
    ),
  );
}

onChange(updateNotice);

export const registrar = {
  id: "registrar",
  async render(root, params) {
    await loadLots();
    listSlot = h("div", { class: "op-list" });
    noticeSlot = h("div", {});
    outcomeSlot = h("div", {});
    formSlot = h("div", { class: "card stack" });
    clear(root).append(
      h("div", { class: "view-head" }, h("div", {}, h("h1", {}, "Registrar operações"), h("p", {}, "Cada operação é assinada pela carteira ativa, validada pelo contrato e gravada em um novo bloco minerado."))),
      h(
        "div",
        { class: "grid split" },
        h("div", { class: "card stack" }, h("h2", {}, "Operação"), listSlot),
        h(
          "div",
          { class: "stack" },
          formSlot,
          outcomeSlot,
          h("div", { class: "card flat stack" }, h("h3", {}, "Cenários de rejeição"), h("p", { class: "hint" }, "Preenchem o formulário com uma entrada inválida ou sem permissão. Envie para ver o contrato recusar."), h("div", { class: "chips" }, SCENARIOS.map((s) => h("button", { type: "button", class: "chip-btn", onclick: s.apply }, s.label)))),
        ),
      ),
    );
    if (params[0] && OPERATIONS.some((op) => op.id === params[0])) selectedOp = OPERATIONS.find((op) => op.id === params[0]);
    renderList();
    renderForm();
  },
};
