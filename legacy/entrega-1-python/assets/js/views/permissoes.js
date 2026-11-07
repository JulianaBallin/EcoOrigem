// Permissions: wallets, roles and the administrator operations.
import { api, ApiError, clear, copyButton, h, icon, setBusy, toast } from "../lib.js";
import { activeWallet, refreshCore, state } from "../state.js";

const ROLES = [
  ["PRODUCER", "Produtor"],
  ["PROCESSOR", "Beneficiador"],
  ["CARRIER", "Transportador"],
  ["DISTRIBUTOR", "Distribuidor"],
];

function walletTable() {
  return h(
    "div",
    { class: "table-wrap" },
    h(
      "table",
      {},
      h("thead", {}, h("tr", {}, ["Carteira", "Endereço", "Perfis", "Nonce"].map((t) => h("th", { scope: "col" }, t)))),
      h(
        "tbody",
        {},
        state.wallets.map((w) =>
          h(
            "tr",
            {},
            h("td", {}, h("strong", {}, w.name), h("div", { class: "hint" }, w.description)),
            h("td", {}, h("span", { class: "hash" }, w.address), copyButton(w.address)),
            h("td", {}, h("div", { class: "pill-list" }, w.is_admin ? h("span", { class: "badge admin" }, "Administrador") : null, w.role_labels.map((r) => h("span", { class: "badge role" }, r)), !w.is_admin && !w.roles.length ? h("span", { class: "hint" }, "sem perfil") : null)),
            h("td", {}, String(w.nonce)),
          ),
        ),
      ),
    ),
  );
}

function adminForm(root) {
  const account = h("select", { id: "perm-account" }, state.wallets.map((w) => h("option", { value: w.address }, w.name)));
  const role = h("select", { id: "perm-role" }, ROLES.map(([value, label]) => h("option", { value }, label)));
  const outcome = h("div", {});
  const run = async (method, button) => {
    setBusy(button, true);
    clear(outcome);
    try {
      const receipt = await api.post("send", { wallet: state.active, method, args: { account: account.value, role: role.value } });
      outcome.append(h("div", { class: "notice ok" }, h("strong", {}, "Confirmado no bloco "), `#${receipt.block_index}.`));
      await refreshCore();
      root.render(root.node);
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      outcome.append(h("div", { class: "notice bad" }, h("strong", {}, `${error.code}: `), error.message, h("div", { class: "hint" }, "Nenhum bloco foi criado.")));
      toast("Operação rejeitada.", true);
      await refreshCore();
    } finally {
      setBusy(button, false);
    }
  };
  const grant = h("button", { type: "button", class: "btn", onclick: () => run("grant_role", grant) }, icon("check", 16), "Conceder perfil");
  const revoke = h("button", { type: "button", class: "btn danger", onclick: () => run("revoke_role", revoke) }, icon("x", 16), "Revogar perfil");
  const wallet = activeWallet();
  return h(
    "div",
    { class: "card stack" },
    h("h2", {}, "Gerenciar perfis"),
    h("p", { class: "hint" }, "Somente o administrador do contrato concede ou revoga perfis. Selecione a carteira Administrador no topo para ter sucesso, ou outra carteira para ver a rejeição."),
    wallet && !wallet.is_admin ? h("div", { class: "notice warn" }, `A carteira ativa (${wallet.name}) não é a administradora. O contrato rejeitará a operação.`) : null,
    h("div", { class: "form-grid" }, h("label", { class: "field" }, "Conta", account), h("label", { class: "field" }, "Perfil", role)),
    h("div", { class: "row" }, grant, revoke),
    outcome,
  );
}

export const permissoes = {
  id: "permissoes",
  render(root) {
    const view = { node: root, render: (node) => permissoes.render(node) };
    clear(root).append(
      h("div", { class: "view-head" }, h("div", {}, h("h1", {}, "Permissões"), h("p", {}, "O contrato controla quem pode executar cada operação. Perfis são gravados na blockchain."))),
      h("div", { class: "grid split" }, adminForm(view), h("div", { class: "card stack" }, h("h2", {}, "Carteiras de demonstração"), walletTable())),
    );
  },
};
