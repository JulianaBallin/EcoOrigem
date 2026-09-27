// Shared helpers: safe DOM builder, API client, formatting, icons, toasts and dialog.

/** Create an element. Children may be nodes, strings or arrays; strings become text nodes. */
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === false || value === null || value === undefined) continue;
    if (key === "class") el.className = value;
    else if (key === "dataset") Object.assign(el.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2), value);
    else if (key in el && key !== "list" && key !== "form") el[key] = value;
    else el.setAttribute(key, value === true ? "" : value);
  }
  append(el, children);
  return el;
}

export function append(el, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

export function clear(el) {
  el.replaceChildren();
  return el;
}

/** Build an inline SVG icon from a static definition (never from user data). */
const ICONS = {
  check: '<path d="M5 12.5l4.5 4.5L19 7.5" stroke-width="2.4"/>',
  x: '<path d="M6 6l12 12M18 6L6 18" stroke-width="2.4"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 012-2h9"/>',
  cube: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12L4 7.5M12 12v9"/>',
  shield: '<path d="M12 3l8 3v6c0 4.5-3.2 7.9-8 9-4.8-1.1-8-4.5-8-9V6l8-3z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
  alert: '<path d="M12 4l9 16H3L12 4z"/><path d="M12 10v4M12 17.2v.1"/>',
  link: '<path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"/>',
  refresh: '<path d="M20 11a8 8 0 10-2.3 6"/><path d="M20 5v6h-6"/>',
  pickaxe: '<path d="M14 6l4 4"/><path d="M4 20l9-9"/><path d="M9 4c4-1 9 1 11 5-4-1-7 0-9 2"/>',
};
export function icon(name, size = 16) {
  const span = document.createElement("span");
  span.style.display = "inline-flex";
  span.setAttribute("aria-hidden", "true");
  span.innerHTML =
    `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" ` +
    `stroke-linecap="round" stroke-linejoin="round" stroke-width="2">${ICONS[name] || ""}</svg>`;
  return span;
}

// ---------------------------------------------------------------- API
export class ApiError extends Error {
  constructor(status, error) {
    super(error?.message || "Falha na comunicação com o servidor.");
    this.status = status;
    this.code = error?.code || "ERROR";
    this.layer = error?.layer || "node";
    this.details = error?.details || {};
  }
}

async function request(method, path, body) {
  let response;
  try {
    response = await fetch(`/api/${path}`, {
      method,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, { code: "NETWORK", message: "Não foi possível contatar a aplicação." });
  }
  let data = null;
  try {
    data = await response.json();
  } catch {
    /* empty body */
  }
  if (!response.ok) throw new ApiError(response.status, data?.error);
  return data;
}

export const api = {
  get: (path, params) => {
    const query = params ? `?${new URLSearchParams(params)}` : "";
    return request("GET", path + query);
  },
  post: (path, body = {}) => request("POST", path, body),
};

// ---------------------------------------------------------- formatting
export const STATUS_ORDER = ["REGISTERED", "PROCESSED", "IN_TRANSIT", "DISTRIBUTED", "FINALIZED"];
export const STATUS_LABEL = {
  REGISTERED: "CADASTRADO",
  PROCESSED: "BENEFICIADO",
  IN_TRANSIT: "EM_TRANSPORTE",
  DISTRIBUTED: "DISTRIBUIDO",
  FINALIZED: "FINALIZADO",
};
export const EVENT_LABEL = {
  CONTRACT_DEPLOYED: "Contrato implantado",
  ROLE_GRANTED: "Perfil concedido",
  ROLE_REVOKED: "Perfil revogado",
  LOT_REGISTERED: "Lote cadastrado",
  LOT_PROCESSED: "Beneficiamento registrado",
  TRANSPORT_STARTED: "Transporte iniciado",
  DELIVERY_CONFIRMED: "Recebimento confirmado",
  LOT_FINALIZED: "Lote finalizado",
  DOCUMENT_ATTACHED: "Documento anexado",
};
export const LAYER_LABEL = { contract: "Contrato", transaction: "Transação", node: "Nó", wallet: "Carteira", client: "Aplicação" };

export function formatDateTime(ms) {
  if (!ms) return "-";
  return new Date(ms).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "medium" });
}

export function formatKg(value) {
  return `${Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 3 })} kg`;
}

export function shortHash(value, head = 8, tail = 6) {
  if (!value) return "-";
  return value.length <= head + tail + 1 ? value : `${value.slice(0, head)}…${value.slice(-tail)}`;
}

/** Render a hash highlighting the leading zeros required by the proof of work. */
export function powHash(value) {
  const zeros = value.match(/^0*/)[0];
  return h("span", { class: "hash" }, zeros ? h("span", { class: "pow" }, zeros) : null, value.slice(zeros.length));
}

export function statusBadge(status) {
  return h("span", { class: `badge ${status}` }, STATUS_LABEL[status] || status);
}

export function copyButton(text, label = "Copiar") {
  return h(
    "button",
    {
      type: "button",
      class: "copy",
      title: label,
      "aria-label": label,
      onclick: async () => {
        try {
          await navigator.clipboard.writeText(text);
          toast("Copiado para a área de transferência.");
        } catch {
          toast("Não foi possível copiar.", true);
        }
      },
    },
    icon("copy", 14),
  );
}

export async function sha256File(file) {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

// ------------------------------------------------------- toasts, dialog
export function toast(message, bad = false) {
  const el = h("div", { class: `toast${bad ? " bad" : ""}`, role: "status" }, message);
  document.getElementById("toasts").append(el);
  setTimeout(() => el.remove(), 4500);
}

export function openDialog(title, content) {
  const dialog = document.getElementById("dialog");
  document.getElementById("dialog-title").textContent = title;
  const body = clear(document.getElementById("dialog-body"));
  append(body, [content]);
  if (!dialog.open) dialog.showModal();
}

export function closeDialog() {
  const dialog = document.getElementById("dialog");
  if (dialog.open) dialog.close();
}

export function setBusy(button, busy, label) {
  button.disabled = busy;
  if (label) button.dataset.label = button.dataset.label || button.textContent;
  if (label) button.textContent = busy ? label : button.dataset.label;
}
