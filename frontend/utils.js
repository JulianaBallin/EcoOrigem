export const ROLE = Object.freeze({
  NONE: 0,
  PRODUCER: 1,
  PROCESSOR: 2,
  CARRIER: 3,
  DISTRIBUTOR: 4,
});

export const ROLE_LABELS = Object.freeze([
  "Administrador",
  "Produtor",
  "Beneficiador",
  "Transportador",
  "Distribuidor",
]);

export const STATUS_LABELS = Object.freeze([
  "Cadastrado",
  "Beneficiado",
  "Em transporte",
  "Distribuído",
  "Finalizado",
]);

export function shortAddress(address, head = 6, tail = 4) {
  if (!address || address.length < head + tail) return address || "Não conectada";
  return `${address.slice(0, head)}…${address.slice(-tail)}`;
}

export function formatQuantity(quantityGrams) {
  const grams = Number(quantityGrams || 0);
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: grams % 1000 === 0 ? 0 : 3,
    maximumFractionDigits: 3,
  }).format(grams / 1000);
}

export function toQuantityGrams(quantityKg) {
  const value = Number(String(quantityKg).replace(",", "."));
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error("Informe uma quantidade maior que zero.");
  }
  const grams = Math.round(value * 1000);
  if (grams > 100_000_000) {
    throw new Error("A quantidade máxima é 100.000 kg.");
  }
  return String(grams);
}

export function dateToTimestamp(date) {
  if (!date) throw new Error("Informe a data da coleta.");
  const timestamp = Math.floor(new Date(`${date}T12:00:00Z`).getTime() / 1000);
  const now = Math.floor(Date.now() / 1000);
  if (!Number.isFinite(timestamp) || timestamp > now) {
    throw new Error("A data da coleta não pode estar no futuro.");
  }
  return String(timestamp);
}

export function formatTimestamp(timestamp) {
  if (!timestamp || Number(timestamp) === 0) return "-";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Manaus",
  }).format(new Date(Number(timestamp) * 1000));
}

export function normalizeLot(raw) {
  return {
    id: String(raw.id ?? raw[0]),
    product: raw.product ?? raw[1],
    origin: raw.origin ?? raw[2],
    quantityGrams: String(raw.quantityGrams ?? raw[3]),
    harvestedAt: String(raw.harvestedAt ?? raw[4]),
    producer: raw.producer ?? raw[5],
    custodian: raw.custodian ?? raw[6],
    processor: raw.processor ?? raw[7],
    carrier: raw.carrier ?? raw[8],
    distributor: raw.distributor ?? raw[9],
    status: Number(raw.status ?? raw[10]),
    temperature: Number(raw.transportTemperatureMilliC ?? raw[11]),
    createdAt: String(raw.createdAt ?? raw[12]),
    updatedAt: String(raw.updatedAt ?? raw[13]),
    active: Boolean(raw.active ?? raw[14]),
  };
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export async function sha256File(file) {
  if (!file) return `0x${"0".repeat(64)}`;
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return `0x${Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("")}`;
}

export function normalizeIpfsUri(value) {
  const uri = String(value || "").trim();
  if (!uri) return "";
  if (uri.startsWith("ipfs://") && uri.length >= 10) return uri;
  if (/^[a-zA-Z0-9]+$/.test(uri) && uri.length >= 10) return `ipfs://${uri}`;
  throw new Error("Informe um CID ou uma URI iniciada por ipfs://.");
}

export function ipfsGatewayUrl(uri) {
  if (!uri?.startsWith("ipfs://")) return "";
  return `https://ipfs.io/ipfs/${encodeURIComponent(uri.slice(7))}`;
}

export function errorCode(error) {
  return Number(error?.code ?? error?.cause?.code ?? error?.innerError?.code ?? 0);
}

// Textos dos require() do contrato, já em linguagem de usuário.
const REVERT_REASONS = [
  ["contrato pausado", "O contrato está pausado pelo administrador. Aguarde a retomada."],
  ["estado de pausa inalterado", "O contrato já está nesse estado de pausa."],
  ["perfil ja esta", "Essa carteira já está nesse estado para o perfil escolhido."],
  ["sem saldo para sacar", "O contrato não tem taxas acumuladas para sacar."],
  ["limite entre", "O tamanho da página deve ficar entre 1 e 50."],
];

export function revertReasonMessage(reason) {
  const text = String(reason || "").toLowerCase();
  const found = REVERT_REASONS.find(([key]) => text.includes(key));
  return found ? found[1] : "";
}

export function friendlyFallbackError(error) {
  const code = errorCode(error);
  const message = String(error?.message || "");
  const text = message.toLowerCase();
  if (code === 4001 || text.includes("user rejected") || text.includes("user denied")) {
    return "Você cancelou a operação na MetaMask. Nada foi enviado.";
  }
  if (code === -32002 || text.includes("already pending")) {
    return "Já existe uma solicitação aberta na MetaMask. Abra a extensão e responda a ela.";
  }
  if (text.includes("insufficient funds")) {
    return "Saldo de SepoliaETH insuficiente para a taxa e o gas. Peça mais na faucet.";
  }
  const reason = revertReasonMessage(text);
  if (reason) return reason;
  if (text.includes("invalid params input")) {
    return "A MetaMask recusou o formato da transação. Recarregue a página (Ctrl+Shift+R) e tente de novo.";
  }
  if (text.includes("transaction not found")) {
    return "A transação ainda não apareceu na rede. Aguarde alguns segundos e confira em Atividade na MetaMask antes de tentar de novo.";
  }
  if (text.includes("nonce")) {
    return "Há uma transação pendente nesta conta. Aguarde a confirmação ou cancele a pendente na MetaMask.";
  }
  if (text.includes("chain") || text.includes("network")) {
    return "A MetaMask não está na rede Sepolia. Troque de rede e tente de novo.";
  }
  if (text.includes("failed to fetch") || text.includes("timeout")) {
    return "Sem resposta da rede. Confira a internet e tente de novo.";
  }
  return "A operação não foi concluída. Confira os dados e tente de novo. Os detalhes técnicos estão no console do navegador (F12).";
}

// Quais perfis liberam cada seção e cada formulário (o contrato continua sendo
// quem decide de verdade; isto só evita o erro antes de gastar gas).
export const TAB_ROLES = Object.freeze({
  registrar: [ROLE.PRODUCER],
  operacoes: [ROLE.PROCESSOR, ROLE.CARRIER, ROLE.DISTRIBUTOR],
  documentos: [ROLE.PRODUCER, ROLE.PROCESSOR, ROLE.CARRIER, ROLE.DISTRIBUTOR],
});

export const FORM_ROLES = Object.freeze({
  "processing-form": [ROLE.PROCESSOR],
  "transport-form": [ROLE.CARRIER],
  "delivery-form": [ROLE.DISTRIBUTOR],
  "finalize-form": [ROLE.DISTRIBUTOR],
});

export function hasAnyRole(userRoles, needed) {
  return needed.some((role) => userRoles.includes(role));
}

export function lockMessage(needed, userRoles, connected) {
  if (!connected) return "Conecte a MetaMask para liberar esta área.";
  const required = needed.map((role) => ROLE_LABELS[role]).join(" ou ");
  const mine = userRoles.length
    ? userRoles.map((role) => ROLE_LABELS[role]).join(", ")
    : "sem perfil operacional";
  return `Área do perfil ${required}. Sua carteira está como: ${mine}. Troque de conta na MetaMask.`;
}

const sameWallet = (a, b) => Boolean(a && b && String(a).toLowerCase() === String(b).toLowerCase());

// Lotes que a carteira pode mexer em cada etapa (alimenta as listas de seleção).
export function lotsForStep(lots, step, account) {
  const rules = {
    processing: (lot) => lot.status === 0 && sameWallet(lot.processor, account),
    transport: (lot) => lot.status === 1 && sameWallet(lot.carrier, account),
    delivery: (lot) => lot.status === 2 && sameWallet(lot.distributor, account),
    finalize: (lot) => lot.status === 3 && sameWallet(lot.distributor, account),
    document: (lot) => lot.status < 4 && sameWallet(lot.custodian, account),
  };
  return lots.filter(rules[step] || (() => false));
}

// Monta quem tem cada perfil a partir dos eventos RoleUpdated, em ordem.
export function roleHoldersFromEvents(events) {
  const holders = { 1: new Map(), 2: new Map(), 3: new Map(), 4: new Map() };
  for (const event of events) {
    const { account, role, enabled } = event.returnValues || {};
    const key = Number(role);
    if (!holders[key]) continue;
    const address = String(account);
    if (enabled === true || enabled === "true") holders[key].set(address.toLowerCase(), address);
    else holders[key].delete(address.toLowerCase());
  }
  return Object.fromEntries(
    Object.entries(holders).map(([role, map]) => [role, [...map.values()]]),
  );
}

// Remove acentos e caixa para comparar o que a pessoa digita com a lista.
export function normalizeText(text) {
  return String(text ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

// Filtra a lista enquanto se digita: primeiro quem começa com o texto, depois quem contém.
export function filterOptions(options, query, limit = 50) {
  const q = normalizeText(query);
  if (!q) return options.slice(0, limit);
  const starts = [];
  const contains = [];
  for (const option of options) {
    const text = normalizeText(option);
    if (text.startsWith(q)) starts.push(option);
    else if (text.includes(q)) contains.push(option);
    if (starts.length >= limit) break;
  }
  return [...starts, ...contains].slice(0, limit);
}
