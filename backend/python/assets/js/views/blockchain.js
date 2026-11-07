// Block explorer: the chain, its blocks, transactions and integrity report.
import { api, ApiError, clear, copyButton, formatDateTime, h, icon, powHash, prettyJson, setBusy, toast } from "../lib.js";
import { nameOf, refreshCore, state } from "../state.js";
import { showTransaction } from "../txdialog.js";

const PAGE = 15;
let report = { valid: true, issues: [] };
let listSlot = null;
let moreSlot = null;
let loaded = 0;
let total = 0;

const issuesOf = (index) => report.issues.filter((issue) => issue.block_index === index);

function txItem(tx) {
  return h(
    "div",
    { class: "tx-item" },
    h("div", { class: "row" }, h("strong", {}, tx.type === "deploy" ? "Implantação do contrato" : tx.method), h("span", { class: "spacer" }), h("span", {}, "por ", h("strong", {}, nameOf(tx.sender)))),
    h("div", {}, h("span", { class: "hash" }, tx.hash)),
    h("pre", { class: "json" }, prettyJson(tx.args)),
    h("div", { class: "row" }, h("button", { type: "button", class: "btn secondary small", onclick: () => showTransaction(tx.hash) }, icon("link", 14), "Detalhes e prova de Merkle")),
  );
}

function blockCard(block, open = false) {
  const problems = issuesOf(block.index);
  const invalid = problems.length > 0;
  return h(
    "article",
    { class: `block-card${invalid ? " invalid" : ""}`, id: `block-${block.index}` },
    h(
      "div",
      { class: "block-title" },
      h("div", { class: "block-num", "aria-hidden": "true" }, `#${block.index}`),
      h("h3", {}, `Bloco #${block.index}`),
      block.index === 0 ? h("span", { class: "badge info" }, "Gênesis") : null,
      h("span", { class: "badge" }, `${block.transaction_count} transação(ões)`),
      invalid ? h("span", { class: "badge bad" }, "Inválido") : h("span", { class: "badge ok" }, "Íntegro"),
      h("span", { class: "spacer" }),
      h("span", { class: "hint" }, formatDateTime(block.timestamp)),
    ),
    h(
      "div",
      { class: "block-body" },
      h(
        "dl",
        { class: "kv" },
        h("dt", {}, "Hash"),
        h("dd", {}, powHash(block.hash), copyButton(block.hash)),
        h("dt", {}, "Hash anterior"),
        h("dd", {}, h("span", { class: "hash" }, block.previous_hash)),
        h("dt", {}, "Raiz de Merkle"),
        h("dd", {}, h("span", { class: "hash" }, block.merkle_root)),
        h("dt", {}, "Nonce e dificuldade"),
        h("dd", {}, `${block.nonce.toLocaleString("pt-BR")} tentativas, ${block.difficulty} zeros iniciais`),
        block.note ? [h("dt", {}, "Nota"), h("dd", {}, block.note)] : null,
      ),
      invalid ? h("div", { class: "notice bad" }, h("strong", {}, "Problemas encontrados"), h("ul", { class: "list-plain" }, problems.map((p) => h("li", {}, h("span", { class: "mono" }, p.code), ` ${p.message}`)))) : null,
    ),
    block.transactions.length ? h("details", { class: "txs", open }, h("summary", {}, `Transações do bloco (${block.transactions.length})`), block.transactions.map(txItem)) : null,
  );
}

async function loadPage(reset = false) {
  if (reset) {
    loaded = 0;
    clear(listSlot);
  }
  const page = await api.get("blocks", { offset: loaded, limit: PAGE });
  total = page.total;
  listSlot.append(...page.blocks.map((block) => blockCard(block)));
  loaded += page.blocks.length;
  clear(moreSlot);
  if (loaded < total) {
    moreSlot.append(h("button", { type: "button", class: "btn secondary", onclick: () => loadPage() }, `Carregar blocos mais antigos (${total - loaded})`));
  }
}

async function validate(button) {
  if (button) setBusy(button, true, "Validando…");
  try {
    report = await api.get("validate");
    await refreshCore();
    toast(report.valid ? "Cadeia íntegra: todos os blocos conferem." : `Adulteração detectada no bloco ${report.first_invalid_block}.`, !report.valid);
  } finally {
    if (button) setBusy(button, false, "Validando…");
  }
}

export const blockchain = {
  id: "blockchain",
  signature: () => `${state.status?.height}|${state.status?.integrity?.valid}|${state.status?.pending}`,
  async render(root, params) {
    listSlot = h("div", { class: "chain" });
    moreSlot = h("div", { class: "row", style: "justify-content:center; margin-top:18px" });
    const selectedSlot = h("div", {});
    const banner = h("div", {});
    const validateButton = h("button", { type: "button", class: "btn", onclick: () => validate(validateButton).then(() => blockchain.render(root, params)) }, icon("shield", 16), "Validar cadeia");
    const pending = state.status?.pending || 0;
    const mineButton = pending
      ? h(
          "button",
          {
            type: "button",
            class: "btn secondary",
            onclick: async () => {
              setBusy(mineButton, true);
              try {
                await api.post("mine");
                await refreshCore();
                toast("Bloco minerado.");
                blockchain.render(root, params);
              } catch (error) {
                if (!(error instanceof ApiError)) throw error;
                toast(error.message, true);
                setBusy(mineButton, false);
              }
            },
          },
          icon("pickaxe", 16),
          `Minerar ${pending} transação(ões) pendente(s)`,
        )
      : null;
    clear(root).append(
      h("div", { class: "view-head" }, h("div", {}, h("h1", {}, "Blockchain"), h("p", {}, "Cada bloco guarda o hash do anterior. Alterar qualquer dado muda o hash e quebra a cadeia dali em diante.")), h("div", { class: "row" }, mineButton, validateButton)),
      banner,
      selectedSlot,
      listSlot,
      moreSlot,
    );
    try {
      report = await api.get("validate");
    } catch {
      report = { valid: true, issues: [] };
    }
    banner.append(
      report.valid
        ? h("div", { class: "notice ok", style: "margin-bottom:18px" }, h("div", { class: "row" }, icon("shield", 18), h("strong", {}, "Cadeia íntegra."), `${state.status?.height ?? ""} bloco(s) verificados: hashes, encadeamento, prova de trabalho, raízes de Merkle e assinaturas.`))
        : h("div", { class: "notice bad", style: "margin-bottom:18px" }, h("div", { class: "row" }, icon("alert", 18), h("strong", {}, `Cadeia inválida a partir do bloco ${report.first_invalid_block}.`), "Veja os blocos marcados abaixo.")),
    );
    const wanted = params[0] !== undefined ? Number(params[0]) : null;
    if (Number.isInteger(wanted)) {
      try {
        const block = await api.get(`blocks/${wanted}`);
        selectedSlot.append(h("h2", { style: "margin-bottom:10px" }, "Bloco selecionado"), blockCard(block, true), h("hr", { class: "divider", style: "margin:22px 0" }));
      } catch (error) {
        if (!(error instanceof ApiError)) throw error;
        selectedSlot.append(h("div", { class: "notice bad", style: "margin-bottom:18px" }, error.message));
      }
    }
    await loadPage(true);
  },
};

