// Confere o SHA-256 de um arquivo com os documentos registrados no contrato.
import crypto from "node:crypto";
import fs from "node:fs";
import { color, connect, CONTRACT_ADDRESS, short } from "./lib-onchain.mjs";

const [file, lotArg] = process.argv.slice(2);
if (!file || !fs.existsSync(file)) {
  console.error(color.red("Uso: make hash ARQUIVO=caminho/do/arquivo [LOTE=1]"));
  process.exit(1);
}

const hash = `0x${crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex")}`;
console.log(color.cyan("▶ Verificação de integridade"));
console.log(`  Arquivo  : ${file}`);
console.log(`  SHA-256  : ${color.yellow(hash)}`);
console.log(`  Contrato : ${short(CONTRACT_ADDRESS)} (Sepolia)\n`);

const { contract } = connect();
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function retry(task, tries = 5) {
  for (let i = 1; ; i += 1) {
    try {
      return await task();
    } catch (error) {
      if (i >= tries) throw error;
      await pause(3000);
    }
  }
}
let lots;
try {
  const total = Number(await retry(() => contract.methods.totalLots().call()));
  lots = lotArg ? [Number(lotArg)] : Array.from({ length: total }, (_, i) => i + 1);
  let found = 0;
  for (const id of lots) {
    const documents = await retry(() => contract.methods.getDocuments(id).call());
    for (const doc of documents) {
      const contentHash = String(doc.contentHash ?? doc[0]).toLowerCase();
      if (contentHash !== hash) continue;
      found += 1;
      const when = new Date(Number(doc.timestamp ?? doc[4]) * 1000).toLocaleString("pt-BR");
      console.log(
        color.green(`✔ ÍNTEGRO`) +
          ` confere com “${doc.description ?? doc[2]}” no lote #${id}, por ${short(doc.author ?? doc[3])} em ${when}`,
      );
      const uri = doc.ipfsUri ?? doc[1];
      if (uri) console.log(color.dim(`  IPFS: ${uri}`));
    }
  }
  if (!found) {
    const onde = lotArg ? `no lote #${lotArg}` : `em nenhum dos ${lots.length} lotes`;
    console.log(color.red(`✖ NÃO CONFERE`) + ` este arquivo não corresponde a nenhum documento ${onde}.`);
    console.log(color.dim("  O arquivo foi alterado ou nunca foi registrado."));
    process.exit(2);
  }
} catch (error) {
  console.error(color.red(`Falha ao consultar a Sepolia: ${error.message}`));
  process.exit(1);
}
