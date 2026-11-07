import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const [address, blockValue, transaction] = process.argv.slice(2);
if (!/^0x[0-9a-fA-F]{40}$/.test(address || "")) {
  console.error("Uso: npm run configure:contract -- 0xENDERECO BLOCO 0xHASH_DEPLOY");
  process.exit(1);
}
const block = Number(blockValue);
if (!Number.isSafeInteger(block) || block <= 0) {
  console.error("O bloco de implantação deve ser um inteiro positivo.");
  process.exit(1);
}
if (!/^0x[0-9a-fA-F]{64}$/.test(transaction || "")) {
  console.error("O hash da transação deve ter 32 bytes em hexadecimal.");
  process.exit(1);
}

const configPath = path.join(process.cwd(), "frontend", "contract.js");
let contents = fs.readFileSync(configPath, "utf8");
contents = contents
  .replace(/export const CONTRACT_ADDRESS = [^;]+;/, `export const CONTRACT_ADDRESS = "${address}";`)
  .replace(/export const DEPLOYMENT_BLOCK = [^;]+;/, `export const DEPLOYMENT_BLOCK = ${block};`)
  .replace(/export const DEPLOYMENT_TX = [^;]+;/, `export const DEPLOYMENT_TX = "${transaction}";`);
fs.writeFileSync(configPath, contents);
console.log("Dados da implantação registrados em frontend/contract.js.");
