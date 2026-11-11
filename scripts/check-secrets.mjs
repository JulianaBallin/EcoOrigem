import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

const result = spawnSync(
  "git",
  ["ls-files", "--cached", "--others", "--exclude-standard", "-z"],
  { encoding: "utf8", maxBuffer: 10 * 1024 * 1024 },
);

if (result.status !== 0) {
  console.error("Não foi possível listar os arquivos para a verificação de segredos.");
  process.exit(1);
}

const textExtensions = new Set([
  "", ".css", ".env", ".example", ".html", ".js", ".json", ".md",
  ".mjs", ".py", ".sh", ".sol", ".toml", ".txt", ".yaml", ".yml",
]);
const ignored = new Set([
  "scripts/check-secrets.mjs",
  "docs/relatorio/relatorio-desenvolvimento-ecoorigem.docx",
  "docs/relatorio/relatorio-desenvolvimento-ecoorigem.pdf",
  "docs/slides/apresentacao-ecoorigem.pdf",
  "docs/slides/apresentacao-ecoorigem.pptx",
  "docs/slides/template-entrega-1.pptx",
]);
const findings = [];
const rules = [
  ["chave privada em formato PEM", /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/],
  ["chave privada hexadecimal", /(?:PRIVATE_KEY|SECRET_KEY)\s*[:=]\s*["']?0x[a-fA-F0-9]{64}\b/i],
  ["token GitHub", /\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b/],
  ["chave AWS", /\bAKIA[0-9A-Z]{16}\b/],
  ["token Slack", /\bxox[baprs]-[A-Za-z0-9-]{20,}\b/],
  ["frase de recuperação", /(?:mnemonic|seed phrase|frase de recupera[cç][aã]o)\s*[:=]\s*["'][^"'\n]{20,}["']/i],
];

for (const file of result.stdout.split("\0").filter(Boolean)) {
  if (ignored.has(file) || file.startsWith("node_modules/") || file.startsWith("build/")) continue;
  const extension = path.extname(file).toLowerCase();
  if (!textExtensions.has(extension) && path.basename(file) !== "Makefile") continue;
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) continue;

  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/);
  lines.forEach((line, index) => {
    for (const [label, expression] of rules) {
      if (expression.test(line)) findings.push(`${file}:${index + 1}: ${label}`);
    }

    const assignment = line.match(/\b(password|passwd|token|api[_-]?key|secret)\b\s*[:=]\s*["']?([^\s"'#},]+)/i);
    if (!assignment) return;
    const value = assignment[2];
    const safe = /^(?:\$\{|PENDENTE|EXEMPLO|PLACEHOLDER|CHANGE_ME|SEU_|SUA_|<)/i.test(value) || value === "";
    if (!safe) findings.push(`${file}:${index + 1}: credencial literal em configuração`);
  });
}

if (findings.length) {
  console.error("Possíveis credenciais encontradas. Os valores não são exibidos:");
  findings.forEach((finding) => console.error(`- ${finding}`));
  process.exit(1);
}

console.log("Nenhuma credencial ou chave privada conhecida foi encontrada nos arquivos publicáveis.");
