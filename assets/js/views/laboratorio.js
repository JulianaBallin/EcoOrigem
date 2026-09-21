// Integrity laboratory: shows how tampering with stored data is detected.
import { api, ApiError, append, clear, h, icon, prettyJson, setBusy, toast } from "../lib.js";
import { refreshCore, state } from "../state.js";

function reportCard(report) {
  if (report.valid) {
    return h("div", { class: "notice ok" }, h("div", { class: "row" }, icon("shield", 18), h("strong", {}, "Cadeia íntegra."), `${report.checked_blocks} bloco(s) verificados.`));
  }
  return h(
    "div",
    { class: "notice bad" },
    h("div", { class: "row" }, icon("alert", 18), h("strong", {}, `Adulteração detectada a partir do bloco ${report.first_invalid_block}.`)),
    h("ul", { class: "list-plain", style: "margin-top:8px" }, report.issues.map((issue) => h("li", {}, h("strong", {}, `Bloco ${issue.block_index}`), " ", h("span", { class: "mono" }, issue.code), ` ${issue.message}`))),
  );
}

export const laboratorio = {
  id: "laboratorio",
  async render(root) {
    const result = h("div", { "aria-live": "polite" });
    let blocks = [];
    try {
      blocks = (await api.get("blocks", { limit: 200, order: "asc" })).blocks.filter((b) => b.transaction_count > 0);
    } catch {
      blocks = [];
    }
    const blockSelect = h("select", { id: "lab-block" }, blocks.map((b) => h("option", { value: b.index }, `Bloco #${b.index} (${b.transactions[0].method})`)));
    if (blocks.length) blockSelect.value = String(blocks[blocks.length - 1].index);
    const changes = h("textarea", { id: "lab-changes", rows: 3, class: "mono" });
    changes.value = prettyJson({ quantity_kg: 9999 });
    const remine = h("input", { type: "checkbox", id: "lab-remine" });

    const call = async (button, fn, busy) => {
      setBusy(button, true, busy);
      try {
        const report = await fn();
        clear(result).append(reportCard(report));
        await refreshCore();
      } catch (error) {
        if (!(error instanceof ApiError) && !(error instanceof SyntaxError)) throw error;
        clear(result).append(h("div", { class: "notice bad" }, error.message));
        toast(error.message, true);
      } finally {
        setBusy(button, false, busy);
      }
    };
    const tamper = h("button", { type: "button", class: "btn danger", onclick: () => call(tamper, () => api.post("lab/tamper", { block_index: Number(blockSelect.value), changes: JSON.parse(changes.value), remine: remine.checked }), "Adulterando…") }, icon("alert", 16), "Adulterar dado gravado");
    const validate = h("button", { type: "button", class: "btn secondary", onclick: () => call(validate, () => api.get("validate"), "Validando…") }, icon("shield", 16), "Validar cadeia");
    const restore = h("button", { type: "button", class: "btn", onclick: () => call(restore, () => api.post("lab/restore"), "Restaurando…") }, icon("refresh", 16), "Restaurar da cópia em disco");

    append(clear(root), [
      h("div", { class: "view-head" }, h("div", {}, h("h1", {}, "Integridade e imutabilidade"), h("p", {}, "Altere um dado já gravado e veja a validação da cadeia detectar a fraude. A alteração acontece só em memória; o arquivo em disco não é modificado."))),
      state.status?.lab_enabled === false ? h("div", { class: "notice warn" }, "O laboratório está desativado neste nó.") : null,
      h(
        "div",
        { class: "grid split" },
        h(
          "div",
          { class: "card stack" },
          h("h2", {}, "Simular adulteração"),
          h("label", { class: "field", htmlFor: "lab-block" }, "Bloco a adulterar", blockSelect),
          h("label", { class: "field", htmlFor: "lab-changes" }, "Campos dos argumentos da transação (JSON)", changes, h("span", { class: "field-hint" }, "Exemplo: troca a quantidade de um lote já registrado.")),
          h("label", { class: "row", htmlFor: "lab-remine" }, remine, h("span", {}, "Recalcular raiz de Merkle e refazer a prova de trabalho do bloco (fraude sofisticada)")),
          h("div", { class: "row" }, tamper, validate, restore),
          result,
        ),
        h(
          "div",
          { class: "card stack" },
          h("h2", {}, "O que acontece"),
          h(
            "ol",
            { class: "list-plain" },
            h("li", {}, "Sem recalcular nada: a raiz de Merkle e a assinatura da transação deixam de conferir no bloco alterado."),
            h("li", {}, "Recalculando o bloco: o hash muda e o campo hash anterior do bloco seguinte deixa de coincidir, quebrando a cadeia."),
            h("li", {}, "Para esconder a fraude, o atacante precisaria refazer a prova de trabalho de todos os blocos seguintes."),
            h("li", {}, "Com a integridade comprometida, o nó bloqueia novas operações até a restauração."),
          ),
          h("p", { class: "hint" }, "Limitação: em um único nó local não há rede para recusar a versão adulterada. Em uma rede real, os demais participantes rejeitariam a cadeia alterada."),
        ),
      ),
    ]);
  },
};
