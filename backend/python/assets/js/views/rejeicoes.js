// Log of rejected operations kept by the node.
import { api, clear, formatDateTime, h, LAYER_LABEL } from "../lib.js";
import { nameOf, state } from "../state.js";

export const rejeicoes = {
  id: "rejeicoes",
  signature: () => String(state.status?.rejections),
  async render(root) {
    let items = [];
    try {
      items = (await api.get("rejections", { limit: 100 })).rejections;
    } catch {
      items = [];
    }
    clear(root).append(
      h("div", { class: "view-head" }, h("div", {}, h("h1", {}, "Operações rejeitadas"), h("p", {}, "Toda tentativa barrada pelas regras do contrato ou pela validação do nó fica registrada aqui. Rejeições não geram bloco e não alteram o estado."))),
      h(
        "div",
        { class: "card" },
        items.length
          ? h(
              "div",
              { class: "table-wrap" },
              h(
                "table",
                {},
                h("thead", {}, h("tr", {}, ["Data", "Camada", "Código", "Motivo", "Carteira", "Método"].map((t) => h("th", { scope: "col" }, t)))),
                h(
                  "tbody",
                  {},
                  items.map((item) =>
                    h(
                      "tr",
                      {},
                      h("td", {}, formatDateTime(item.timestamp)),
                      h("td", {}, h("span", { class: "badge bad" }, LAYER_LABEL[item.layer] || item.layer)),
                      h("td", {}, h("span", { class: "mono" }, item.code)),
                      h("td", {}, item.message),
                      h("td", {}, item.sender ? nameOf(item.sender) : "-"),
                      h("td", {}, item.method || "-"),
                    ),
                  ),
                ),
              ),
            )
          : h("div", { class: "empty" }, "Nenhuma operação rejeitada até agora. Use os cenários da aba Registrar para gerar rejeições."),
      ),
    );
  },
};
