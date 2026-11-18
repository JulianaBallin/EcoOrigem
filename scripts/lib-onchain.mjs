// Conexão de leitura com o contrato na Sepolia e cores para o terminal.
import { Web3 } from "web3";
import { CONTRACT_ABI, CONTRACT_ADDRESS, DEPLOYMENT_BLOCK } from "../frontend/contrato.js";

// Tenderly primeiro: o nó publicnode às vezes apaga o histórico antigo de eventos.
export const RPC = process.env.SEPOLIA_RPC || "https://sepolia.gateway.tenderly.co";
export const ETHERSCAN = "https://sepolia.etherscan.io";
export { CONTRACT_ADDRESS, DEPLOYMENT_BLOCK };

const useColor = !process.env.NO_COLOR && (process.stdout.isTTY || process.env.FORCE_COLOR);
const paint = (code) => (text) => (useColor ? `\x1b[${code}m${text}\x1b[0m` : String(text));
export const color = {
  green: paint("1;32"),
  red: paint("1;31"),
  yellow: paint("1;33"),
  cyan: paint("1;36"),
  magenta: paint("1;35"),
  blue: paint("1;34"),
  dim: paint("2"),
  bold: paint("1"),
};

export const STATUS = ["Cadastrado", "Beneficiado", "Em transporte", "Distribuído", "Finalizado"];
export const ROLES = ["Nenhum", "Produtor", "Beneficiador", "Transportador", "Distribuidor"];
export const short = (address) => `${String(address).slice(0, 6)}…${String(address).slice(-4)}`;

export function connect() {
  if (!/^0x[0-9a-fA-F]{40}$/.test(CONTRACT_ADDRESS)) {
    console.error(color.red("Contrato não configurado em frontend/contrato.js (rode make configure)."));
    process.exit(1);
  }
  const web3 = new Web3(RPC);
  return { web3, contract: new web3.eth.Contract(CONTRACT_ABI, CONTRACT_ADDRESS) };
}
