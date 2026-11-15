import assert from "node:assert/strict";
import test from "node:test";
import { MUNICIPIOS_AM, PRODUTOS } from "../amazonas.js";
import { COMUNIDADES_AM } from "../comunidades.js";
import { MUNICIPIOS_BR } from "../brasil.js";
import fs from "node:fs";
import {
  dateToTimestamp,
  formatQuantity,
  filterOptions,
  friendlyFallbackError,
  normalizeText,
  hasAnyRole,
  lockMessage,
  lotsForStep,
  roleHoldersFromEvents,
  normalizeIpfsUri,
  normalizeLot,
  shortAddress,
  toQuantityGrams,
} from "../utils.js";

test("formata e converte quantidades sem usar ponto flutuante no contrato", () => {
  assert.equal(toQuantityGrams("250.125"), "250125");
  assert.equal(formatQuantity("250125"), "250,125");
  assert.throws(() => toQuantityGrams("0"));
  assert.throws(() => toQuantityGrams("100001"));
});

test("normaliza identificadores e URIs exibidos no frontend", () => {
  assert.equal(shortAddress("0x1234567890abcdef", 6, 4), "0x1234…cdef");
  assert.equal(normalizeIpfsUri("Qm1234567890"), "ipfs://Qm1234567890");
  assert.equal(normalizeIpfsUri(""), "");
  assert.throws(() => normalizeIpfsUri("https://exemplo.invalid/arquivo"));
});

test("normaliza a tupla de lote devolvida pelo Web3", () => {
  const raw = [
    7n,
    "Açaí",
    "Manacapuru",
    250000n,
    1700000000n,
    "0x1",
    "0x2",
    "0x3",
    "0x4",
    "0x5",
    2n,
    24000n,
    1700000100n,
    1700000200n,
    true,
  ];
  const lot = normalizeLot(raw);
  assert.equal(lot.id, "7");
  assert.equal(lot.status, 2);
  assert.equal(lot.temperature, 24000);
  assert.equal(lot.active, true);
});

test("rejeita data de coleta futura", () => {
  assert.throws(() => dateToTimestamp("2999-01-01"));
  assert.match(dateToTimestamp("2024-01-01"), /^\d+$/);
});

test("traduz erros da carteira e do contrato em mensagens com orientação", () => {
  assert.match(friendlyFallbackError({ code: 4001, message: "User rejected" }), /cancelou/);
  assert.match(friendlyFallbackError(new Error("insufficient funds for gas")), /faucet/);
  assert.match(friendlyFallbackError(new Error("Contrato pausado")), /pausado/);
  assert.match(friendlyFallbackError(new Error("Invalid params input - Expected never")), /Ctrl\+Shift\+R/);
  assert.match(friendlyFallbackError(new Error("Transaction not found")), /Atividade/);
});

test("listas do Amazonas: 62 municípios e produtos sem repetição", () => {
  assert.equal(MUNICIPIOS_AM.length, 62);
  assert.equal(new Set(MUNICIPIOS_AM).size, 62);
  assert.equal(new Set(PRODUTOS).size, PRODUTOS.length);
  assert.ok(PRODUTOS.every((nome) => nome.length >= 2 && nome.length <= 60));
});

test("bloqueio por perfil e mensagem de orientação", () => {
  assert.equal(hasAnyRole([2], [1]), false);
  assert.equal(hasAnyRole([2, 3], [3, 4]), true);
  assert.match(lockMessage([1], [2], true), /Produtor.*Beneficiador/);
  assert.match(lockMessage([1], [], false), /Conecte a MetaMask/);
});

test("cada etapa lista só os lotes da carteira naquela etapa", () => {
  const eu = "0xAAA";
  const lots = [
    { id: "1", status: 0, processor: "0xaaa", carrier: "", distributor: "", custodian: "0xP" },
    { id: "2", status: 0, processor: "0xBBB", carrier: "", distributor: "", custodian: "0xP" },
    { id: "3", status: 1, processor: "0xBBB", carrier: eu, distributor: "", custodian: eu },
    { id: "4", status: 3, processor: "", carrier: "", distributor: eu, custodian: eu },
  ];
  assert.deepEqual(lotsForStep(lots, "processing", eu).map((l) => l.id), ["1"]);
  assert.deepEqual(lotsForStep(lots, "transport", eu).map((l) => l.id), ["3"]);
  assert.deepEqual(lotsForStep(lots, "finalize", eu).map((l) => l.id), ["4"]);
  assert.deepEqual(lotsForStep(lots, "document", eu).map((l) => l.id), ["3", "4"]);
});

test("carteiras por perfil a partir dos eventos RoleUpdated", () => {
  const ev = (account, role, enabled) => ({ returnValues: { account, role, enabled } });
  const holders = roleHoldersFromEvents([
    ev("0xAb", 1n, true), ev("0xCd", "2", true), ev("0xAb", 1n, false), ev("0xEf", 2, true),
  ]);
  assert.deepEqual(holders[1], []);
  assert.deepEqual(holders[2], ["0xCd", "0xEf"]);
});

test("toda comunidade pertence a um dos 62 municípios e cabe no contrato", () => {
  assert.deepEqual(Object.keys(COMUNIDADES_AM).sort(), [...MUNICIPIOS_AM].sort());
  const nomes = Object.values(COMUNIDADES_AM).flat();
  assert.ok(nomes.length > 3000);
  // origem final = "comunidade, município - AM" precisa ter até 120 caracteres
  assert.ok(nomes.every((n) => n.length <= 60));
});

test("filtro do destino ignora acento e caixa e diminui conforme se digita", () => {
  const lista = ["Manaus - AM", "Manacapuru - AM", "Maués - AM", "Mauá - SP", "Parintins - AM"];
  assert.equal(normalizeText("  Maués "), "maues");
  assert.deepEqual(filterOptions(lista, "mana"), ["Manaus - AM", "Manacapuru - AM"]);
  assert.deepEqual(filterOptions(lista, "maues"), ["Maués - AM"]);
  assert.deepEqual(filterOptions(lista, "sp"), ["Mauá - SP"]);
  assert.equal(filterOptions(lista, "").length, 5);
  assert.equal(filterOptions(lista, "zzz").length, 0);
});

test("municípios do Brasil e arquivos de comunidades por UF", () => {
  const ufs = Object.keys(MUNICIPIOS_BR);
  assert.equal(ufs.length, 27);
  assert.equal(Object.values(MUNICIPIOS_BR).flat().length, 5571);
  for (const uf of ufs) {
    const arquivo = new URL(`../dados/comunidades/${uf}.json`, import.meta.url);
    const dados = JSON.parse(fs.readFileSync(arquivo, "utf8"));
    assert.ok(Object.keys(dados).every((m) => MUNICIPIOS_BR[uf].includes(m)), uf);
    const origem = Object.values(dados).flat();
    // destino final "comunidade, município - UF" precisa caber em 120 caracteres
    assert.ok(origem.every((n) => n.length <= 60), uf);
  }
});
