// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "remix_tests.sol";
import "remix_accounts.sol";
import "../../contracts/EcoOrigem.sol";

contract EcoOrigemTest {
    EcoOrigem private ecoOrigem;

    function beforeAll() public {
        ecoOrigem = new EcoOrigem();
    }

    function ownerIsTestContract() public {
        Assert.equal(
            ecoOrigem.owner(),
            address(this),
            "O contrato de teste deve ser o proprietario"
        );
    }

    function registrationFeeIsExpected() public {
        Assert.equal(
            ecoOrigem.REGISTRATION_FEE(),
            0.00001 ether,
            "A taxa de cadastro deve permanecer fixa"
        );
    }

    function initialStateIsEmpty() public {
        Assert.equal(ecoOrigem.totalLots(), 0, "Nao deve haver lotes no inicio");
        Assert.equal(ecoOrigem.paused(), false, "O contrato deve iniciar ativo");
    }

    function ownerHasEveryRole() public {
        Assert.equal(
            ecoOrigem.hasRole(address(this), EcoOrigem.Role.Producer),
            true,
            "O proprietario deve possuir os perfis operacionais"
        );
    }

    function grantRoleWorks() public {
        address producer = TestsAccounts.getAccount(1);
        ecoOrigem.grantRole(producer, EcoOrigem.Role.Producer);
        Assert.equal(
            ecoOrigem.hasRole(producer, EcoOrigem.Role.Producer),
            true,
            "O perfil Produtor deve ser concedido"
        );
    }

    function statusLabelsAreReadable() public {
        Assert.equal(
            ecoOrigem.statusLabel(EcoOrigem.Status.Registered),
            "Cadastrado",
            "O estado inicial deve ter rotulo legivel"
        );
        Assert.equal(
            ecoOrigem.statusLabel(EcoOrigem.Status.Finalized),
            "Finalizado",
            "O estado final deve ter rotulo legivel"
        );
    }
}
