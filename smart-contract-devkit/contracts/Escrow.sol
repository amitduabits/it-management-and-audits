// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Escrow
 * @notice A two-party escrow contract with deposit, release, refund, and dispute resolution.
 * @dev Implements the following security patterns:
 *      - Reentrancy Guard: Prevents recursive calls during ETH transfers
 *      - Checks-Effects-Interactions: State changes before external calls
 *      - Pull Payment: Funds are withdrawn, not pushed
 *      - State Machine: Strict escrow lifecycle management
 *
 *      Escrow Lifecycle:
 *      1. Buyer creates escrow specifying seller and amount
 *      2. Buyer deposits ETH into the escrow
 *      3. After goods/services are delivered:
 *         a. Buyer releases funds to seller, OR
 *         b. Either party initiates a dispute
 *      4. If disputed, the arbiter can resolve it
 *      5. If expired, buyer can reclaim funds
 */
contract Escrow {
    // =========================================================================
    // Enums & Structs
    // =========================================================================

    /**
     * @notice The possible states of an escrow
     * @dev State transitions:
     *      Created -> Funded -> Released (happy path)
     *      Created -> Funded -> Refunded (cancellation)
     *      Created -> Funded -> Disputed -> Resolved
     */
    enum EscrowState {
        Created,    // 0: Escrow created but not yet funded
        Funded,     // 1: Buyer has deposited funds
        Released,   // 2: Funds released to the seller
        Refunded,   // 3: Funds returned to the buyer
        Disputed,   // 4: A dispute has been raised
        Resolved    // 5: Dispute resolved by arbiter
    }

    /**
     * @notice Full details of an escrow agreement
     */
    struct EscrowDetails {
        address buyer;          // The party depositing funds
        address payable seller; // The party receiving funds on release
        address arbiter;        // Neutral third party for disputes
        uint256 amount;         // The agreed-upon escrow amount in wei
        uint256 createdAt;      // Timestamp of escrow creation
        uint256 deadline;       // Deadline after which buyer can reclaim
        EscrowState state;      // Current escrow state
        string description;     // Human-readable description
    }

    // =========================================================================
    // State Variables
    // =========================================================================

    /// @notice Auto-incrementing ID for each escrow
    uint256 public escrowCount;

    /// @notice Maps escrow ID to its details
    mapping(uint256 => EscrowDetails) public escrows;

    /// @notice Reentrancy guard lock
    bool private _locked;

    /// @notice Platform fee percentage (in basis points, 100 = 1%)
    uint256 public constant PLATFORM_FEE_BPS = 100;

    /// @notice Minimum escrow duration in seconds (1 day)
    uint256 public constant MIN_DURATION = 1 days;

    /// @notice Contract deployer who receives platform fees
    address payable public platformOwner;

    /// @notice Accumulated platform fees available for withdrawal
    uint256 public platformBalance;

    // =========================================================================
    // Events
    // =========================================================================

    event EscrowCreated(
        uint256 indexed escrowId,
        address indexed buyer,
        address indexed seller,
        uint256 amount,
        uint256 deadline
    );

    event EscrowFunded(uint256 indexed escrowId, uint256 amount);
    event EscrowReleased(uint256 indexed escrowId, uint256 amountToSeller, uint256 fee);
    event EscrowRefunded(uint256 indexed escrowId, uint256 amount);
    event DisputeRaised(uint256 indexed escrowId, address raisedBy);
    event DisputeResolved(uint256 indexed escrowId, address recipient, uint256 amount);

    // =========================================================================
    // Custom Errors
    // =========================================================================

    error Unauthorized(address caller, string role);
    error InvalidState(EscrowState current, EscrowState expected);
    error InvalidAmount();
    error InvalidDeadline();
    error ZeroAddress();
    error TransferFailed();
    error ReentrancyDetected();
    error DeadlineNotReached();
    error DeadlinePassed();

    // =========================================================================
    // Modifiers
    // =========================================================================

    /**
     * @notice Prevents reentrant calls
     * @dev Sets a lock before function execution and releases it after.
     *      This is critical for any function that sends ETH.
     */
    modifier nonReentrant() {
        if (_locked) revert ReentrancyDetected();
        _locked = true;
        _;
        _locked = false;
    }

    /// @notice Ensures only the buyer of a given escrow can call
    modifier onlyBuyer(uint256 escrowId) {
        if (msg.sender != escrows[escrowId].buyer)
            revert Unauthorized(msg.sender, "buyer");
        _;
    }

    /// @notice Ensures only the seller of a given escrow can call
    modifier onlySeller(uint256 escrowId) {
        if (msg.sender != escrows[escrowId].seller)
            revert Unauthorized(msg.sender, "seller");
        _;
    }

    /// @notice Ensures only the arbiter of a given escrow can call
    modifier onlyArbiter(uint256 escrowId) {
        if (msg.sender != escrows[escrowId].arbiter)
            revert Unauthorized(msg.sender, "arbiter");
        _;
    }

    /// @notice Ensures the escrow is in the expected state
    modifier inState(uint256 escrowId, EscrowState expected) {
        if (escrows[escrowId].state != expected)
            revert InvalidState(escrows[escrowId].state, expected);
        _;
    }

    // =========================================================================
    // Constructor
    // =========================================================================

    /**
     * @notice Deploys the escrow platform
     * @dev The deployer becomes the platform owner who receives fees
     */
    constructor() {
        platformOwner = payable(msg.sender);
    }

    // =========================================================================
    // Core Escrow Functions
    // =========================================================================

    /**
     * @notice Creates a new escrow agreement
     * @param seller The address that will receive funds upon release
     * @param arbiter A trusted third party for dispute resolution
     * @param duration How long (in seconds) before the escrow expires
     * @param description A text description of the escrow terms
     * @return escrowId The ID of the newly created escrow
     *
     * @dev The amount is set to msg.value. Escrow is created in Funded state
     *      when ETH is sent, or Created state if no ETH is sent.
     */
    function createEscrow(
        address payable seller,
        address arbiter,
        uint256 duration,
        string calldata description
    ) external payable returns (uint256 escrowId) {
        // Input validation
        if (seller == address(0) || arbiter == address(0)) revert ZeroAddress();
        if (duration < MIN_DURATION) revert InvalidDeadline();
        if (msg.value == 0) revert InvalidAmount();

        escrowId = escrowCount++;

        escrows[escrowId] = EscrowDetails({
            buyer: msg.sender,
            seller: seller,
            arbiter: arbiter,
            amount: msg.value,
            createdAt: block.timestamp,
            deadline: block.timestamp + duration,
            state: EscrowState.Funded,
            description: description
        });

        emit EscrowCreated(escrowId, msg.sender, seller, msg.value, block.timestamp + duration);
        emit EscrowFunded(escrowId, msg.value);
    }

    /**
     * @notice Buyer releases escrowed funds to the seller
     * @param escrowId The ID of the escrow to release
     *
     * @dev This is the happy-path conclusion. A platform fee is deducted.
     *
     * Security:
     * - Only the buyer can release funds
     * - Escrow must be in Funded state
     * - State is changed BEFORE the external call (checks-effects-interactions)
     * - nonReentrant guard prevents recursive calls
     */
    function release(uint256 escrowId)
        external
        nonReentrant
        onlyBuyer(escrowId)
        inState(escrowId, EscrowState.Funded)
    {
        EscrowDetails storage escrow = escrows[escrowId];

        // Calculate platform fee
        uint256 fee = (escrow.amount * PLATFORM_FEE_BPS) / 10000;
        uint256 sellerAmount = escrow.amount - fee;

        // Effects: Update state BEFORE external calls
        escrow.state = EscrowState.Released;
        platformBalance += fee;

        // Interaction: Send ETH to seller
        (bool success, ) = escrow.seller.call{value: sellerAmount}("");
        if (!success) revert TransferFailed();

        emit EscrowReleased(escrowId, sellerAmount, fee);
    }

    /**
     * @notice Refunds the escrowed funds back to the buyer
     * @param escrowId The ID of the escrow to refund
     *
     * @dev Can be called by the seller (voluntary refund) or by the buyer
     *      after the deadline has passed.
     */
    function refund(uint256 escrowId)
        external
        nonReentrant
        inState(escrowId, EscrowState.Funded)
    {
        EscrowDetails storage escrow = escrows[escrowId];

        // Seller can always issue a refund
        // Buyer can only refund after deadline
        if (msg.sender == escrow.buyer) {
            if (block.timestamp < escrow.deadline) revert DeadlineNotReached();
        } else if (msg.sender != escrow.seller) {
            revert Unauthorized(msg.sender, "buyer or seller");
        }

        uint256 refundAmount = escrow.amount;

        // Effects first
        escrow.state = EscrowState.Refunded;

        // Interaction
        (bool success, ) = payable(escrow.buyer).call{value: refundAmount}("");
        if (!success) revert TransferFailed();

        emit EscrowRefunded(escrowId, refundAmount);
    }

    /**
     * @notice Raises a dispute on a funded escrow
     * @param escrowId The ID of the escrow to dispute
     *
     * @dev Only the buyer or seller can raise a dispute.
     *      Once disputed, only the arbiter can resolve it.
     */
    function raiseDispute(uint256 escrowId)
        external
        inState(escrowId, EscrowState.Funded)
    {
        EscrowDetails storage escrow = escrows[escrowId];

        if (msg.sender != escrow.buyer && msg.sender != escrow.seller) {
            revert Unauthorized(msg.sender, "buyer or seller");
        }

        escrow.state = EscrowState.Disputed;

        emit DisputeRaised(escrowId, msg.sender);
    }

    /**
     * @notice Arbiter resolves a dispute by sending funds to the winning party
     * @param escrowId The ID of the disputed escrow
     * @param recipient The address that should receive the funds (buyer or seller)
     *
     * @dev The arbiter decides who gets the funds. A platform fee is still taken.
     *
     * Security:
     * - Only the arbiter can resolve
     * - Recipient must be the buyer or seller (no arbitrary addresses)
     * - nonReentrant prevents reentrancy during ETH transfer
     */
    function resolveDispute(uint256 escrowId, address payable recipient)
        external
        nonReentrant
        onlyArbiter(escrowId)
        inState(escrowId, EscrowState.Disputed)
    {
        EscrowDetails storage escrow = escrows[escrowId];

        // Recipient must be either buyer or seller
        if (recipient != escrow.buyer && recipient != escrow.seller) {
            revert Unauthorized(recipient, "buyer or seller");
        }

        uint256 fee = (escrow.amount * PLATFORM_FEE_BPS) / 10000;
        uint256 recipientAmount = escrow.amount - fee;

        // Effects
        escrow.state = EscrowState.Resolved;
        platformBalance += fee;

        // Interaction
        (bool success, ) = recipient.call{value: recipientAmount}("");
        if (!success) revert TransferFailed();

        emit DisputeResolved(escrowId, recipient, recipientAmount);
    }

    // =========================================================================
    // View Functions
    // =========================================================================

    /**
     * @notice Returns full details of an escrow
     * @param escrowId The escrow to query
     * @return The EscrowDetails struct
     */
    function getEscrow(uint256 escrowId)
        external
        view
        returns (EscrowDetails memory)
    {
        return escrows[escrowId];
    }

    /**
     * @notice Checks if an escrow has passed its deadline
     * @param escrowId The escrow to check
     * @return True if the current time is past the deadline
     */
    function isExpired(uint256 escrowId) external view returns (bool) {
        return block.timestamp >= escrows[escrowId].deadline;
    }

    // =========================================================================
    // Platform Functions
    // =========================================================================

    /**
     * @notice Withdraws accumulated platform fees
     * @dev Only the platform owner can call this
     */
    function withdrawPlatformFees() external nonReentrant {
        if (msg.sender != platformOwner) revert Unauthorized(msg.sender, "platform owner");

        uint256 amount = platformBalance;
        if (amount == 0) revert InvalidAmount();

        platformBalance = 0;

        (bool success, ) = platformOwner.call{value: amount}("");
        if (!success) revert TransferFailed();
    }

    /**
     * @notice Returns the contract's total ETH balance
     * @return The balance in wei
     */
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
