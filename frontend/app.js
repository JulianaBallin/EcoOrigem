import {
  CONTRACT_ABI,
  CONTRACT_ADDRESS,
  DEPLOYMENT_BLOCK,
} from "./contrato.js";
import {
  ROLE,
  ROLE_LABELS,
  STATUS_LABELS,
  dateToTimestamp,
  escapeHtml,
  formatQuantity,
  formatTimestamp,
  friendlyFallbackError,
  ipfsGatewayUrl,
  normalizeIpfsUri,
  normalizeLot,
  sha256File,
  shortAddress,
  toQuantityGrams,
} from "./utils.js";

const SEPOLIA_CHAIN_ID = "0xaa36a7";
const ETHERSCAN = "https://sepolia.etherscan.io";
const ZERO_HASH = `0x${"0".repeat(64)}`;
const PAGE_LIMIT = 50;

const state = {
  web3: null,
  contract: null,
  account: "",
  owner: "",
  chainId: "",
  authenticated: false,
  paused: false,
  feeWei: "0",
  lots: [],
};

const byId = (id) => document.getElementById(id);
const all = (selector) => [...document.querySelectorAll(selector)];

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  bindNavigation();
  bindActions();
  setMaximumHarvestDate();

  if (!window.ethereum || !window.Web3) {
    showBanner(
      "Instale ou habilite a MetaMask para usar a dApp. As consultas também dependem do provedor da carteira.",
      "error",
    );
    byId("connect-button").disabled = true;
    return;
  }

  state.web3 = new window.Web3(window.ethereum);
  state.web3.eth.handleRevert = true;
  state.chainId = await window.ethereum.request({ method: "eth_chainId" });
  configureContract();
  registerProviderEvents();

  const accounts = await window.ethereum.request({ method: "eth_accounts" });
  if (accounts.length) {
    state.account = state.web3.utils.toChecksumAddress(accounts[0]);
  }
  await refreshSession();
}

function configureContract() {
  const configured =
    CONTRACT_ABI.length > 0 &&
    state.web3.utils.isAddress(CONTRACT_ADDRESS) &&
    !/^0x0{40}$/i.test(CONTRACT_ADDRESS);

  if (!configured) {
    showBanner(
      "Contrato ainda não configurado. Faça o deploy na Sepolia e execute npm run configure:contract -- <endereço> <bloco> <hash>.",
      "warning",
    );
    return;
  }
  state.contract = new state.web3.eth.Contract(CONTRACT_ABI, CONTRACT_ADDRESS);
  byId("contract-link").href = `${ETHERSCAN}/address/${CONTRACT_ADDRESS}`;
  byId("contract-link").textContent = shortAddress(CONTRACT_ADDRESS);
}

function registerProviderEvents() {
  window.ethereum.on("accountsChanged", async (accounts) => {
    state.account = accounts[0]
      ? state.web3.utils.toChecksumAddress(accounts[0])
      : "";
    state.authenticated = false;
    showToast(
      state.account
        ? "A conta mudou. Autentique a nova carteira para enviar transações."
        : "A MetaMask foi desconectada.",
    );
    await refreshSession();
  });

  window.ethereum.on("chainChanged", async (chainId) => {
    state.chainId = chainId;
    state.authenticated = false;
    showToast("A rede mudou. Os dados da dApp foram atualizados.");
    await refreshSession();
  });
}

function bindNavigation() {
  all("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => openPanel(button.dataset.tab));
  });
  all("[data-go]").forEach((button) => {
    button.addEventListener("click", () => {
      openPanel(button.dataset.go);
      document.querySelector(".section-tabs").scrollIntoView({ block: "start" });
    });
  });
}

function openPanel(id) {
  all(".tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === id);
  });
  all(".panel").forEach((panel) => {
    const active = panel.id === id;
    panel.hidden = !active;
    panel.classList.toggle("active", active);
  });
}

function bindActions() {
  byId("connect-button").addEventListener("click", () => connectWallet(true));
  byId("authenticate-button").addEventListener("click", authenticateWallet);
  byId("network-button").addEventListener("click", switchToSepolia);
  all(".refresh-button").forEach((button) =>
    button.addEventListener("click", refreshContractData),
  );
  byId("events-refresh").addEventListener("click", loadEvents);
  byId("lot-search").addEventListener("input", renderLots);
  byId("register-form").addEventListener("submit", submitRegisterLot);
  byId("processing-form").addEventListener("submit", submitProcessing);
  byId("transport-form").addEventListener("submit", submitTransport);
  byId("delivery-form").addEventListener("submit", submitDelivery);
  byId("finalize-form").addEventListener("submit", submitFinalize);
  byId("document-form").addEventListener("submit", submitDocument);
  byId("role-form").addEventListener("submit", submitRoleUpdate);
  byId("pause-button").addEventListener("click", togglePause);
  byId("withdraw-button").addEventListener("click", withdrawFees);
  all("[data-close-dialog]").forEach((button) =>
    button.addEventListener("click", () => byId("transaction-dialog").close()),
  );
}

async function connectWallet(authenticate) {
  try {
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });
    state.account = state.web3.utils.toChecksumAddress(accounts[0]);
    state.chainId = await window.ethereum.request({ method: "eth_chainId" });
    if (state.chainId !== SEPOLIA_CHAIN_ID) await switchToSepolia();
    await refreshSession();
    if (authenticate) await authenticateWallet();
  } catch (error) {
    showToast(friendlyFallbackError(error), "error");
  }
}

async function authenticateWallet() {
  try {
    if (!state.account) {
      await connectWallet(false);
    }
    if (!state.account) return;

    const nonce = crypto.getRandomValues(new Uint32Array(4)).join("-");
    const message = [
      "EcoOrigem - autenticacao de perfil",
      `Origem: ${window.location.origin}`,
      `Carteira: ${state.account}`,
      `Nonce: ${nonce}`,
      "Esta assinatura nao envia transacao nem consome gas.",
    ].join("\n");
    const signature = await window.ethereum.request({
      method: "personal_sign",
      params: [message, state.account],
    });
    const recovered = state.web3.eth.accounts.recover(message, signature);
    if (recovered.toLowerCase() !== state.account.toLowerCase()) {
      throw new Error("A assinatura não corresponde à carteira conectada.");
    }

    state.authenticated = true;
    renderAuthentication();
    showToast("Carteira autenticada. Nenhuma assinatura foi armazenada.");
  } catch (error) {
    state.authenticated = false;
    renderAuthentication();
    showToast(friendlyFallbackError(error), "error");
  }
}

async function switchToSepolia() {
  if (!window.ethereum) return;
  try {
    await window.ethereum.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: SEPOLIA_CHAIN_ID }],
    });
  } catch (error) {
    if (Number(error.code) !== 4902) {
      showToast(friendlyFallbackError(error), "error");
      return;
    }
    try {
      await window.ethereum.request({
        method: "wallet_addEthereumChain",
        params: [
          {
            chainId: SEPOLIA_CHAIN_ID,
            chainName: "Ethereum Sepolia",
            nativeCurrency: { name: "Sepolia Ether", symbol: "ETH", decimals: 18 },
            rpcUrls: ["https://rpc.sepolia.org"],
            blockExplorerUrls: [ETHERSCAN],
          },
        ],
      });
    } catch (addError) {
      showToast(friendlyFallbackError(addError), "error");
    }
  }
}

async function refreshSession() {
  renderConnection();
  renderAuthentication();
  if (!state.account || state.chainId !== SEPOLIA_CHAIN_ID || !state.contract) {
    clearContractState();
    return;
  }

  try {
    const balance = await state.web3.eth.getBalance(state.account);
    byId("balance-value").textContent = `${formatEth(balance)} ETH`;
    await refreshContractData();
  } catch (error) {
    showToast("Não foi possível consultar a Sepolia. Tente novamente.", "error");
  }
}

async function refreshContractData() {
  if (!state.contract || state.chainId !== SEPOLIA_CHAIN_ID) return;
  setBusyRefresh(true);
  try {
    const [owner, paused, fee, total, contractBalance] = await Promise.all([
      state.contract.methods.owner().call(),
      state.contract.methods.paused().call(),
      state.contract.methods.REGISTRATION_FEE().call(),
      state.contract.methods.totalLots().call(),
      state.web3.eth.getBalance(CONTRACT_ADDRESS),
    ]);
    state.owner = state.web3.utils.toChecksumAddress(owner);
    state.paused = Boolean(paused);
    state.feeWei = String(fee);

    byId("total-lots").textContent = String(total);
    byId("pause-state").textContent = state.paused ? "Pausado" : "Ativo";
    byId("registration-fee").textContent = formatEth(fee);
    byId("contract-balance").textContent = formatEth(contractBalance);
    byId("form-fee").textContent = `${formatEth(fee)} SepoliaETH`;

    await Promise.all([loadRoles(), loadLots()]);
    renderAdminState();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  } finally {
    setBusyRefresh(false);
  }
}

async function loadRoles() {
  if (!state.account) return;
  const values = await Promise.all(
    [ROLE.PRODUCER, ROLE.PROCESSOR, ROLE.CARRIER, ROLE.DISTRIBUTOR].map((role) =>
      state.contract.methods.hasRole(state.account, role).call(),
    ),
  );
  const roles = values
    .map((enabled, index) => (enabled ? ROLE_LABELS[index + 1] : null))
    .filter(Boolean);
  if (sameAddress(state.account, state.owner)) roles.unshift("Administrador");
  byId("roles-value").textContent = roles.join(" · ") || "Sem perfil operacional";
}

async function loadLots() {
  state.lots = (await state.contract.methods.getLots(0, PAGE_LIMIT).call()).map(
    normalizeLot,
  );
  renderLots();
}

function renderLots() {
  const query = byId("lot-search").value.trim().toLowerCase();
  const lots = state.lots.filter((lot) =>
    [lot.id, lot.product, lot.origin, lot.producer, lot.custodian]
      .join(" ")
      .toLowerCase()
      .includes(query),
  );
  byId("lots-count").textContent = `${lots.length} resultado${lots.length === 1 ? "" : "s"}`;
  const body = byId("lots-body");
  if (!lots.length) {
    body.innerHTML = `<tr><td colspan="7" class="empty-state">${
      state.contract ? "Nenhum lote encontrado." : "Configure e conecte o contrato."
    }</td></tr>`;
    return;
  }
  body.innerHTML = lots
    .map(
      (lot) => `
        <tr>
          <td class="mono">#${escapeHtml(lot.id)}</td>
          <td><strong>${escapeHtml(lot.product)}</strong></td>
          <td>${escapeHtml(lot.origin)}</td>
          <td>${formatQuantity(lot.quantityGrams)} kg</td>
          <td><span class="status-badge status-${lot.status}">${STATUS_LABELS[lot.status]}</span></td>
          <td>${formatTimestamp(lot.updatedAt)}</td>
          <td><button type="button" class="table-link" data-lot-id="${lot.id}">Detalhes</button></td>
        </tr>`,
    )
    .join("");
  all("[data-lot-id]").forEach((button) =>
    button.addEventListener("click", () => showLotDetail(button.dataset.lotId)),
  );
}

async function showLotDetail(lotId) {
  const detail = byId("lot-detail");
  detail.hidden = false;
  detail.innerHTML = '<p class="empty-state">Carregando o histórico do lote...</p>';
  detail.scrollIntoView({ behavior: "smooth", block: "nearest" });
  try {
    const [rawLot, documents, history] = await Promise.all([
      state.contract.methods.getLot(lotId).call(),
      state.contract.methods.getDocuments(lotId).call(),
      state.contract.methods.getHistory(lotId).call(),
    ]);
    const lot = normalizeLot(rawLot);
    detail.innerHTML = `
      <div class="card-heading">
        <div><span class="eyebrow">LOTE #${lot.id}</span><h3>${escapeHtml(lot.product)} · ${escapeHtml(lot.origin)}</h3></div>
        <span class="status-badge status-${lot.status}">${STATUS_LABELS[lot.status]}</span>
      </div>
      <div class="detail-grid">
        ${detailItem("Quantidade", `${formatQuantity(lot.quantityGrams)} kg`)}
        ${detailItem("Coleta", formatTimestamp(lot.harvestedAt))}
        ${detailItem("Temperatura", lot.status >= 2 ? `${lot.temperature / 1000} °C` : "-")}
        ${detailItem("Produtor", shortAddress(lot.producer))}
        ${detailItem("Custodiante", shortAddress(lot.custodian))}
        ${detailItem("Beneficiador", shortAddress(lot.processor))}
        ${detailItem("Transportador", shortAddress(lot.carrier))}
        ${detailItem("Distribuidor", shortAddress(lot.distributor))}
        ${detailItem("Atualização", formatTimestamp(lot.updatedAt))}
      </div>
      <div class="overview-grid">
        <div><h3>Histórico</h3><div class="history-list">${renderHistory(history)}</div></div>
        <div><h3>Documentos</h3><div class="document-list">${renderDocuments(documents)}</div></div>
      </div>`;
  } catch (error) {
    detail.innerHTML = `<p class="empty-state">${escapeHtml(decodeContractError(error))}</p>`;
  }
}

function detailItem(label, value) {
  return `<div class="detail-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function renderHistory(history) {
  if (!history.length) return '<p class="empty-state">Sem histórico.</p>';
  return history
    .map((entry) => {
      const status = Number(entry.status ?? entry[0]);
      const actor = entry.actor ?? entry[1];
      const timestamp = entry.timestamp ?? entry[2];
      const note = entry.note ?? entry[3];
      return `<article class="history-item"><span class="history-marker">${status + 1}</span><div><strong>${STATUS_LABELS[status]}</strong><small>${escapeHtml(note || "Sem observação")} · ${shortAddress(actor)}</small></div><span class="item-time">${formatTimestamp(timestamp)}</span></article>`;
    })
    .join("");
}

function renderDocuments(documents) {
  if (!documents.length) return '<p class="empty-state">Nenhum documento.</p>';
  return documents
    .map((document) => {
      const hash = document.contentHash ?? document[0];
      const uri = document.ipfsUri ?? document[1];
      const description = document.description ?? document[2];
      const author = document.author ?? document[3];
      const timestamp = document.timestamp ?? document[4];
      const gateway = ipfsGatewayUrl(uri);
      return `<article class="document-item"><span class="history-marker">#</span><div><strong>${escapeHtml(description)}</strong><small class="mono">${escapeHtml(hash)}</small><small>${shortAddress(author)}${gateway ? ` · <a href="${gateway}" target="_blank" rel="noreferrer">Abrir IPFS</a>` : ""}</small></div><span class="item-time">${formatTimestamp(timestamp)}</span></article>`;
    })
    .join("");
}

async function loadEvents() {
  if (!state.contract) return;
  const list = byId("events-list");
  list.innerHTML = '<p class="empty-state">Consultando os logs da Sepolia...</p>';
  try {
    const latest = Number(await state.web3.eth.getBlockNumber());
    const configuredStart = Number(DEPLOYMENT_BLOCK || 0);
    const fromBlock = Math.max(configuredStart, latest - 49_999, 0);
    const events = await state.contract.getPastEvents("allEvents", {
      fromBlock,
      toBlock: "latest",
    });
    if (!events.length) {
      list.innerHTML = '<p class="empty-state">Nenhum evento encontrado no intervalo consultado.</p>';
      return;
    }
    list.innerHTML = events
      .slice(-100)
      .reverse()
      .map((event) => renderEvent(event))
      .join("");
  } catch (error) {
    list.innerHTML = `<p class="empty-state">${escapeHtml(decodeContractError(error))}</p>`;
  }
}

function renderEvent(event) {
  const values = event.returnValues || {};
  const important = Object.entries(values)
    .filter(([key]) => Number.isNaN(Number(key)) && key !== "__length__")
    .slice(0, 4)
    .map(([key, value]) => `${key}: ${formatEventValue(value)}`)
    .join(" · ");
  return `<article class="event-item"><span class="history-marker">E</span><div><strong>${escapeHtml(event.event || "Evento")}</strong><small>${escapeHtml(important)}</small><small>Bloco ${event.blockNumber}</small></div><a class="item-time" href="${ETHERSCAN}/tx/${event.transactionHash}" target="_blank" rel="noreferrer">Etherscan</a></article>`;
}

function formatEventValue(value) {
  const text = String(value);
  if (/^0x[0-9a-f]{40}$/i.test(text)) return shortAddress(text);
  if (/^0x[0-9a-f]{64}$/i.test(text)) return `${text.slice(0, 10)}…`;
  return text.length > 55 ? `${text.slice(0, 52)}…` : text;
}

async function submitRegisterLot(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    await requireWriteAccess();
    const method = state.contract.methods.registerLot(
      data.get("product"),
      data.get("origin").trim(),
      toQuantityGrams(data.get("quantity")),
      dateToTimestamp(data.get("harvestDate")),
      validateAddress(data.get("processor"), "beneficiador"),
    );
    await sendTransaction("Cadastro do lote", method, { value: state.feeWei });
    event.currentTarget.reset();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function submitProcessing(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    await requireWriteAccess();
    const file = data.get("document");
    const hash = file?.size ? await sha256File(file) : ZERO_HASH;
    const method = state.contract.methods.recordProcessing(
      data.get("lotId"),
      data.get("description").trim(),
      validateAddress(data.get("carrier"), "transportador"),
      hash,
      normalizeIpfsUri(data.get("ipfsUri")),
    );
    await sendTransaction("Beneficiamento do lote", method);
    event.currentTarget.reset();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function submitTransport(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    await requireWriteAccess();
    const temperature = Math.round(Number(data.get("temperature")) * 1000);
    const method = state.contract.methods.startTransport(
      data.get("lotId"),
      validateAddress(data.get("distributor"), "distribuidor"),
      data.get("destination").trim(),
      String(temperature),
    );
    await sendTransaction("Início do transporte", method);
    event.currentTarget.reset();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function submitDelivery(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    await requireWriteAccess();
    await sendTransaction(
      "Confirmação de recebimento",
      state.contract.methods.confirmDelivery(
        data.get("lotId"),
        data.get("note").trim(),
      ),
    );
    event.currentTarget.reset();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function submitFinalize(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    await requireWriteAccess();
    await sendTransaction(
      "Finalização do lote",
      state.contract.methods.finalizeLot(
        data.get("lotId"),
        data.get("note").trim(),
      ),
    );
    event.currentTarget.reset();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function submitDocument(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    await requireWriteAccess();
    const hash = await sha256File(data.get("document"));
    await sendTransaction(
      "Registro de documento",
      state.contract.methods.attachDocument(
        data.get("lotId"),
        hash,
        normalizeIpfsUri(data.get("ipfsUri")),
        data.get("description").trim(),
      ),
    );
    event.currentTarget.reset();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function submitRoleUpdate(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    await requireWriteAccess();
    const account = validateAddress(data.get("account"), "carteira");
    const role = data.get("role");
    const grant = event.submitter?.value !== "revoke";
    const method = grant
      ? state.contract.methods.grantRole(account, role)
      : state.contract.methods.revokeRole(account, role);
    await sendTransaction(grant ? "Concessão de perfil" : "Revogação de perfil", method);
    event.currentTarget.reset();
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function togglePause() {
  try {
    await requireWriteAccess();
    await sendTransaction(
      state.paused ? "Retomada do contrato" : "Pausa do contrato",
      state.contract.methods.setPaused(!state.paused),
    );
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function withdrawFees() {
  try {
    await requireWriteAccess();
    await sendTransaction("Saque das taxas", state.contract.methods.withdrawFees());
  } catch (error) {
    showToast(decodeContractError(error), "error");
  }
}

async function requireWriteAccess() {
  if (!state.account) {
    await connectWallet(false);
  }
  if (!state.account) throw new Error("Conecte a MetaMask.");
  if (state.chainId !== SEPOLIA_CHAIN_ID) {
    await switchToSepolia();
    state.chainId = await window.ethereum.request({ method: "eth_chainId" });
  }
  if (state.chainId !== SEPOLIA_CHAIN_ID) {
    throw new Error("Selecione a rede Ethereum Sepolia.");
  }
  if (!state.contract) throw new Error("O contrato ainda não foi configurado.");
  if (!state.authenticated) {
    await authenticateWallet();
  }
  if (!state.authenticated) throw new Error("Autentique a carteira antes de continuar.");
}

async function sendTransaction(title, method, options = {}) {
  const dialog = byId("transaction-dialog");
  byId("transaction-title").textContent = title;
  setTransactionState(
    "pending",
    "Aguardando confirmação",
    "Revise os dados e confirme a transação na MetaMask.",
  );
  if (!dialog.open) dialog.showModal();

  try {
    const transaction = method.send({ from: state.account, ...options });
    transaction.on("transactionHash", (hash) => {
      setTransactionState(
        "pending",
        "Transação enviada",
        "Aguardando inclusão em um bloco da Sepolia.",
        hash,
      );
    });
    const receipt = await transaction;
    const hash = receipt.transactionHash;
    setTransactionState(
      "success",
      "Transação confirmada",
      `Incluída no bloco ${receipt.blockNumber}.`,
      hash,
    );
    showToast("Transação confirmada na Sepolia.");
    await refreshContractData();
    return receipt;
  } catch (error) {
    const message = decodeContractError(error);
    setTransactionState("error", "Transação não concluída", message);
    throw error;
  }
}

function setTransactionState(type, title, detail, hash = "") {
  const icon = type === "pending" ? '<span class="tx-spinner"></span>' : `<span class="event-check">${type === "success" ? "✓" : "!"}</span>`;
  byId("transaction-body").innerHTML = `
    <div class="transaction-state ${type}">${icon}<div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(detail)}</p></div></div>
    ${hash ? `<a class="tx-hash" href="${ETHERSCAN}/tx/${hash}" target="_blank" rel="noreferrer">${escapeHtml(hash)}</a>` : ""}`;
}

function decodeContractError(error) {
  const data = findKnownRevertData(error);
  if (data) {
    const fragment = errorFragmentForData(data);
    if (fragment) {
      try {
        const values = state.web3.eth.abi.decodeParameters(
          fragment.inputs,
          `0x${data.slice(10)}`,
        );
        return customErrorMessage(fragment.name, values);
      } catch {
        // A mensagem genérica abaixo continua compreensível.
      }
    }
  }
  const direct = String(error?.message || "");
  if (direct && !direct.toLowerCase().includes("execution reverted")) {
    const friendly = friendlyFallbackError(error);
    if (friendly.startsWith("A operação")) return direct;
  }
  return friendlyFallbackError(error);
}

function findKnownRevertData(value, depth = 0) {
  if (depth > 6 || value == null) return "";
  if (typeof value === "string" && /^0x[0-9a-f]{8,}$/i.test(value)) {
    return errorFragmentForData(value) || value.startsWith("0x08c379a0") ? value : "";
  }
  if (typeof value !== "object") return "";
  for (const key of ["data", "result", "return", "originalError", "cause", "innerError"]) {
    const found = findKnownRevertData(value[key], depth + 1);
    if (found) return found;
  }
  for (const nested of Object.values(value)) {
    const found = findKnownRevertData(nested, depth + 1);
    if (found) return found;
  }
  return "";
}

function errorFragmentForData(data) {
  if (!state.web3 || !data) return null;
  const selector = data.slice(0, 10).toLowerCase();
  return (
    CONTRACT_ABI.filter((item) => item.type === "error").find((fragment) => {
      const signature = `${fragment.name}(${fragment.inputs.map((input) => input.type).join(",")})`;
      return state.web3.eth.abi.encodeFunctionSignature(signature).toLowerCase() === selector;
    }) || null
  );
}

function customErrorMessage(name, values) {
  const role = Number(values.requiredRole ?? values[1]);
  const messages = {
    Unauthorized: `A carteira ${shortAddress(values.account ?? values[0])} não possui o perfil ${ROLE_LABELS[role] || "necessário"}.`,
    InvalidStatus: `O lote #${values.lotId ?? values[0]} está em “${STATUS_LABELS[Number(values.current ?? values[1])]}” e a operação exige “${STATUS_LABELS[Number(values.expected ?? values[2])]}”.`,
    LotNotFound: `O lote #${values.lotId ?? values[0]} não existe.`,
    InvalidData: `O campo “${values.field ?? values[0]}” contém um valor inválido.`,
    WrongFee: `A taxa enviada é diferente da taxa de cadastro definida pelo contrato.`,
    DesignatedActorOnly: `Esta etapa pertence à carteira designada ${shortAddress(values.expected ?? values[1])}.`,
    DuplicateDocument: "Esse documento já está registrado no lote.",
    FinalizedLot: `O lote #${values.lotId ?? values[0]} está finalizado e não aceita alterações.`,
    TransferFailed: "A transferência para a tesouraria falhou.",
  };
  return messages[name] || "O contrato recusou a operação.";
}

function validateAddress(value, label) {
  const address = String(value || "").trim();
  if (!state.web3.utils.isAddress(address)) {
    throw new Error(`Informe um endereço válido para ${label}.`);
  }
  return state.web3.utils.toChecksumAddress(address);
}

function renderConnection() {
  const connected = Boolean(state.account);
  const rightNetwork = state.chainId === SEPOLIA_CHAIN_ID;
  const networkButton = byId("network-button");
  networkButton.dataset.state = connected ? (rightNetwork ? "online" : "wrong") : "offline";
  byId("network-label").textContent = connected
    ? rightNetwork
      ? "Ethereum Sepolia"
      : "Trocar para Sepolia"
    : "MetaMask desconectada";
  byId("connect-button").textContent = connected
    ? shortAddress(state.account)
    : "Conectar e autenticar";
  byId("account-value").textContent = connected ? shortAddress(state.account) : "Não conectada";
  if (!connected) {
    byId("balance-value").textContent = "-";
    byId("roles-value").textContent = "Conecte a MetaMask";
  }
}

function renderAuthentication() {
  const proof = byId("auth-proof");
  proof.dataset.state = state.authenticated ? "online" : "offline";
  byId("auth-title").textContent = state.authenticated
    ? "Carteira autenticada"
    : "Sessão não autenticada";
  byId("auth-detail").textContent = state.authenticated
    ? `${shortAddress(state.account)} assinou o desafio desta sessão.`
    : "Conecte a carteira para assinar o desafio.";
  byId("authenticate-button").textContent = state.authenticated
    ? "Autenticação confirmada"
    : "Autenticar carteira";
  byId("authenticate-button").disabled = state.authenticated;
}

function renderAdminState() {
  const isOwner = sameAddress(state.account, state.owner);
  all(".admin-tab").forEach((tab) => {
    tab.hidden = !isOwner;
  });
  if (!isOwner && !byId("administracao").hidden) openPanel("visao-geral");
  byId("pause-button").textContent = state.paused
    ? "Retomar contrato"
    : "Pausar contrato";
}

function clearContractState() {
  byId("total-lots").textContent = "0";
  byId("pause-state").textContent = "-";
  byId("registration-fee").textContent = "-";
  byId("contract-balance").textContent = "-";
  state.lots = [];
  renderLots();
  renderAdminState();
}

function setBusyRefresh(busy) {
  all(".refresh-button").forEach((button) => {
    button.disabled = busy;
    button.textContent = busy ? "Atualizando..." : "Atualizar dados";
  });
}

function setMaximumHarvestDate() {
  const today = new Date();
  const local = new Date(today.getTime() - today.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 10);
  document.querySelector('[name="harvestDate"]').max = local;
}

function showBanner(message, type = "warning") {
  const banner = byId("system-banner");
  banner.hidden = false;
  banner.className = `system-banner ${type}`;
  banner.textContent = message;
}

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  byId("toasts").append(toast);
  window.setTimeout(() => toast.remove(), 5200);
}

function formatEth(value) {
  if (!state.web3) return "0";
  const eth = Number(state.web3.utils.fromWei(String(value), "ether"));
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 6,
  }).format(eth);
}

function sameAddress(left, right) {
  return Boolean(left && right && left.toLowerCase() === right.toLowerCase());
}
