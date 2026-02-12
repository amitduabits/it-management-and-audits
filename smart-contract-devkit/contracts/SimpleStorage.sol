// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleStorage
 * @notice A straightforward contract for storing and retrieving unsigned integers.
 * @dev Demonstrates state variables, events, modifiers, and basic access control.
 *      This serves as a foundational example for developers new to Solidity.
 *
 *      Key Concepts Covered:
 *      - State variable declaration and visibility
 *      - Custom events for off-chain indexing
 *      - Ownable pattern without external dependencies
 *      - View vs. state-changing functions
 *      - Mapping data structure for key-value storage
 */
contract SimpleStorage {
    // =========================================================================
    // State Variables
    // =========================================================================

    /// @notice The address that deployed this contract
    address public owner;

    /// @notice The currently stored unsigned integer value
    uint256 private _storedValue;

    /// @notice Tracks the total number of times the value has been updated
    uint256 public updateCount;

    /// @notice Maps addresses to their last stored value (historical tracking)
    mapping(address => uint256) public lastValueByAddress;

    /// @notice Maps addresses to the timestamp of their last update
    mapping(address => uint256) public lastUpdateTimestamp;

    // =========================================================================
    // Events
    // =========================================================================

    /**
     * @notice Emitted whenever the stored value changes
     * @param previousValue The value before the update
     * @param newValue The value after the update
     * @param updatedBy The address that performed the update
     * @param timestamp The block timestamp when the update occurred
     */
    event ValueChanged(
        uint256 indexed previousValue,
        uint256 indexed newValue,
        address indexed updatedBy,
        uint256 timestamp
    );

    /**
     * @notice Emitted when contract ownership is transferred
     * @param previousOwner The address of the former owner
     * @param newOwner The address of the new owner
     */
    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );

    // =========================================================================
    // Errors (Custom errors save gas compared to revert strings)
    // =========================================================================

    /// @notice Thrown when a non-owner tries to call an owner-only function
    error NotOwner(address caller);

    /// @notice Thrown when the new value is the same as the current value
    error ValueUnchanged(uint256 currentValue);

    /// @notice Thrown when the zero address is provided where it shouldn't be
    error ZeroAddressNotAllowed();

    // =========================================================================
    // Modifiers
    // =========================================================================

    /**
     * @notice Restricts function access to the contract owner
     * @dev Uses custom error for gas efficiency
     */
    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert NotOwner(msg.sender);
        }
        _;
    }

    // =========================================================================
    // Constructor
    // =========================================================================

    /**
     * @notice Initializes the contract with an optional starting value
     * @param initialValue The value to store upon deployment
     * @dev The deployer automatically becomes the contract owner
     */
    constructor(uint256 initialValue) {
        owner = msg.sender;
        _storedValue = initialValue;

        emit ValueChanged(0, initialValue, msg.sender, block.timestamp);
    }

    // =========================================================================
    // External / Public Functions
    // =========================================================================

    /**
     * @notice Stores a new unsigned integer value
     * @param newValue The value to store
     * @dev Reverts if the new value equals the current value to prevent
     *      unnecessary state changes and wasted gas.
     *
     * Security considerations:
     * - No access restriction: any address can call this function
     * - Duplicate value check prevents wasteful transactions
     * - Event emission enables off-chain tracking
     */
    function set(uint256 newValue) external {
        uint256 previousValue = _storedValue;

        if (newValue == previousValue) {
            revert ValueUnchanged(previousValue);
        }

        _storedValue = newValue;
        updateCount += 1;
        lastValueByAddress[msg.sender] = newValue;
        lastUpdateTimestamp[msg.sender] = block.timestamp;

        emit ValueChanged(previousValue, newValue, msg.sender, block.timestamp);
    }

    /**
     * @notice Retrieves the currently stored value
     * @return The current unsigned integer value
     * @dev This is a view function -- it reads state but does not modify it,
     *      so calling it does not cost gas when called externally (off-chain).
     */
    function get() external view returns (uint256) {
        return _storedValue;
    }

    /**
     * @notice Retrieves the stored value along with metadata
     * @return value The current stored value
     * @return totalUpdates The total number of updates performed
     * @return contractOwner The address of the contract owner
     * @dev Demonstrates returning multiple values from a function
     */
    function getDetails()
        external
        view
        returns (
            uint256 value,
            uint256 totalUpdates,
            address contractOwner
        )
    {
        return (_storedValue, updateCount, owner);
    }

    /**
     * @notice Resets the stored value to zero (owner only)
     * @dev Restricted to the contract owner as a safety measure
     */
    function reset() external onlyOwner {
        uint256 previousValue = _storedValue;
        _storedValue = 0;
        updateCount += 1;

        emit ValueChanged(previousValue, 0, msg.sender, block.timestamp);
    }

    /**
     * @notice Transfers ownership of the contract to a new address
     * @param newOwner The address of the new owner
     * @dev Only the current owner can transfer ownership.
     *      Cannot transfer to the zero address.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) {
            revert ZeroAddressNotAllowed();
        }

        address previousOwner = owner;
        owner = newOwner;

        emit OwnershipTransferred(previousOwner, newOwner);
    }

    /**
     * @notice Increments the stored value by a given amount
     * @param amount The amount to add to the current value
     * @dev Uses Solidity 0.8.x built-in overflow protection.
     *      Prior to 0.8.x, SafeMath would be needed here.
     */
    function increment(uint256 amount) external {
        uint256 previousValue = _storedValue;
        _storedValue += amount; // Overflow automatically reverts in 0.8.x
        updateCount += 1;
        lastValueByAddress[msg.sender] = _storedValue;
        lastUpdateTimestamp[msg.sender] = block.timestamp;

        emit ValueChanged(previousValue, _storedValue, msg.sender, block.timestamp);
    }

    /**
     * @notice Decrements the stored value by a given amount
     * @param amount The amount to subtract from the current value
     * @dev Uses Solidity 0.8.x built-in underflow protection.
     */
    function decrement(uint256 amount) external {
        uint256 previousValue = _storedValue;
        _storedValue -= amount; // Underflow automatically reverts in 0.8.x
        updateCount += 1;
        lastValueByAddress[msg.sender] = _storedValue;
        lastUpdateTimestamp[msg.sender] = block.timestamp;

        emit ValueChanged(previousValue, _storedValue, msg.sender, block.timestamp);
    }
}
