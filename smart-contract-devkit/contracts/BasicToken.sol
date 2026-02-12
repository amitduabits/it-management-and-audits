// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title BasicToken
 * @notice An ERC-20 compatible fungible token implementation built from scratch.
 * @dev Implements the full ERC-20 standard interface without importing OpenZeppelin,
 *      so that every line of logic is visible and documented for learning purposes.
 *
 *      ERC-20 Standard Functions:
 *      - totalSupply()     : Returns total token supply
 *      - balanceOf()       : Returns balance of an account
 *      - transfer()        : Transfers tokens to a recipient
 *      - approve()         : Approves a spender to spend tokens
 *      - allowance()       : Returns remaining approved amount
 *      - transferFrom()    : Transfers tokens on behalf of an owner
 *
 *      Additional Features:
 *      - Minting (owner only) with cap enforcement
 *      - Burning (any holder can burn their own tokens)
 *      - Pausable transfers (emergency stop pattern)
 *
 *      Security Features:
 *      - Overflow/underflow protection (Solidity 0.8.x native)
 *      - Zero-address validation on all transfers
 *      - Allowance race condition mitigation via increaseAllowance/decreaseAllowance
 */
contract BasicToken {
    // =========================================================================
    // State Variables
    // =========================================================================

    /// @notice Human-readable name of the token (e.g., "DevKit Token")
    string public name;

    /// @notice Abbreviated symbol of the token (e.g., "DKT")
    string public symbol;

    /// @notice Number of decimal places the token uses (18 is standard)
    uint8 public constant decimals = 18;

    /// @notice Maximum number of tokens that can ever exist
    uint256 public immutable cap;

    /// @notice Total number of tokens currently in circulation
    uint256 private _totalSupply;

    /// @notice The address that deployed the contract and has minting rights
    address public owner;

    /// @notice Whether token transfers are currently paused
    bool public paused;

    /// @notice Maps each address to its token balance
    mapping(address => uint256) private _balances;

    /// @notice Maps owner => spender => approved amount
    mapping(address => mapping(address => uint256)) private _allowances;

    // =========================================================================
    // Events (ERC-20 Standard + Extensions)
    // =========================================================================

    /**
     * @notice Emitted when tokens are transferred between addresses
     * @param from The sender address (address(0) for minting)
     * @param to The recipient address (address(0) for burning)
     * @param value The number of tokens transferred
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @notice Emitted when an allowance is set via approve or modified
     * @param owner The address that owns the tokens
     * @param spender The address approved to spend
     * @param value The approved amount
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);

    /// @notice Emitted when the contract is paused
    event Paused(address indexed account);

    /// @notice Emitted when the contract is unpaused
    event Unpaused(address indexed account);

    /// @notice Emitted when ownership is transferred
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // =========================================================================
    // Custom Errors
    // =========================================================================

    error NotOwner(address caller);
    error ZeroAddress();
    error InsufficientBalance(uint256 available, uint256 required);
    error InsufficientAllowance(uint256 available, uint256 required);
    error CapExceeded(uint256 currentSupply, uint256 mintAmount, uint256 maxCap);
    error ContractPaused();
    error ContractNotPaused();
    error AllowanceUnderflow();

    // =========================================================================
    // Modifiers
    // =========================================================================

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner(msg.sender);
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert ContractPaused();
        _;
    }

    modifier whenPaused() {
        if (!paused) revert ContractNotPaused();
        _;
    }

    modifier validAddress(address account) {
        if (account == address(0)) revert ZeroAddress();
        _;
    }

    // =========================================================================
    // Constructor
    // =========================================================================

    /**
     * @notice Deploys the token with a name, symbol, initial supply, and cap
     * @param _name The human-readable token name
     * @param _symbol The token ticker symbol
     * @param _initialSupply Number of tokens to mint to the deployer (in whole units)
     * @param _cap Maximum total supply (in whole units); must be >= initialSupply
     * @dev The initial supply and cap are multiplied by 10^decimals internally.
     */
    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply,
        uint256 _cap
    ) {
        require(_cap >= _initialSupply, "Cap must be >= initial supply");

        name = _name;
        symbol = _symbol;
        owner = msg.sender;

        // Convert whole-unit amounts to their smallest denomination
        cap = _cap * 10 ** decimals;
        uint256 initialAmount = _initialSupply * 10 ** decimals;

        _totalSupply = initialAmount;
        _balances[msg.sender] = initialAmount;

        emit Transfer(address(0), msg.sender, initialAmount);
    }

    // =========================================================================
    // ERC-20 Standard Functions
    // =========================================================================

    /**
     * @notice Returns the total supply of tokens in circulation
     * @return Total token supply including all decimals
     */
    function totalSupply() external view returns (uint256) {
        return _totalSupply;
    }

    /**
     * @notice Returns the token balance of a specific account
     * @param account The address to query
     * @return The token balance of the account
     */
    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    /**
     * @notice Transfers tokens from the caller to a recipient
     * @param to The recipient address
     * @param amount The number of tokens to transfer
     * @return success True if the transfer succeeded
     *
     * @dev Requirements:
     *      - `to` cannot be the zero address
     *      - Caller must have a balance >= `amount`
     *      - Contract must not be paused
     */
    function transfer(address to, uint256 amount)
        external
        whenNotPaused
        validAddress(to)
        returns (bool success)
    {
        _transfer(msg.sender, to, amount);
        return true;
    }

    /**
     * @notice Sets the allowance for a spender to spend caller's tokens
     * @param spender The address authorized to spend
     * @param amount The maximum amount they can spend
     * @return success True if the approval succeeded
     *
     * @dev WARNING: Changing an allowance with this method introduces a race
     *      condition. Use increaseAllowance/decreaseAllowance instead when
     *      modifying existing non-zero allowances. See:
     *      https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     */
    function approve(address spender, uint256 amount)
        external
        validAddress(spender)
        returns (bool success)
    {
        _approve(msg.sender, spender, amount);
        return true;
    }

    /**
     * @notice Returns the remaining allowance for a spender
     * @param _owner The address that owns the tokens
     * @param spender The address approved to spend
     * @return The remaining approved amount
     */
    function allowance(address _owner, address spender)
        external
        view
        returns (uint256)
    {
        return _allowances[_owner][spender];
    }

    /**
     * @notice Transfers tokens from one address to another using an allowance
     * @param from The address to transfer from
     * @param to The address to transfer to
     * @param amount The number of tokens to transfer
     * @return success True if the transfer succeeded
     *
     * @dev The caller must have an allowance >= `amount` from `from`.
     *      The allowance is decreased by the transferred amount.
     */
    function transferFrom(address from, address to, uint256 amount)
        external
        whenNotPaused
        validAddress(to)
        returns (bool success)
    {
        uint256 currentAllowance = _allowances[from][msg.sender];
        if (currentAllowance < amount) {
            revert InsufficientAllowance(currentAllowance, amount);
        }

        // Decrease allowance before transfer (checks-effects-interactions)
        unchecked {
            _approve(from, msg.sender, currentAllowance - amount);
        }

        _transfer(from, to, amount);
        return true;
    }

    // =========================================================================
    // Allowance Safety Helpers (Mitigate race condition)
    // =========================================================================

    /**
     * @notice Safely increases the allowance for a spender
     * @param spender The address whose allowance increases
     * @param addedValue The amount to add to the current allowance
     * @return True if successful
     */
    function increaseAllowance(address spender, uint256 addedValue)
        external
        validAddress(spender)
        returns (bool)
    {
        _approve(
            msg.sender,
            spender,
            _allowances[msg.sender][spender] + addedValue
        );
        return true;
    }

    /**
     * @notice Safely decreases the allowance for a spender
     * @param spender The address whose allowance decreases
     * @param subtractedValue The amount to subtract from the current allowance
     * @return True if successful
     */
    function decreaseAllowance(address spender, uint256 subtractedValue)
        external
        validAddress(spender)
        returns (bool)
    {
        uint256 currentAllowance = _allowances[msg.sender][spender];
        if (subtractedValue > currentAllowance) {
            revert AllowanceUnderflow();
        }
        unchecked {
            _approve(msg.sender, spender, currentAllowance - subtractedValue);
        }
        return true;
    }

    // =========================================================================
    // Minting & Burning
    // =========================================================================

    /**
     * @notice Creates new tokens and assigns them to a recipient
     * @param to The address that receives the newly minted tokens
     * @param amount The number of tokens to mint (in smallest unit)
     *
     * @dev Only the owner can mint. Total supply must not exceed the cap.
     */
    function mint(address to, uint256 amount)
        external
        onlyOwner
        validAddress(to)
    {
        if (_totalSupply + amount > cap) {
            revert CapExceeded(_totalSupply, amount, cap);
        }

        _totalSupply += amount;
        _balances[to] += amount;

        emit Transfer(address(0), to, amount);
    }

    /**
     * @notice Permanently destroys tokens from the caller's balance
     * @param amount The number of tokens to burn
     *
     * @dev Any token holder can burn their own tokens.
     *      This reduces the total supply permanently.
     */
    function burn(uint256 amount) external {
        if (_balances[msg.sender] < amount) {
            revert InsufficientBalance(_balances[msg.sender], amount);
        }

        unchecked {
            _balances[msg.sender] -= amount;
        }
        _totalSupply -= amount;

        emit Transfer(msg.sender, address(0), amount);
    }

    // =========================================================================
    // Pausable (Emergency Stop Pattern)
    // =========================================================================

    /**
     * @notice Pauses all token transfers
     * @dev Only callable by the owner when the contract is not paused
     */
    function pause() external onlyOwner whenNotPaused {
        paused = true;
        emit Paused(msg.sender);
    }

    /**
     * @notice Unpauses all token transfers
     * @dev Only callable by the owner when the contract is paused
     */
    function unpause() external onlyOwner whenPaused {
        paused = false;
        emit Unpaused(msg.sender);
    }

    // =========================================================================
    // Ownership
    // =========================================================================

    /**
     * @notice Transfers contract ownership to a new address
     * @param newOwner The address of the new owner
     */
    function transferOwnership(address newOwner)
        external
        onlyOwner
        validAddress(newOwner)
    {
        address previousOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    // =========================================================================
    // Internal Functions
    // =========================================================================

    /**
     * @dev Internal transfer logic shared by transfer() and transferFrom()
     * @param from Sender address
     * @param to Recipient address
     * @param amount Token amount
     */
    function _transfer(address from, address to, uint256 amount) internal {
        if (_balances[from] < amount) {
            revert InsufficientBalance(_balances[from], amount);
        }

        unchecked {
            _balances[from] -= amount;
        }
        _balances[to] += amount;

        emit Transfer(from, to, amount);
    }

    /**
     * @dev Internal approval logic
     * @param _owner Token owner
     * @param spender Approved spender
     * @param amount Approved amount
     */
    function _approve(address _owner, address spender, uint256 amount) internal {
        _allowances[_owner][spender] = amount;
        emit Approval(_owner, spender, amount);
    }
}
