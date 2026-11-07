import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const required = [
  "frontend/index.html",
  "frontend/style.css",
  "frontend/app.js",
  "frontend/utils.js",
  "frontend/contract.js",
  "frontend/assets/logo.png",
  "frontend/assets/favicon.png",
];
const missing = required.filter((file) => !fs.existsSync(path.join(process.cwd(), file)));
if (missing.length) {
  console.error(`Arquivos obrigatórios ausentes: ${missing.join(", ")}`);
  process.exit(1);
}

const html = fs.readFileSync(path.join(process.cwd(), "frontend/index.html"), "utf8");
const checks = [
  [html.includes("web3@4.0.3"), "Web3.js 4.0.3 não está fixada no HTML"],
  [html.includes("sha384-/rnEp+xI/XCIM1gOUXDUCBSVKUx0Fc+WzvIsdbJYcEkMCcyzeKn5FJwNrwc314pV"), "Hash SRI do Web3.js ausente"],
  [html.includes('type="module" src="app.js"'), "app.js não está carregado como módulo"],
  [html.includes('name="viewport"'), "meta viewport ausente"],
  [html.includes("connect-button"), "botão de conexão ausente"],
];
const failures = checks.filter(([ok]) => !ok).map(([, message]) => message);
if (failures.length) {
  failures.forEach((message) => console.error(message));
  process.exit(1);
}
console.log("Frontend estático validado para publicação.");
