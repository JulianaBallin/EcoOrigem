// Application bootstrap: routing, global status, wallet picker and banners.
import { api, ApiError, append, clear, closeDialog, h, setBusy, shortHash, toast } from "./lib.js";
import { activeWallet, onChange, refreshCore, setActiveWallet, state } from "./state.js";
import { blockchain } from "./views/blockchain.js";
import { consultar } from "./views/consultar.js";
import { laboratorio } from "./views/laboratorio.js";
import { painel } from "./views/painel.js";
import { permissoes } from "./views/permissoes.js";
import { registrar } from "./views/registrar.js";
import { rejeicoes } from "./views/rejeicoes.js";

const VIEWS = Object.fromEntries([painel, registrar, consultar, blockchain, permissoes, rejeicoes, laboratorio].map((v) => [v.id, v]));
const POLL_MS = 5000;
let current = { id: null, params: [] };
let signature = null;

function parseHash() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const id = VIEWS[parts[0]] ? parts[0] : "painel";
  return { id, params: VIEWS[parts[0]] ? parts.slice(1) : [] };
}

async function navigate() {
  current = parseHash();
  document.querySelectorAll(".view").forEach((section) => (section.hidden = section.dataset.view !== current.id));
  document.querySelectorAll("#tabs a").forEach((link) => {
    if (link.dataset.view === current.id) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  const view = VIEWS[current.id];
  const root = document.getElementById(`view-${current.id}`);
  signature = view.signature ? view.signature() : null;
  if (state.offline) {
    clear(root).append(h("div", { class: "card" }, h("div", { class: "empty" }, "Blockchain local indisponível. Inicie o nó com make node (ou docker compose up) e recarregue a página.")));
    return;
  }
  await view.render(root, current.params);
  if (!location.hash.includes("/") || current.params.length === 0) window.scrollTo({ top: 0 });
  else document.getElementById(`block-${current.params[0]}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderPill() {
  const pill = document.getElementById("chain-pill");
  const text = pill.querySelector(".chain-pill-text");
  const { status } = state;
  if (state.offline || !status) {
    pill.dataset.state = "offline";
    text.textContent = "Blockchain local indisponível";
  } else if (!status.integrity.valid) {
    pill.dataset.state = "invalid";
    text.textContent = `Cadeia adulterada no bloco ${status.integrity.first_invalid_block}`;
  } else {
    pill.dataset.state = "ok";
    text.textContent = `Blockchain local ativa · bloco #${status.height - 1} · dificuldade ${status.difficulty}`;
  }
}

function renderWallets() {
  const select = document.getElementById("wallet-select");
  if (select.options.length !== state.wallets.length) {
    clear(select).append(...state.wallets.map((w) => h("option", { value: w.label }, w.name)));
    select.onchange = () => setActiveWallet(select.value);
  }
  if (state.active) select.value = state.active;
  const detail = clear(document.getElementById("wallet-detail"));
  const wallet = activeWallet();
  if (!wallet) return;
  append(detail, [
    h("span", { class: "mono", title: wallet.address }, shortHash(wallet.address, 6, 4)),
    wallet.is_admin ? h("span", { class: "badge admin" }, "Administrador") : null,
    wallet.role_labels.map((label) => h("span", { class: "badge role" }, label)),
    !wallet.is_admin && !wallet.roles.length ? h("span", {}, "sem perfil") : null,
  ]);
}

function renderBanner() {
  const slot = clear(document.getElementById("banner"));
  if (state.offline || !state.status) return;
  if (!state.contract) {
    const button = h("button", { type: "button", class: "btn small", onclick: () => deploy(button) }, "Implantar contrato com o Administrador");
    slot.append(h("div", { class: "banner" }, h("div", { class: "banner-inner" }, h("span", {}, h("strong", {}, "O contrato ainda não foi implantado. "), "Use make deploy ou o botão ao lado para implantá-lo na blockchain local."), button)));
  } else if (!state.status.integrity.valid) {
    slot.append(h("div", { class: "banner bad" }, h("div", { class: "banner-inner" }, h("span", {}, h("strong", {}, "Integridade comprometida. "), "Novas operações estão bloqueadas. Veja a aba Integridade para restaurar."), h("a", { class: "btn small secondary", href: "#/laboratorio" }, "Abrir Integridade"))));
  }
}

async function deploy(button) {
  setBusy(button, true);
  try {
    const receipt = await api.post("deploy", { wallet: "administrador" });
    toast(`Contrato implantado no bloco #${receipt.block_index}. Conceda os perfis na aba Permissões.`);
    await refreshCore();
    navigate();
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    toast(error.message, true);
    setBusy(button, false);
  }
}

function renderChrome() {
  renderPill();
  renderWallets();
  renderBanner();
}

async function poll() {
  await refreshCore();
  const view = VIEWS[current.id];
  const next = view.signature ? view.signature() : null;
  if (view.signature && next !== signature) {
    signature = next;
    view.render(document.getElementById(`view-${current.id}`), current.params);
  }
}

document.getElementById("dialog-close").addEventListener("click", closeDialog);
document.getElementById("dialog").addEventListener("click", (event) => {
  if (event.target.id === "dialog") closeDialog();
});
window.addEventListener("hashchange", () => {
  closeDialog();
  navigate();
});
onChange(renderChrome);

await refreshCore();
renderChrome();
await navigate();
setInterval(poll, POLL_MS);
