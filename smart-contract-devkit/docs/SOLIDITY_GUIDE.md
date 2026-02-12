# Solidity Language Guide

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Data Types](#data-types)
4. [Variables and Storage](#variables-and-storage)
5. [Functions](#functions)
6. [Modifiers](#modifiers)
7. [Events](#events)
8. [Error Handling](#error-handling)
9. [Control Structures](#control-structures)
10. [Mappings and Arrays](#mappings-and-arrays)
11. [Structs and Enums](#structs-and-enums)
12. [Inheritance](#inheritance)
13. [Interfaces](#interfaces)
14. [Security Patterns](#security-patterns)
15. [Gas Optimization Tips](#gas-optimization-tips)
16. [Common Pitfalls](#common-pitfalls)

---

## Overview

Solidity is a statically-typed, contract-oriented programming language designed for the Ethereum Virtual Machine (EVM). It draws syntax inspiration from JavaScript, C++, and Python.

**Current stable version**: 0.8.x (used in this project)

**Key features of 0.8.x**:
- Built-in overflow/underflow protection (no SafeMath needed)
- Custom errors for gas-efficient reverts
- User-defined value types
- Improved ABI encoder (v2 by default)

---

## File Structure

Every Solidity file follows this structure:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// Import statements (if any)
// import "./OtherContract.sol";

/**
 * @title ContractName
 * @notice What this contract does (user-facing)
 * @dev Technical implementation details (developer-facing)
 */
contract ContractName {
    // State variables
    // Events
    // Errors
    // Modifiers
    // Constructor
    // External functions
    // Public functions
    // Internal functions
    // Private functions
}
```

### License Identifier

The `SPDX-License-Identifier` comment is required by the compiler. Common options:
- `MIT` -- Permissive open source
- `GPL-3.0` -- Copyleft open source
- `UNLICENSED` -- No license (proprietary)

### Pragma Directive

```solidity
pragma solidity ^0.8.19;  // Any 0.8.x version >= 0.8.19
pragma solidity >=0.8.0 <0.9.0;  // Range specification
pragma solidity 0.8.19;  // Exact version (most restrictive)
```

---

## Data Types

### Value Types

| Type | Size | Default | Example |
|:-----|:-----|:--------|:--------|
| `bool` | 1 byte | `false` | `true`, `false` |
| `uint256` | 32 bytes | `0` | `42`, `1e18` |
| `int256` | 32 bytes | `0` | `-1`, `100` |
| `address` | 20 bytes | `0x0` | `0x742d...2bD18` |
| `bytes32` | 32 bytes | `0x0` | Fixed-size byte array |

**Smaller integer types**: `uint8`, `uint16`, `uint32`, ..., `uint256` (in 8-bit increments). Same for `int`.

### Reference Types

```solidity
string public name = "Hello";          // Dynamic UTF-8 string
bytes public data = hex"001122";       // Dynamic byte array
uint256[] public numbers;              // Dynamic array
uint256[10] public fixedArray;         // Fixed-size array
```

### Address Type

```solidity
address public wallet = 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18;
address payable public receiver;  // Can receive ETH

// address members:
wallet.balance;           // ETH balance in wei
payable(wallet).transfer(amount);  // Send ETH (reverts on failure)
payable(wallet).send(amount);      // Send ETH (returns bool)
wallet.call{value: amount}("");    // Low-level call (recommended)
```

---

## Variables and Storage

### Storage Locations

Solidity has three data locations:

| Location | Persistence | Gas Cost | Use Case |
|:---------|:------------|:---------|:---------|
| **storage** | Permanent (on-chain) | Expensive | State variables |
| **memory** | Temporary (function scope) | Moderate | Function parameters, local vars |
| **calldata** | Read-only, temporary | Cheapest | External function inputs |

### State Variables

```solidity
contract Example {
    // Stored permanently on the blockchain
    uint256 public count;                    // Slot 0
    address public owner;                    // Slot 1
    mapping(address => uint256) public balances;  // Slot 2 (hash-based)
}
```

### Variable Visibility

| Keyword | Who Can Access |
|:--------|:---------------|
| `public` | Anyone (auto-generates getter) |
| `private` | Only this contract |
| `internal` | This contract + derived contracts |

> **Note**: `private` does NOT mean the data is hidden. All blockchain data is publicly visible. `private` only restricts Solidity-level access.

### Constants and Immutables

```solidity
uint256 public constant MAX_SUPPLY = 1000000;  // Set at compile time, no storage slot
uint256 public immutable deployTimestamp;        // Set once in constructor, no storage slot

constructor() {
    deployTimestamp = block.timestamp;  // Can only be set here
}
```

---

## Functions

### Function Syntax

```solidity
function functionName(uint256 param1, string memory param2)
    public          // Visibility
    payable         // State mutability
    onlyOwner       // Modifier
    returns (bool)  // Return type
{
    // Function body
    return true;
}
```

### Visibility Specifiers

| Keyword | Access Level |
|:--------|:-------------|
| `external` | Only callable from outside (most gas-efficient for external calls) |
| `public` | Callable internally and externally |
| `internal` | Only this contract and derived contracts |
| `private` | Only this contract |

### State Mutability

| Keyword | Can Read State? | Can Modify State? | Can Receive ETH? |
|:--------|:----------------|:-------------------|:------------------|
| (none) | Yes | Yes | No |
| `view` | Yes | No | No |
| `pure` | No | No | No |
| `payable` | Yes | Yes | Yes |

### Special Functions

```solidity
// Constructor: Runs once at deployment
constructor(uint256 initialValue) {
    owner = msg.sender;
}

// Receive: Called when ETH is sent with no data
receive() external payable {
    // Handle plain ETH transfers
}

// Fallback: Called when no function matches or ETH sent with data
fallback() external payable {
    // Handle unknown function calls
}
```

---

## Modifiers

Modifiers add preconditions to functions:

```solidity
modifier onlyOwner() {
    require(msg.sender == owner, "Not the owner");
    _;  // This is where the function body gets inserted
}

modifier validAmount(uint256 amount) {
    require(amount > 0, "Amount must be > 0");
    _;
}

// Usage: modifiers run in order, left to right
function withdraw(uint256 amount) external onlyOwner validAmount(amount) {
    // This code runs after both modifier checks pass
}
```

### Common Modifier Patterns

```solidity
modifier nonReentrant() {
    require(!locked, "Reentrant call");
    locked = true;
    _;
    locked = false;
}

modifier whenNotPaused() {
    require(!paused, "Contract is paused");
    _;
}
```

---

## Events

Events are the primary mechanism for off-chain logging and indexing:

```solidity
// Declaration
event Transfer(
    address indexed from,   // indexed: searchable in logs
    address indexed to,     // indexed: searchable in logs
    uint256 value           // non-indexed: stored in data
);

// Emission
function transfer(address to, uint256 amount) external {
    emit Transfer(msg.sender, to, amount);
}
```

**Key points**:
- Up to 3 `indexed` parameters per event (stored as topics)
- Events cost gas to emit but are much cheaper than storage
- Events CANNOT be read by smart contracts (only off-chain tools)
- Indexed parameters enable filtering (e.g., "show all transfers FROM address X")

---

## Error Handling

### require (Legacy -- Still Widely Used)

```solidity
require(msg.sender == owner, "Only the owner can call this");
require(balance >= amount, "Insufficient balance");
```

### Custom Errors (Recommended in 0.8.x)

Custom errors are more gas-efficient than string-based require messages:

```solidity
// Declaration
error InsufficientBalance(uint256 available, uint256 required);
error Unauthorized(address caller);

// Usage
function withdraw(uint256 amount) external {
    if (msg.sender != owner) revert Unauthorized(msg.sender);
    if (balance < amount) revert InsufficientBalance(balance, amount);
}
```

**Gas savings**: Custom errors save ~50+ gas per revert compared to `require` with strings.

### assert

```solidity
// Use for invariant checking (should NEVER fail in correct code)
assert(totalSupply == sumOfAllBalances);
```

### try/catch

```solidity
try otherContract.someFunction() returns (uint256 result) {
    // Success
} catch Error(string memory reason) {
    // Revert with reason string
} catch (bytes memory lowLevelData) {
    // Low-level revert
}
```

---

## Control Structures

```solidity
// If / else
if (x > 10) {
    // ...
} else if (x > 5) {
    // ...
} else {
    // ...
}

// For loop (be careful with gas in unbounded loops!)
for (uint256 i = 0; i < array.length; i++) {
    // Process array[i]
}

// While loop
while (condition) {
    // ...
}

// Ternary operator
uint256 max = (a > b) ? a : b;
```

> **Warning**: Unbounded loops can cause transactions to exceed the block gas limit. Always set a maximum iteration count or use pagination.

---

## Mappings and Arrays

### Mappings

```solidity
// Simple mapping
mapping(address => uint256) public balances;

// Nested mapping
mapping(address => mapping(address => uint256)) public allowances;

// Usage
balances[msg.sender] = 100;
uint256 bal = balances[someAddress];  // Returns 0 if not set
```

**Mapping properties**:
- Cannot be iterated (no `.length`, no `for` loop)
- All keys map to a value (unset keys return the type's default)
- Cannot be passed as function parameters in external calls

### Arrays

```solidity
// Dynamic array
uint256[] public numbers;
numbers.push(42);          // Add element
numbers.pop();             // Remove last element
uint256 len = numbers.length;
delete numbers[0];         // Sets to 0, does NOT remove

// Fixed array
uint256[5] public fixed;
```

---

## Structs and Enums

### Structs

```solidity
struct Proposal {
    string name;
    uint256 voteCount;
    address proposer;
    bool executed;
}

// Usage
Proposal memory newProposal = Proposal({
    name: "Fund Development",
    voteCount: 0,
    proposer: msg.sender,
    executed: false
});

// Array of structs
Proposal[] public proposals;
proposals.push(newProposal);
```

### Enums

```solidity
enum OrderStatus {
    Pending,    // 0
    Active,     // 1
    Completed,  // 2
    Cancelled   // 3
}

OrderStatus public status = OrderStatus.Pending;

// Comparison
if (status == OrderStatus.Active) { /* ... */ }
```

---

## Inheritance

```solidity
contract Ownable {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
}

// Single inheritance
contract Token is Ownable {
    function mint() external onlyOwner {
        // Can use onlyOwner from Ownable
    }
}

// Multiple inheritance
contract GovToken is Ownable, Pausable, ERC20 {
    // Inherits from all three
}
```

### Virtual and Override

```solidity
contract Base {
    function greet() public virtual returns (string memory) {
        return "Hello from Base";
    }
}

contract Child is Base {
    function greet() public override returns (string memory) {
        return "Hello from Child";
    }
}
```

---

## Interfaces

Interfaces define a contract's external API without implementation:

```solidity
interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

// Usage: interact with any ERC-20 contract
IERC20 token = IERC20(tokenAddress);
token.transfer(recipient, amount);
```

---

## Security Patterns

### 1. Checks-Effects-Interactions

Always follow this order:
1. **Checks**: Validate conditions (require/revert)
2. **Effects**: Update state variables
3. **Interactions**: Make external calls

```solidity
function withdraw(uint256 amount) external {
    // CHECK
    require(balances[msg.sender] >= amount, "Insufficient");

    // EFFECT (update state BEFORE external call)
    balances[msg.sender] -= amount;

    // INTERACTION (external call last)
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

### 2. Reentrancy Guard

```solidity
bool private locked;

modifier nonReentrant() {
    require(!locked, "Reentrant");
    locked = true;
    _;
    locked = false;
}
```

### 3. Access Control

```solidity
modifier onlyOwner() {
    require(msg.sender == owner, "Unauthorized");
    _;
}

modifier onlyRole(bytes32 role) {
    require(hasRole[role][msg.sender], "Missing role");
    _;
}
```

### 4. Pull Payment Pattern

Instead of pushing payments, let recipients withdraw:

```solidity
mapping(address => uint256) public pendingWithdrawals;

function withdraw() external {
    uint256 amount = pendingWithdrawals[msg.sender];
    pendingWithdrawals[msg.sender] = 0;
    payable(msg.sender).transfer(amount);
}
```

---

## Gas Optimization Tips

1. **Use `uint256`** instead of smaller types unless packing struct slots
2. **Use `calldata`** for read-only external function parameters
3. **Use custom errors** instead of `require` with string messages
4. **Cache storage reads** in local variables
5. **Use `unchecked`** blocks where overflow is impossible
6. **Pack struct variables** to minimize storage slots
7. **Use events** instead of storage for data only needed off-chain
8. **Short-circuit conditions** -- put cheaper checks first
9. **Use `immutable` and `constant`** for values that never change
10. **Minimize on-chain storage** -- use IPFS/Arweave for large data

```solidity
// Gas optimization example: caching storage reads
function process(uint256[] calldata items) external {
    uint256 cachedLength = items.length;  // Cache to avoid repeated SLOAD
    uint256 cachedBalance = balances[msg.sender];

    for (uint256 i = 0; i < cachedLength;) {
        cachedBalance += items[i];
        unchecked { ++i; }  // Safe: i < cachedLength prevents overflow
    }

    balances[msg.sender] = cachedBalance;
}
```

---

## Common Pitfalls

### 1. Floating Pragma

```solidity
// Bad: could compile with buggy version
pragma solidity ^0.8.0;

// Good: specific version
pragma solidity 0.8.19;
```

### 2. Reentrancy

Always update state before external calls. Use a reentrancy guard for extra safety.

### 3. Integer Overflow (Pre-0.8.x)

Solidity 0.8.x has built-in overflow checks. In older versions, use SafeMath.

### 4. Unbounded Loops

Never iterate over an unbounded array in a transaction -- it may exceed the gas limit.

### 5. tx.origin vs msg.sender

```solidity
// Bad: vulnerable to phishing attacks
require(tx.origin == owner);

// Good: checks the direct caller
require(msg.sender == owner);
```

### 6. Block Timestamp Manipulation

Miners can manipulate `block.timestamp` by ~15 seconds. Do not use it for precision timing.

### 7. Denial of Service

A contract that sends ETH to an address that reverts can block the entire function. Use the pull payment pattern.

---

## Further Reading

- [Solidity Documentation](https://docs.soliditylang.org/)
- [Solidity by Example](https://solidity-by-example.org/)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)
- [Smart Contract Security Best Practices](https://consensys.github.io/smart-contract-best-practices/)
