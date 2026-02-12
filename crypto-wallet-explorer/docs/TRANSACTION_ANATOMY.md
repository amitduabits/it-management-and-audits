# Ethereum Transaction Anatomy

> **WARNING**: This document accompanies an educational tool.
> NEVER use the Crypto Wallet Explorer for real cryptocurrency transactions.
> All examples use Sepolia testnet only. Testnet ETH has NO real value.

---

## Table of Contents

1. [What Is a Transaction?](#what-is-a-transaction)
2. [Transaction Types](#transaction-types)
3. [Transaction Fields](#transaction-fields)
4. [EIP-1559 Fee Model](#eip-1559-fee-model)
5. [Transaction Lifecycle](#transaction-lifecycle)
6. [Transaction Signing (ECDSA)](#transaction-signing-ecdsa)
7. [RLP Encoding](#rlp-encoding)
8. [Gas Mechanics](#gas-mechanics)
9. [Contract Interactions](#contract-interactions)
10. [Reading a Raw Transaction](#reading-a-raw-transaction)

---

## What Is a Transaction?

An Ethereum transaction is a **cryptographically signed instruction** from
an externally owned account (EOA) to the Ethereum network. It is the ONLY
way to change state on the Ethereum blockchain.

```
+-------------------+                    +-------------------+
|   Sender (EOA)    |                    |   Ethereum        |
|                   |    Transaction     |   Network         |
| Has private key   |------------------->|                   |
| Signs transaction |                    | Validates & mines |
| Pays gas fees     |                    | Updates state     |
+-------------------+                    +-------------------+
```

Transactions can:
- Transfer ETH from one account to another
- Deploy a new smart contract
- Call a function on an existing smart contract
- Do nothing (zero-value transaction with no data)

---

## Transaction Types

Ethereum supports three transaction types:

### Type 0: Legacy Transaction

The original transaction format before EIP-2930 and EIP-1559.

```
{
    nonce:    uint64,    // Sender's transaction count
    gasPrice: uint256,   // Price per gas unit (wei)
    gasLimit: uint64,    // Maximum gas units
    to:       address,   // Recipient (or null for contract creation)
    value:    uint256,   // Amount of ETH to transfer (wei)
    data:     bytes,     // Calldata for contract interaction
    v:        uint256,   // ECDSA recovery parameter
    r:        uint256,   // ECDSA signature component
    s:        uint256    // ECDSA signature component
}
```

### Type 1: EIP-2930 (Access List Transaction)

Introduced to specify storage slots and addresses that the transaction
will access, reducing gas costs for cross-contract calls.

```
{
    chainId:    uint256,
    nonce:      uint64,
    gasPrice:   uint256,
    gasLimit:   uint64,
    to:         address,
    value:      uint256,
    data:       bytes,
    accessList: [{address, storageKeys[]}],  // NEW
    v, r, s
}
```

### Type 2: EIP-1559 (Recommended)

The modern fee model with base fee + priority fee (tip).

```
{
    chainId:             uint256,
    nonce:               uint64,
    maxPriorityFeePerGas: uint256,  // Tip to validator
    maxFeePerGas:        uint256,   // Maximum total fee
    gasLimit:            uint64,
    to:                  address,
    value:               uint256,
    data:                bytes,
    accessList:          [{address, storageKeys[]}],
    v, r, s
}
```

---

## Transaction Fields

### nonce

```
Purpose: Prevent replay attacks and ensure transaction ordering
Type:    uint64 (unsigned 64-bit integer)
Example: 42

The nonce is the number of transactions sent from the sender's address.
It starts at 0 and increments by 1 for each transaction.

Address: 0xAbC...
    Nonce 0: First transaction ever sent
    Nonce 1: Second transaction
    Nonce 2: Third transaction
    ...

Nonce gaps prevent execution:
    Nonce 0: Confirmed
    Nonce 1: Confirmed
    Nonce 2: MISSING  <-- Nonce 3 cannot be mined until 2 exists
    Nonce 3: Pending (stuck)
```

### to

```
Purpose: Specify the recipient
Type:    20-byte address (or empty for contract creation)
Example: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

Three cases:
1. ETH transfer:     to = recipient address
2. Contract call:    to = contract address
3. Contract deploy:  to = empty/null (the contract gets a new address)
```

### value

```
Purpose: Amount of ETH to transfer
Type:    uint256 (in wei, smallest unit)
Example: 1000000000000000000 (= 1 ETH)

Unit conversions:
    1 ETH   = 1,000,000,000 Gwei
    1 ETH   = 1,000,000,000,000,000,000 Wei
    1 Gwei  = 1,000,000,000 Wei
```

### data (input)

```
Purpose: Calldata for contract interactions
Type:    bytes (variable length)
Example: 0xa9059cbb000000000000000000000000recipient...amount...

For simple ETH transfers: empty (0x)
For contract calls: ABI-encoded function call

Structure of calldata:
+----------+----------------------------+
| Bytes    | Content                    |
+----------+----------------------------+
| 0-3      | Function selector          |
|          | (first 4 bytes of          |
|          |  keccak256(signature))     |
+----------+----------------------------+
| 4-35     | Parameter 1 (32 bytes)     |
+----------+----------------------------+
| 36-67    | Parameter 2 (32 bytes)     |
+----------+----------------------------+
| ...      | Additional parameters      |
+----------+----------------------------+

Example: ERC-20 transfer(address, uint256)
    Function selector: 0xa9059cbb
    keccak256("transfer(address,uint256)") -> a9059cbb...

    Parameter 1 (address, left-padded to 32 bytes):
    0x000000000000000000000000d8dA6BF26964aF9D7eEd9e03E53415D37aA96045

    Parameter 2 (uint256, amount in token units):
    0x0000000000000000000000000000000000000000000000000de0b6b3a7640000
    (= 1 * 10^18 = 1 token with 18 decimals)
```

### gasLimit

```
Purpose: Maximum gas units the transaction can consume
Type:    uint64
Example: 21000 (simple ETH transfer)

If the transaction uses less gas, the unused portion is refunded.
If the transaction exceeds the gas limit, it reverts (fails) but
the gas is NOT refunded (the work was done).

Common gas limits:
    Simple ETH transfer:    21,000
    ERC-20 token transfer:  ~65,000
    Uniswap swap:           ~150,000 - 300,000
    Complex DeFi:           ~500,000+
    Contract deployment:    ~1,000,000+
```

---

## EIP-1559 Fee Model

EIP-1559 (London hard fork, August 2021) replaced the simple auction-based
gas price with a more predictable fee structure.

### How It Works

```
+------------------------------------------+
|         Transaction Fee Breakdown        |
+------------------------------------------+

Total Fee = Gas Used * (Base Fee + Priority Fee)

Where:
    Base Fee:     Set by the protocol (burned, not paid to validators)
    Priority Fee: Tip to the validator (incentive for inclusion)

maxFeePerGas:          Maximum you're willing to pay per gas unit
maxPriorityFeePerGas:  Maximum tip per gas unit

Actual fee = min(maxFeePerGas, baseFee + maxPriorityFeePerGas)

+------------------------------------------+
|  Example:                                |
|                                          |
|  maxFeePerGas = 50 Gwei                 |
|  maxPriorityFeePerGas = 2 Gwei          |
|  Current baseFee = 30 Gwei              |
|                                          |
|  Effective fee = 30 + 2 = 32 Gwei       |
|  Refund = 50 - 32 = 18 Gwei/gas         |
|                                          |
|  For 21,000 gas:                         |
|  Fee = 21,000 * 32 Gwei                 |
|      = 672,000 Gwei                      |
|      = 0.000672 ETH                      |
+------------------------------------------+
```

### Base Fee Adjustment

The base fee adjusts each block based on gas utilization:

```
Target: 50% gas utilization (15M gas of 30M limit)

Block N:   Gas used = 30M (100%) --> Base fee INCREASES by 12.5%
Block N+1: Gas used = 25M (83%)  --> Base fee INCREASES
Block N+2: Gas used = 15M (50%)  --> Base fee STAYS THE SAME
Block N+3: Gas used = 10M (33%)  --> Base fee DECREASES
Block N+4: Gas used = 0   (0%)  --> Base fee DECREASES by 12.5%

This creates a self-adjusting mechanism:
    High demand --> Higher base fee --> Users wait or pay more
    Low demand  --> Lower base fee  --> Cheaper transactions
```

### Fee Burning (EIP-1559)

The base fee is **burned** (destroyed), not paid to validators:

```
Transaction fee = base_fee + priority_fee

    base_fee:     BURNED (removed from circulation)
    priority_fee: PAID to the block proposer (validator)

This makes ETH potentially deflationary:
    If burn rate > issuance rate --> ETH supply decreases over time
```

---

## Transaction Lifecycle

```
[1] CONSTRUCTION
    Build the transaction object with all required fields

[2] SIGNING
    Sign with sender's private key using ECDSA
    +---> Produces v, r, s signature components

[3] RLP ENCODING
    Serialize the signed transaction using RLP encoding
    +---> Produces the raw transaction bytes

[4] BROADCASTING
    Send the raw transaction to an Ethereum node
    +---> Node validates and adds to mempool (transaction pool)

[5] MEMPOOL
    Transaction sits in the mempool waiting for inclusion
    +---> Validators select transactions (highest priority fee first)

[6] INCLUSION
    A validator includes the transaction in a block
    +---> Transaction is executed by the EVM

[7] EXECUTION
    The EVM processes the transaction
    +---> State changes are applied
    +---> Gas is consumed
    +---> Events/logs are emitted

[8] CONFIRMATION
    The block is added to the chain
    +---> Transaction has 1 confirmation
    +---> Each subsequent block adds 1 more confirmation
    +---> After ~12-15 confirmations, considered finalized

[9] FINALITY (post-Merge)
    After ~12.8 minutes (2 epochs), the block is finalized
    +---> Cannot be reverted without exceptional circumstances
```

---

## Transaction Signing (ECDSA)

Ethereum uses the **Elliptic Curve Digital Signature Algorithm (ECDSA)**
with the **secp256k1** curve to sign transactions.

```
Signing Process:
                              +----------------+
    Transaction data -------->|                |
                              |  Keccak-256    |----> Message hash (32 bytes)
    (RLP-encoded, unsigned)   |                |
                              +----------------+
                                     |
                                     v
                              +----------------+
    Private key ------------->|                |
                              |  ECDSA Sign    |----> (v, r, s)
    (32 bytes)                |  (secp256k1)   |
                              +----------------+

Verification Process:
                              +----------------+
    Message hash ------------>|                |
                              |  ECDSA Recover |----> Public key
    (v, r, s) --------------->|  (secp256k1)   |----> Address
                              +----------------+

The signature (v, r, s) proves:
    1. The sender owns the private key for the from address
    2. The transaction data has not been tampered with
    3. The transaction was authorized by the account owner
```

### Signature Components

- **r**: The x-coordinate of a point on the elliptic curve (32 bytes)
- **s**: The signature proof value (32 bytes)
- **v**: The recovery ID (1 byte) + chain_id encoding (EIP-155)
  - Pre-EIP-155: v = 27 or 28
  - Post-EIP-155: v = chain_id * 2 + 35 or chain_id * 2 + 36

---

## RLP Encoding

**Recursive Length Prefix (RLP)** is Ethereum's serialization format for
encoding transaction data.

```
RLP Encoding Rules:
    1. Single byte [0x00, 0x7f]: encoded as itself
    2. String 0-55 bytes: 0x80 + length, then string
    3. String > 55 bytes: 0xb7 + length-of-length, length, then string
    4. List 0-55 bytes total: 0xc0 + total length, then items
    5. List > 55 bytes: 0xf7 + length-of-length, length, then items

Example: Encoding a simple ETH transfer
    [
        nonce: 0x09,
        gasPrice: 0x04a817c800,     (20 Gwei)
        gasLimit: 0x5208,            (21000)
        to: 0xd8dA6BF2...96045,
        value: 0x0de0b6b3a7640000,  (1 ETH)
        data: 0x
    ]
```

---

## Gas Mechanics

### What Is Gas?

Gas is the unit of computational work on Ethereum. Every operation in the
EVM has a defined gas cost:

```
Operation                    Gas Cost
---------                    --------
ADD (addition)               3
MUL (multiplication)         5
SUB (subtraction)            3
SLOAD (storage read)         2,100
SSTORE (storage write)       5,000 - 20,000
CALL (external call)         2,600+
CREATE (deploy contract)     32,000+
KECCAK256 (hash)             30 + 6/word
LOG0 (emit event)            375+

Base transaction cost:       21,000
    (the minimum for any transaction)
```

### Gas Refund

Certain operations provide gas refunds:
- Clearing storage (setting a non-zero slot to zero): refund
- Self-destruct (deprecated): previously provided refund

### Out-of-Gas

```
Transaction with gasLimit = 21,000

Step 1: Base cost              -21,000 gas
Step 2: No more operations     Total used: 21,000

If gasLimit was 20,000:
Step 1: Base cost              -21,000 gas
ERROR: Out of gas!
    --> Transaction REVERTS
    --> State changes UNDONE
    --> Gas is NOT refunded (work was performed)
    --> Value transfer DOES NOT happen
```

---

## Contract Interactions

### Function Selectors

When calling a smart contract function, the first 4 bytes of the calldata
identify which function to call:

```
Function: transfer(address recipient, uint256 amount)

1. Compute function signature:
   "transfer(address,uint256)"

2. Hash with Keccak-256:
   keccak256("transfer(address,uint256)")
   = a9059cbb2ab09eb219583f4a59a5d0623ade346d962bcd4e46b11da047c9049b

3. Take first 4 bytes:
   Function selector = 0xa9059cbb

Common ERC-20 function selectors:
    0xa9059cbb  transfer(address,uint256)
    0x23b872dd  transferFrom(address,address,uint256)
    0x095ea7b3  approve(address,uint256)
    0x70a08231  balanceOf(address)
    0x18160ddd  totalSupply()
    0x313ce567  decimals()
    0x06fdde03  name()
    0x95d89b41  symbol()
```

### ABI Encoding

Parameters are ABI-encoded as 32-byte words:

```
transfer(0xRecipient, 1000000000000000000)

Calldata:
0xa9059cbb                                                           <- selector
000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa96045       <- address (left-padded)
0000000000000000000000000000000000000000000000000de0b6b3a7640000       <- uint256 (1 ETH worth of tokens)
```

---

## Reading a Raw Transaction

Here is how to interpret a raw signed EIP-1559 transaction:

```
Raw transaction (hex):
02f8720b8202...

Breakdown:
02              Type: 2 (EIP-1559)
f872            RLP: list, 114 bytes total
  0b            chainId: 11 (0x0b = 11155111 would be longer)
  82 0200       nonce: 512
  85 02540be400 maxPriorityFeePerGas: 10 Gwei
  85 0ba43b7400 maxFeePerGas: 50 Gwei
  82 5208       gasLimit: 21000
  94 d8dA6B...  to: 0xd8dA6BF2... (20 bytes)
  88 0de0...    value: 1 ETH in wei
  80            data: empty
  c0            accessList: empty
  01            v: 1
  a0 abc123...  r: 32 bytes
  a0 def456...  s: 32 bytes
```

---

> **REMINDER**: All examples in this document use testnet addresses and
> transactions. The Crypto Wallet Explorer is for educational purposes only.
> NEVER use it for real cryptocurrency transactions.
