import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const source = path.join(root, "backend", "contracts", "EcoOrigem.sol");
const destination = path.join(root, "remix", "contracts", "EcoOrigem.sol");

if (!fs.existsSync(source)) {
  console.error("Contrato principal não encontrado em backend/contracts/EcoOrigem.sol.");
  process.exit(1);
}

fs.mkdirSync(path.dirname(destination), { recursive: true });
const contract = fs.readFileSync(source, "utf8");
fs.writeFileSync(destination, contract);

if (fs.readFileSync(destination, "utf8") !== contract) {
  console.error("A cópia do contrato para o Remix não ficou idêntica ao original.");
  process.exit(1);
}

console.log("Pasta remix preparada com uma cópia idêntica do contrato principal.");
