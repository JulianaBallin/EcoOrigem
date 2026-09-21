// Application state shared by all views.
import { api, h, shortHash } from "./lib.js";

export const state = {
  wallets: [],
  active: null, // label of the wallet used to sign transactions
  status: null,
  contract: null, // description of the deployed contract or null
  offline: false,
};

const listeners = new Set();
export function onChange(fn) {
  listeners.add(fn);
}
function emit() {
  listeners.forEach((fn) => fn());
}

const STORAGE_KEY = "ecoorigem.wallet";
function readStoredWallet() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setActiveWallet(label) {
  state.active = label;
  try {
    localStorage.setItem(STORAGE_KEY, label);
  } catch {
    /* storage unavailable */
  }
  emit();
}

export const activeWallet = () => state.wallets.find((w) => w.label === state.active) || null;
export const walletByAddress = (address) => state.wallets.find((w) => w.address === address) || null;

/** Human friendly name of an address, falling back to the shortened address. */
export function nameOf(address) {
  if (!address) return "-";
  const wallet = walletByAddress(address);
  return wallet ? wallet.name : shortHash(address, 6, 4);
}

export function addressLabel(address) {
  const wallet = walletByAddress(address);
  return h(
    "span",
    { title: address },
    wallet ? h("strong", {}, wallet.name) : null,
    wallet ? " " : null,
    h("span", { class: "mono" }, shortHash(address, 6, 4)),
  );
}

export function hasRole(wallet, role) {
  return Boolean(wallet && wallet.roles.includes(role));
}

/** Reload status, contract and wallets. Never throws: failures mark the node offline. */
export async function refreshCore() {
  try {
    const [status, contract, wallets] = await Promise.all([
      api.get("status"),
      api.get("contract"),
      api.get("wallets"),
    ]);
    state.status = status;
    state.contract = contract.deployed ? contract.contract : null;
    state.wallets = wallets.wallets;
    state.offline = false;
    const stored = readStoredWallet();
    if (!state.active || !state.wallets.some((w) => w.label === state.active)) {
      const preferred = state.wallets.some((w) => w.label === stored) ? stored : "produtor";
      state.active = state.wallets.some((w) => w.label === preferred) ? preferred : state.wallets[0]?.label;
    }
  } catch {
    state.offline = true;
  }
  emit();
}
