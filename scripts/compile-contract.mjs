import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import solc from "solc";

const root = process.cwd();
const sourcePath = path.join(root, "contracts", "EcoOrigem.sol");
const outputDirectory = path.join(root, "build");
const sourceName = "contracts/EcoOrigem.sol";

const input = {
  language: "Solidity",
  sources: {
    [sourceName]: { content: fs.readFileSync(sourcePath, "utf8") },
  },
  settings: {
    optimizer: { enabled: true, runs: 200 },
    evmVersion: "paris",
    outputSelection: {
      "*": {
        "*": ["abi", "evm.bytecode.object", "evm.deployedBytecode.object"],
      },
    },
  },
};

const output = JSON.parse(solc.compile(JSON.stringify(input)));
const diagnostics = output.errors || [];
for (const item of diagnostics) {
  const stream = item.severity === "error" ? process.stderr : process.stdout;
  stream.write(`${item.formattedMessage}\n`);
}

if (diagnostics.some((item) => item.severity === "error")) {
  process.exit(1);
}

const contract = output.contracts[sourceName].EcoOrigem;
const artifact = {
  contractName: "EcoOrigem",
  compiler: solc.version(),
  optimizer: { enabled: true, runs: 200 },
  evmVersion: "paris",
  abi: contract.abi,
  bytecode: `0x${contract.evm.bytecode.object}`,
  deployedBytecode: `0x${contract.evm.deployedBytecode.object}`,
};

fs.mkdirSync(outputDirectory, { recursive: true });
fs.writeFileSync(
  path.join(outputDirectory, "EcoOrigem.json"),
  `${JSON.stringify(artifact, null, 2)}\n`,
);

const byteLength = contract.evm.deployedBytecode.object.length / 2;
console.log(`Contrato compilado com ${solc.version()} (${byteLength} bytes implantados).`);
