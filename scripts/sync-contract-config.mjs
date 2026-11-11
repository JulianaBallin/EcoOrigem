import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const configPath = path.join(root, "frontend", "contrato.js");
const artifact = JSON.parse(
  fs.readFileSync(path.join(root, "build", "EcoOrigem.json"), "utf8"),
);
const current = fs.readFileSync(configPath, "utf8");

function currentValue(name, fallback) {
  const pattern = new RegExp(`export const ${name} = ([^;]+);`);
  return current.match(pattern)?.[1] ?? fallback;
}

const address = currentValue("CONTRACT_ADDRESS", '""');
const block = currentValue("DEPLOYMENT_BLOCK", "0");
const transaction = currentValue("DEPLOYMENT_TX", '""');
const contents = `// Gerado a partir de backend/contracts/EcoOrigem.sol por \`npm run sync:abi\`.
// Preencha os dados de implantação depois do deploy na Sepolia.
export const CONTRACT_ADDRESS = ${address};
export const DEPLOYMENT_BLOCK = ${block};
export const DEPLOYMENT_TX = ${transaction};

export const CONTRACT_ABI = ${JSON.stringify(artifact.abi, null, 2)};
`;

fs.writeFileSync(configPath, contents);
console.log(`ABI sincronizada em ${path.relative(root, configPath)}.`);
