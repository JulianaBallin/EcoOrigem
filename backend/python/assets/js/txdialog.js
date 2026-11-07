// Transaction detail dialog with the Merkle inclusion proof.
import { api, ApiError, copyButton, EVENT_LABEL, formatDateTime, h, icon, openDialog, prettyJson } from "./lib.js";
import { nameOf } from "./state.js";

export async function showTransaction(txHash) {
  openDialog("Detalhes da transação", h("div", { class: "empty" }, "Carregando…"));
  try {
    const tx = await api.get(`transactions/${txHash}`);
    let proof = null;
    if (tx.status === "confirmed") {
      try {
        proof = await api.get(`transactions/${txHash}/proof`);
      } catch (error) {
        if (!(error instanceof ApiError)) throw error;
      }
    }
    openDialog("Detalhes da transação", body(tx, proof));
  } catch (error) {
    openDialog("Detalhes da transação", h("div", { class: "notice bad" }, error.message));
  }
}

function body(tx, proof) {
  return h(
    "div",
    { class: "stack" },
    h(
      "dl",
      { class: "kv" },
      h("dt", {}, "Hash"),
      h("dd", {}, h("span", { class: "hash" }, tx.hash), copyButton(tx.hash)),
      h("dt", {}, "Tipo"),
      h("dd", {}, tx.type === "deploy" ? "Implantação do contrato" : `Chamada de ${tx.method}`),
      h("dt", {}, "Remetente"),
      h("dd", {}, h("strong", {}, nameOf(tx.sender)), " ", h("span", { class: "hash" }, tx.sender)),
      h("dt", {}, "Nonce"),
      h("dd", {}, String(tx.nonce)),
      h("dt", {}, "Data"),
      h("dd", {}, formatDateTime(tx.timestamp)),
      h("dt", {}, "Bloco"),
      h("dd", {}, tx.block_index === null ? "Pendente de mineração" : h("a", { href: `#/blockchain/${tx.block_index}` }, `#${tx.block_index}`)),
      h("dt", {}, "Assinatura Ed25519"),
      h("dd", {}, h("span", { class: "hash" }, tx.signature)),
    ),
    h("div", {}, h("h3", {}, "Argumentos"), h("pre", { class: "json" }, prettyJson(tx.args))),
    tx.events?.length
      ? h("div", {}, h("h3", {}, "Eventos emitidos"), h("div", { class: "pill-list" }, tx.events.map((e) => h("span", { class: "badge ok" }, EVENT_LABEL[e.name] || e.name))))
      : null,
    proof ? merkle(proof) : null,
  );
}

function merkle(proof) {
  return h(
    "div",
    { class: "stack" },
    h("h3", {}, "Prova de inclusão (árvore de Merkle)"),
    h("p", { class: "hint" }, "Com poucos hashes irmãos é possível provar que esta transação pertence ao bloco, sem conhecer as demais."),
    h(
      "div",
      { class: `notice ${proof.valid ? "ok" : "bad"}` },
      h("div", { class: "row" }, icon(proof.valid ? "shield" : "alert", 18), h("strong", {}, proof.valid ? "Prova válida: a raiz recalculada coincide com a do bloco." : "Prova inválida.")),
    ),
    h("dl", { class: "kv" }, h("dt", {}, "Raiz de Merkle"), h("dd", {}, h("span", { class: "hash" }, proof.merkle_root))),
    proof.proof.length
      ? h("ol", { class: "list-plain" }, proof.proof.map((step) => h("li", {}, `Hash irmão à ${step.side === "left" ? "esquerda" : "direita"}: `, h("span", { class: "hash" }, step.hash))))
      : h("p", { class: "hint" }, "Bloco com uma única transação: o hash da transação é a própria raiz."),
  );
}
