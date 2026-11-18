// Acompanha os eventos do contrato: histórico recente e novos eventos em tempo real.
import { color, connect, CONTRACT_ADDRESS, DEPLOYMENT_BLOCK, ETHERSCAN, ROLES, short, STATUS } from "./lib-onchain.mjs";

const onlyNew = process.argv.includes("--novos");
const { web3, contract } = connect();
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Rede instável não derruba o acompanhamento: tenta de novo algumas vezes.
async function retry(task, tries = 5) {
  for (let i = 1; ; i += 1) {
    try {
      return await task();
    } catch (error) {
      if (i >= tries) throw error;
      console.log(color.yellow(`(sem resposta da rede, tentativa ${i}/${tries}...)`));
      await pause(3000);
    }
  }
}

function describe(event) {
  const v = event.returnValues;
  switch (event.event) {
    case "RoleUpdated":
      return [color.magenta, `${ROLES[Number(v.role)]} ${v.enabled ? "concedido a" : "retirado de"} ${short(v.account)}`];
    case "LotRegistered":
      return [color.green, `Lote #${v.lotId}: ${v.product} por ${short(v.producer)} (beneficiador ${short(v.processor)})`];
    case "LotStatusChanged":
      return [color.cyan, `Lote #${v.lotId} → ${STATUS[Number(v.status)]} por ${short(v.actor)}${v.note ? ` — “${v.note}”` : ""}`];
    case "DocumentAttached":
      return [color.yellow, `Lote #${v.lotId}: documento ${String(v.contentHash).slice(0, 14)}… por ${short(v.author)}${v.ipfsUri ? ` ${v.ipfsUri}` : ""}`];
    case "PauseChanged":
      return [color.red, `Contrato ${v.paused ? "PAUSADO" : "retomado"} por ${short(v.actor)}`];
    case "FeesWithdrawn":
      return [color.blue, `${web3.utils.fromWei(String(v.amount), "ether")} ETH enviados para ${short(v.treasury)}`];
    default:
      return [color.dim, event.event];
  }
}

function show(event) {
  const [paint, text] = describe(event);
  const name = String(event.event).padEnd(17);
  console.log(`${color.dim(`[bloco ${event.blockNumber}]`)} ${paint(name)} ${text}`);
  console.log(color.dim(`             ${ETHERSCAN}/tx/${event.transactionHash}`));
}

console.log(color.cyan("▶ Acompanhando o contrato EcoOrigem na Sepolia"));
console.log(`  Contrato: ${CONTRACT_ADDRESS}\n  Aperte Ctrl+C para sair.\n`);

try {
  let latest = Number(await retry(() => web3.eth.getBlockNumber()));
  if (!onlyNew) {
    const start = Math.max(Number(DEPLOYMENT_BLOCK || 0), 0);
    const history = [];
    for (let from = start; from <= latest; from += 10_000) {
      const to = Math.min(from + 9_999, latest);
      history.push(...(await retry(() => contract.getPastEvents("allEvents", { fromBlock: from, toBlock: to }))));
    }
    console.log(color.dim(`Histórico recente (${history.length} eventos, mostrando os últimos 40):`));
    history.slice(-40).forEach(show);
    console.log(color.dim("\nAguardando novos eventos...\n"));
  }
  let next = latest + 1;
  for (;;) {
    await pause(6000);
    try {
      latest = Number(await web3.eth.getBlockNumber());
      if (latest < next) continue;
      const events = await contract.getPastEvents("allEvents", { fromBlock: next, toBlock: latest });
      events.forEach(show);
      next = latest + 1;
    } catch (error) {
      console.log(color.yellow(`(consulta falhou, tentando de novo: ${error.message})`));
    }
  }
} catch (error) {
  console.error(color.red(`Falha ao consultar a Sepolia: ${error.message}`));
  process.exit(1);
}
