import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import ganache from "ganache";
import { Web3 } from "web3";

const artifact = JSON.parse(
  fs.readFileSync(path.join(process.cwd(), "build", "EcoOrigem.json"), "utf8"),
);

async function expectRevert(promise) {
  await assert.rejects(promise, (error) => {
    assert.ok(error, "a operação deveria retornar um erro");
    return true;
  });
}

test("executa o fluxo completo, permissões, exceções, eventos e taxas", async () => {
  const provider = ganache.provider({
    logging: { quiet: true },
    wallet: { totalAccounts: 8, defaultBalance: 100 },
    chain: { hardfork: "shanghai" },
  });
  const web3 = new Web3(provider);
  const [owner, producer, processor, carrier, distributor, outsider] =
    await web3.eth.getAccounts();

  const contract = await new web3.eth.Contract(artifact.abi)
    .deploy({ data: artifact.bytecode })
    .send({ from: owner, gas: "9000000" });

  assert.equal((await contract.methods.owner().call()).toLowerCase(), owner.toLowerCase());
  assert.equal(await contract.methods.totalLots().call(), 0n);
  assert.equal(await contract.methods.statusLabel(2).call(), "Em transporte");

  for (const [account, role] of [
    [producer, 1],
    [processor, 2],
    [carrier, 3],
    [distributor, 4],
  ]) {
    const receipt = await contract.methods
      .grantRole(account, role)
      .send({ from: owner, gas: "150000" });
    assert.ok(receipt.events.RoleUpdated);
    assert.equal(await contract.methods.hasRole(account, role).call(), true);
  }
  await expectRevert(
    contract.methods.grantRole(producer, 1).send({ from: owner, gas: "150000" }),
  );
  await expectRevert(
    contract.methods.grantRole(outsider, 1).send({ from: outsider, gas: "150000" }),
  );

  const fee = await contract.methods.REGISTRATION_FEE().call();
  const harvest = Math.floor(Date.now() / 1000) - 86_400;
  await expectRevert(
    contract.methods
      .registerLot(
        "Açaí",
        "Comunidade do Catalão, Amazonas",
        250000,
        harvest,
        processor,
      )
      .send({ from: producer, value: 0, gas: "900000" }),
  );

  const registered = await contract.methods
    .registerLot(
      "Açaí",
      "Comunidade do Catalão, Amazonas",
      250000,
      harvest,
      processor,
    )
    .send({ from: producer, value: fee, gas: "900000" });
  assert.ok(registered.events.LotRegistered);
  assert.equal(await contract.methods.totalLots().call(), 1n);
  assert.equal(await web3.eth.getBalance(contract.options.address), fee);

  let lot = await contract.methods.getLot(1).call();
  assert.equal(lot.product, "Açaí");
  assert.equal(lot.status, 0n);
  assert.equal(lot.processor.toLowerCase(), processor.toLowerCase());
  assert.equal((await contract.methods.getDocuments(1).call()).length, 0);

  await expectRevert(
    contract.methods
      .recordProcessing(1, "Polpa selecionada", carrier, `0x${"22".repeat(32)}`, "")
      .send({ from: outsider, gas: "700000" }),
  );
  await expectRevert(
    contract.methods
      .recordProcessing(1, "Polpa selecionada", carrier, `0x${"22".repeat(32)}`, "")
      .send({ from: producer, gas: "700000" }),
  );

  await contract.methods
    .recordProcessing(
      1,
      "Polpa selecionada e refrigerada",
      carrier,
      `0x${"22".repeat(32)}`,
      "ipfs://QmLaudoBeneficiamento",
    )
    .send({ from: processor, gas: "700000" });
  lot = await contract.methods.getLot(1).call();
  assert.equal(lot.status, 1n);
  assert.equal(lot.custodian.toLowerCase(), processor.toLowerCase());

  const extraHash = `0x${"33".repeat(32)}`;
  await contract.methods
    .attachDocument(1, extraHash, "", "Certificado de qualidade")
    .send({ from: processor, gas: "450000" });
  await expectRevert(
    contract.methods
      .attachDocument(1, extraHash, "", "Documento repetido")
      .send({ from: processor, gas: "450000" }),
  );
  await expectRevert(
    contract.methods
      .attachDocument(1, `0x${"44".repeat(32)}`, "", "Documento sem custódia")
      .send({ from: outsider, gas: "450000" }),
  );

  await expectRevert(
    contract.methods
      .startTransport(1, distributor, "Manaus, Amazonas", 70000)
      .send({ from: carrier, gas: "500000" }),
  );
  await contract.methods
    .startTransport(1, distributor, "Manaus, Amazonas", 24000)
    .send({ from: carrier, gas: "500000" });
  lot = await contract.methods.getLot(1).call();
  assert.equal(lot.status, 2n);
  assert.equal(lot.transportTemperatureMilliC, 24000n);

  await expectRevert(
    contract.methods
      .confirmDelivery(1, "Tentativa de outra carteira")
      .send({ from: outsider, gas: "400000" }),
  );
  await contract.methods
    .confirmDelivery(1, "Recebimento conferido")
    .send({ from: distributor, gas: "400000" });
  await contract.methods
    .finalizeLot(1, "Lote disponibilizado ao consumidor")
    .send({ from: distributor, gas: "400000" });

  lot = await contract.methods.getLot(1).call();
  assert.equal(lot.status, 4n);
  assert.equal((await contract.methods.getHistory(1).call()).length, 5);
  assert.equal((await contract.methods.getDocuments(1).call()).length, 2);
  assert.equal((await contract.methods.getLots(0, 50).call()).length, 1);
  assert.equal((await contract.methods.getLots(99, 50).call()).length, 0);
  await expectRevert(contract.methods.getLots(0, 0).call());
  await expectRevert(
    contract.methods
      .attachDocument(1, `0x${"55".repeat(32)}`, "", "Após finalizar")
      .send({ from: distributor, gas: "450000" }),
  );

  await contract.methods.setPaused(true).send({ from: owner, gas: "120000" });
  assert.equal(await contract.methods.paused().call(), true);
  await expectRevert(
    contract.methods
      .registerLot("Cupuaçu", "Presidente Figueiredo", 50000, harvest, processor)
      .send({ from: producer, value: fee, gas: "900000" }),
  );
  await contract.methods.setPaused(false).send({ from: owner, gas: "120000" });

  const beforeWithdraw = await web3.eth.getBalance(contract.options.address);
  assert.equal(beforeWithdraw, fee);
  const withdrawn = await contract.methods
    .withdrawFees()
    .send({ from: owner, gas: "150000" });
  assert.ok(withdrawn.events.FeesWithdrawn);
  assert.equal(await web3.eth.getBalance(contract.options.address), 0n);
  await expectRevert(
    contract.methods.withdrawFees().send({ from: owner, gas: "150000" }),
  );

  await contract.methods.revokeRole(producer, 1).send({ from: owner, gas: "150000" });
  assert.equal(await contract.methods.hasRole(producer, 1).call(), false);
  assert.equal(await contract.methods.actionCount(distributor).call(), 2n);
  await provider.disconnect();
});
