// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title EcoOrigem
/// @notice Rastreia lotes da bioeconomia amazônica na Ethereum Sepolia.
/// @dev Os arquivos ficam fora da rede; o contrato registra hash e URI IPFS.
contract EcoOrigem {
    // [Recurso: StructsEEnums]
    enum Role {
        None,
        Producer,
        Processor,
        Carrier,
        Distributor
    }

    enum Status {
        Registered,
        Processed,
        InTransit,
        Distributed,
        Finalized
    }

    struct Lot {
        uint256 id;
        string product;
        string origin;
        uint256 quantityGrams;
        uint256 harvestedAt;
        address producer;
        address custodian;
        address processor;
        address carrier;
        address distributor;
        Status status;
        int256 transportTemperatureMilliC;
        uint256 createdAt;
        uint256 updatedAt;
        bool active;
    }

    struct Document {
        bytes32 contentHash;
        string ipfsUri;
        string description;
        address author;
        uint256 timestamp;
    }

    struct HistoryEntry {
        Status status;
        address actor;
        uint256 timestamp;
        string note;
    }

    // [Recurso: TiposDeDados]
    uint256 public constant REGISTRATION_FEE = 0.00001 ether;
    uint256 public constant MAX_PAGE_SIZE = 50;
    uint256 private constant MIN_HARVEST_DATE = 946684800; // 01/01/2000
    address public immutable owner;
    address payable public immutable treasury;
    bool public paused;
    uint256 private lotCounter;

    // [Recurso: ArraysEMappings]
    uint256[] private lotIds;
    mapping(uint256 => Lot) private lots;
    mapping(uint256 => Document[]) private lotDocuments;
    mapping(uint256 => HistoryEntry[]) private lotHistory;
    mapping(address => mapping(Role => bool)) private roles;
    mapping(uint256 => mapping(bytes32 => bool)) private registeredDocuments;
    mapping(address => uint256) public actionCount;

    // [Recurso: EventosEErros]
    event RoleUpdated(
        address indexed account,
        Role indexed role,
        bool enabled
    );
    event LotRegistered(
        uint256 indexed lotId,
        address indexed producer,
        address indexed processor,
        string product
    );
    event LotStatusChanged(
        uint256 indexed lotId,
        Status indexed status,
        address indexed actor,
        string note
    );
    event DocumentAttached(
        uint256 indexed lotId,
        bytes32 indexed contentHash,
        address indexed author,
        string ipfsUri
    );
    event PauseChanged(bool paused, address indexed actor);
    event FeesWithdrawn(address indexed treasury, uint256 amount);

    error Unauthorized(address account, Role requiredRole);
    error InvalidStatus(uint256 lotId, Status current, Status expected);
    error LotNotFound(uint256 lotId);
    error InvalidData(string field);
    error WrongFee(uint256 received, uint256 expected);
    error DesignatedActorOnly(address caller, address expected);
    error DuplicateDocument(bytes32 contentHash);
    error FinalizedLot(uint256 lotId);
    error TransferFailed();

    // [Recurso: Funcoes]
    constructor() {
        owner = msg.sender;
        treasury = payable(msg.sender);
    }

    // [Recurso: Modificadores]
    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert Unauthorized(msg.sender, Role.None);
        }
        _;
    }

    modifier onlyRole(Role role) {
        if (!hasRole(msg.sender, role)) {
            revert Unauthorized(msg.sender, role);
        }
        _;
    }

    modifier lotExists(uint256 lotId) {
        if (!lots[lotId].active) {
            revert LotNotFound(lotId);
        }
        _;
    }

    modifier atStatus(uint256 lotId, Status expected) {
        Status current = lots[lotId].status;
        if (current != expected) {
            revert InvalidStatus(lotId, current, expected);
        }
        _;
    }

    modifier whenRunning() {
        require(!paused, "Contrato pausado");
        _;
    }

    /// @notice Concede um perfil operacional a uma carteira.
    /// @param account Carteira que receberá o perfil.
    /// @param role Perfil concedido.
    function grantRole(address account, Role role) external onlyOwner {
        _validateRoleUpdate(account, role, false);
        roles[account][role] = true;
        emit RoleUpdated(account, role, true);
    }

    /// @notice Revoga um perfil operacional de uma carteira.
    /// @param account Carteira que perderá o perfil.
    /// @param role Perfil revogado.
    function revokeRole(address account, Role role) external onlyOwner {
        _validateRoleUpdate(account, role, true);
        roles[account][role] = false;
        emit RoleUpdated(account, role, false);
    }

    /// @notice Pausa ou retoma as operações que alteram lotes.
    function setPaused(bool value) external onlyOwner {
        require(paused != value, "Estado de pausa inalterado");
        paused = value;
        emit PauseChanged(value, msg.sender);
    }

    /// @notice Cadastra um lote e designa o beneficiador.
    /// @param product Produto rastreado.
    /// @param origin Local de origem.
    /// @param quantityGrams Quantidade inteira em gramas.
    /// @param harvestedAt Data da coleta em timestamp Unix.
    /// @param processor Carteira designada para beneficiar o lote.
    function registerLot(
        string calldata product,
        string calldata origin,
        uint256 quantityGrams,
        uint256 harvestedAt,
        address processor
    ) external payable onlyRole(Role.Producer) whenRunning returns (uint256) {
        if (msg.value != REGISTRATION_FEE) {
            revert WrongFee(msg.value, REGISTRATION_FEE);
        }
        _validateLotInput(product, origin, quantityGrams, harvestedAt, processor);

        lotCounter += 1;
        uint256 lotId = lotCounter;
        lots[lotId] = Lot({
            id: lotId,
            product: product,
            origin: origin,
            quantityGrams: quantityGrams,
            harvestedAt: harvestedAt,
            producer: msg.sender,
            custodian: msg.sender,
            processor: processor,
            carrier: address(0),
            distributor: address(0),
            status: Status.Registered,
            transportTemperatureMilliC: 0,
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            active: true
        });
        lotIds.push(lotId);
        actionCount[msg.sender] += 1;

        _appendHistory(lotId, Status.Registered, "Lote cadastrado");
        emit LotRegistered(lotId, msg.sender, processor, product);
        return lotId;
    }

    /// @notice Registra o beneficiamento e designa o transportador.
    function recordProcessing(
        uint256 lotId,
        string calldata description,
        address carrier,
        bytes32 documentHash,
        string calldata ipfsUri
    )
        external
        onlyRole(Role.Processor)
        whenRunning
        lotExists(lotId)
        atStatus(lotId, Status.Registered)
    {
        Lot storage lot = lots[lotId];
        if (msg.sender != lot.processor) {
            revert DesignatedActorOnly(msg.sender, lot.processor);
        }
        if (!hasRole(carrier, Role.Carrier)) {
            revert Unauthorized(carrier, Role.Carrier);
        }
        if (!_validText(description, 3, 160)) {
            revert InvalidData("description");
        }
        _validateIpfsUri(ipfsUri);

        lot.carrier = carrier;
        lot.custodian = msg.sender;
        _advanceLot(lotId, Status.Processed, description);
        if (documentHash != bytes32(0)) {
            _storeDocument(
                lotId,
                documentHash,
                ipfsUri,
                "Laudo de beneficiamento"
            );
        }
    }

    /// @notice Inicia o transporte e designa o distribuidor.
    /// @param temperatureMilliC Temperatura em milésimos de grau Celsius.
    function startTransport(
        uint256 lotId,
        address distributor,
        string calldata destination,
        int256 temperatureMilliC
    )
        external
        onlyRole(Role.Carrier)
        whenRunning
        lotExists(lotId)
        atStatus(lotId, Status.Processed)
    {
        Lot storage lot = lots[lotId];
        if (msg.sender != lot.carrier) {
            revert DesignatedActorOnly(msg.sender, lot.carrier);
        }
        if (!hasRole(distributor, Role.Distributor)) {
            revert Unauthorized(distributor, Role.Distributor);
        }
        if (!_validText(destination, 3, 120)) {
            revert InvalidData("destination");
        }
        if (temperatureMilliC < -30000 || temperatureMilliC > 60000) {
            revert InvalidData("temperatureMilliC");
        }

        lot.distributor = distributor;
        lot.custodian = msg.sender;
        lot.transportTemperatureMilliC = temperatureMilliC;
        _advanceLot(lotId, Status.InTransit, destination);
    }

    /// @notice Confirma a entrega pelo distribuidor designado.
    function confirmDelivery(uint256 lotId, string calldata note)
        external
        onlyRole(Role.Distributor)
        whenRunning
        lotExists(lotId)
        atStatus(lotId, Status.InTransit)
    {
        Lot storage lot = lots[lotId];
        if (msg.sender != lot.distributor) {
            revert DesignatedActorOnly(msg.sender, lot.distributor);
        }
        if (!_validText(note, 0, 160)) {
            revert InvalidData("note");
        }

        lot.custodian = msg.sender;
        _advanceLot(lotId, Status.Distributed, note);
    }

    /// @notice Finaliza o lote depois do recebimento.
    function finalizeLot(uint256 lotId, string calldata note)
        external
        onlyRole(Role.Distributor)
        whenRunning
        lotExists(lotId)
        atStatus(lotId, Status.Distributed)
    {
        Lot storage lot = lots[lotId];
        if (msg.sender != lot.custodian) {
            revert DesignatedActorOnly(msg.sender, lot.custodian);
        }
        if (!_validText(note, 0, 160)) {
            revert InvalidData("note");
        }
        _advanceLot(lotId, Status.Finalized, note);
    }

    /// @notice Anexa a prova de integridade de um documento ao lote.
    function attachDocument(
        uint256 lotId,
        bytes32 contentHash,
        string calldata ipfsUri,
        string calldata description
    ) external whenRunning lotExists(lotId) {
        Lot storage lot = lots[lotId];
        if (lot.status == Status.Finalized) {
            revert FinalizedLot(lotId);
        }
        if (msg.sender != lot.custodian) {
            revert DesignatedActorOnly(msg.sender, lot.custodian);
        }
        if (contentHash == bytes32(0)) {
            revert InvalidData("contentHash");
        }
        if (!_validText(description, 3, 120)) {
            revert InvalidData("description");
        }
        _validateIpfsUri(ipfsUri);
        _storeDocument(lotId, contentHash, ipfsUri, description);
        actionCount[msg.sender] += 1;
    }

    /// @notice Transfere as taxas acumuladas para a tesouraria imutável.
    function withdrawFees() external onlyOwner {
        uint256 amount = address(this).balance;
        require(amount > 0, "Sem saldo para sacar");

        // Efeitos antes da interação externa evitam reentrância sobre estado mutável.
        (bool success, ) = treasury.call{value: amount}("");
        if (!success) {
            revert TransferFailed();
        }
        emit FeesWithdrawn(treasury, amount);
    }

    /// @notice Informa se uma carteira possui um perfil.
    function hasRole(address account, Role role) public view returns (bool) {
        return account == owner || roles[account][role];
    }

    /// @notice Retorna o total de lotes cadastrados.
    function totalLots() public view returns (uint256) {
        return lotIds.length;
    }

    /// @notice Retorna um lote pelo identificador.
    function getLot(uint256 lotId)
        external
        view
        lotExists(lotId)
        returns (Lot memory)
    {
        return lots[lotId];
    }

    /// @notice Lista uma página de lotes para evitar laços sem limite.
    function getLots(uint256 offset, uint256 limit)
        external
        view
        returns (Lot[] memory page)
    {
        require(limit > 0 && limit <= MAX_PAGE_SIZE, "Limite entre 1 e 50");
        if (offset >= lotIds.length) {
            return new Lot[](0);
        }

        uint256 end = offset + limit;
        if (end > lotIds.length) {
            end = lotIds.length;
        }
        page = new Lot[](end - offset);

        // [Recurso: EstruturasDeControle]
        for (uint256 i = offset; i < end; i += 1) {
            page[i - offset] = lots[lotIds[i]];
        }
    }

    /// @notice Retorna os documentos registrados para um lote.
    function getDocuments(uint256 lotId)
        external
        view
        lotExists(lotId)
        returns (Document[] memory)
    {
        return lotDocuments[lotId];
    }

    /// @notice Retorna o histórico de estados de um lote.
    function getHistory(uint256 lotId)
        external
        view
        lotExists(lotId)
        returns (HistoryEntry[] memory)
    {
        return lotHistory[lotId];
    }

    /// @notice Traduz o enum de estado para texto legível.
    function statusLabel(Status status) public pure returns (string memory) {
        if (status == Status.Registered) return "Cadastrado";
        else if (status == Status.Processed) return "Beneficiado";
        else if (status == Status.InTransit) return "Em transporte";
        else if (status == Status.Distributed) return "Distribuido";
        else return "Finalizado";
    }

    function _advanceLot(
        uint256 lotId,
        Status status,
        string memory note
    ) internal {
        Lot storage lot = lots[lotId];
        lot.status = status;
        lot.updatedAt = block.timestamp;
        actionCount[msg.sender] += 1;
        _appendHistory(lotId, status, note);
        emit LotStatusChanged(lotId, status, msg.sender, note);
    }

    function _appendHistory(
        uint256 lotId,
        Status status,
        string memory note
    ) internal {
        lotHistory[lotId].push(
            HistoryEntry({
                status: status,
                actor: msg.sender,
                timestamp: block.timestamp,
                note: note
            })
        );
    }

    function _storeDocument(
        uint256 lotId,
        bytes32 contentHash,
        string memory ipfsUri,
        string memory description
    ) private {
        if (registeredDocuments[lotId][contentHash]) {
            revert DuplicateDocument(contentHash);
        }
        registeredDocuments[lotId][contentHash] = true;
        lotDocuments[lotId].push(
            Document({
                contentHash: contentHash,
                ipfsUri: ipfsUri,
                description: description,
                author: msg.sender,
                timestamp: block.timestamp
            })
        );
        emit DocumentAttached(lotId, contentHash, msg.sender, ipfsUri);
    }

    function _validateLotInput(
        string calldata product,
        string calldata origin,
        uint256 quantityGrams,
        uint256 harvestedAt,
        address processor
    ) private view {
        if (!_validText(product, 2, 60)) revert InvalidData("product");
        if (!_validText(origin, 3, 120)) revert InvalidData("origin");
        if (quantityGrams == 0 || quantityGrams > 100_000_000) {
            revert InvalidData("quantityGrams");
        }
        if (harvestedAt < MIN_HARVEST_DATE || harvestedAt > block.timestamp) {
            revert InvalidData("harvestedAt");
        }
        if (!hasRole(processor, Role.Processor)) {
            revert Unauthorized(processor, Role.Processor);
        }
    }

    function _validateRoleUpdate(
        address account,
        Role role,
        bool expectedCurrentValue
    ) private view {
        if (account == address(0)) revert InvalidData("account");
        if (role == Role.None) revert InvalidData("role");
        require(
            roles[account][role] == expectedCurrentValue,
            "Perfil ja esta no estado solicitado"
        );
    }

    function _validateIpfsUri(string memory ipfsUri) private pure {
        bytes memory uri = bytes(ipfsUri);
        if (uri.length > 120) revert InvalidData("ipfsUri");
        if (uri.length > 0 && uri.length < 10) revert InvalidData("ipfsUri");
    }

    function _validText(
        string memory value,
        uint256 minLength,
        uint256 maxLength
    ) private pure returns (bool) {
        uint256 length = bytes(value).length;
        return length >= minLength && length <= maxLength;
    }
}
