import fs from "node:fs";
import { spawnSync } from "node:child_process";
import process from "node:process";

const packageJson = JSON.parse(fs.readFileSync("package.json", "utf8"));
const packageLock = JSON.parse(fs.readFileSync("package-lock.json", "utf8"));
const productionDependencies = Object.keys(packageJson.dependencies || {});
if (productionDependencies.length) {
  console.error(
    `Dependências npm de produção inesperadas: ${productionDependencies.join(", ")}`,
  );
  process.exit(1);
}

const audit = spawnSync("npm", ["audit", "--json"], {
  encoding: "utf8",
  maxBuffer: 20 * 1024 * 1024,
});
let report;
try {
  report = JSON.parse(audit.stdout);
} catch {
  process.stderr.write(audit.stderr || audit.stdout);
  console.error("Não foi possível consultar ou interpretar a auditoria do npm.");
  process.exit(1);
}

const vulnerabilities = Object.entries(report.vulnerabilities || {});
const packages = packageLock.packages || {};
const developmentRoots = Object.entries(packages)
  .filter(([, metadata]) => metadata.dev === true)
  .map(([location]) => location);

function isDevelopmentNode(location) {
  if (packages[location]?.dev === true) return true;
  return developmentRoots.some((root) =>
    location.startsWith(`${root}/node_modules/`),
  );
}

const unexpected = vulnerabilities.filter(([, finding]) => {
  const nodes = finding.nodes || [];
  return nodes.length === 0 || nodes.some((node) => !isDevelopmentNode(node));
});

if (unexpected.length) {
  console.error("A auditoria encontrou alertas fora das ferramentas locais:");
  unexpected.forEach(([name, finding]) =>
    console.error(`- ${name}: ${finding.severity}`),
  );
  process.exit(1);
}

const totals = report.metadata?.vulnerabilities || {};
const count =
  totals.total ??
  Object.entries(totals)
    .filter(([key]) => key !== "total")
    .reduce(
      (sum, [, value]) => sum + (typeof value === "number" ? value : 0),
      0,
    );
console.log("A publicação não possui dependências npm de produção.");
if (vulnerabilities.length) {
  console.log(
    `${count} alertas permanecem isolados nas ferramentas locais de compilação e teste, que não são publicadas na Vercel.`,
  );
} else {
  console.log("A auditoria do npm não encontrou alertas.");
}
