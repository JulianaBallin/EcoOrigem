import assert from "node:assert/strict";
import test from "node:test";
import {
  dateToTimestamp,
  formatQuantity,
  normalizeIpfsUri,
  normalizeLot,
  shortAddress,
  toQuantityGrams,
} from "../frontend/utils.js";

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
