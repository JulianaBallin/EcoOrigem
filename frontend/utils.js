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

export function friendlyFallbackError(error) {
  const code = errorCode(error);
  const message = String(error?.message || "");
  if (code === 4001 || message.toLowerCase().includes("user rejected")) {
    return "A solicitação foi cancelada na MetaMask.";
  }
  if (message.toLowerCase().includes("insufficient funds")) {
    return "Saldo de SepoliaETH insuficiente para a taxa e o gas.";
  }
  if (message.toLowerCase().includes("contract pausado")) {
    return "O contrato está pausado pelo administrador.";
  }
  if (message.toLowerCase().includes("perfil ja esta")) {
    return "Esse perfil já está no estado solicitado.";
  }
  if (message.toLowerCase().includes("sem saldo para sacar")) {
    return "O contrato não possui taxas acumuladas para sacar.";
  }
  return "A operação não foi concluída. Confira os dados e tente novamente.";
}
