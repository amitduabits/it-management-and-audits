# Blockchain and Ethereum Primer

## Table of Contents

1. [What is a Blockchain?](#what-is-a-blockchain)
2. [How Blocks Work](#how-blocks-work)
3. [Consensus Mechanisms](#consensus-mechanisms)
4. [Introduction to Ethereum](#introduction-to-ethereum)
5. [Ethereum Virtual Machine (EVM)](#ethereum-virtual-machine-evm)
6. [Accounts and Addresses](#accounts-and-addresses)
7. [Gas and Transaction Fees](#gas-and-transaction-fees)
8. [Smart Contracts](#smart-contracts)
9. [Tokens and Standards](#tokens-and-standards)
10. [Testnets vs. Mainnet](#testnets-vs-mainnet)
11. [Key Terminology](#key-terminology)

---

## What is a Blockchain?

A blockchain is a **distributed, immutable ledger** that records transactions across a network of computers (nodes). Each node maintains a complete copy of the ledger, and consensus algorithms ensure that all copies agree.

**Key properties:**

- **Decentralization**: No single entity controls the network. Thousands of nodes independently validate transactions.
- **Immutability**: Once data is recorded in a block, it cannot be altered without re-mining every subsequent block -- a computationally infeasible task.
- **Transparency**: All transactions are publicly visible and verifiable by anyone.
- **Trustlessness**: Participants do not need to trust each other or a central authority. Trust is placed in the protocol and cryptographic proofs.

**Real-world analogy**: Imagine a shared Google Sheet that thousands of people maintain simultaneously. Everyone can see every entry. Once an entry is recorded, no individual can change it without everyone else noticing.

---

## How Blocks Work

A blockchain is literally a chain of blocks. Each block contains:

| Component        | Description |
|:-----------------|:------------|
| **Block Header** | Metadata including timestamp, block number, and difficulty |
| **Previous Hash** | A cryptographic hash of the preceding block, forming the "chain" |
| **Transactions** | A list of validated transactions included in this block |
| **Nonce**        | A number used in mining to find a valid block hash |
| **Merkle Root**  | A hash tree of all transactions, enabling efficient verification |

### Block Lifecycle

1. Users submit transactions to the network
2. Nodes collect pending transactions into a **mempool**
3. A validator (or miner) selects transactions and assembles a candidate block
4. The block is validated through a consensus mechanism
5. Valid blocks are appended to the chain and propagated to all nodes
6. Transactions in the block are now considered **confirmed**

### Confirmations

The more blocks mined after your transaction's block, the more "confirmations" it has. More confirmations = higher security. Most applications consider 12+ confirmations as final on Ethereum.

---

## Consensus Mechanisms

### Proof of Work (PoW) -- Historical

Bitcoin and early Ethereum used PoW, where miners compete to solve a cryptographic puzzle. The first to solve it gets to add the block and earns a reward. This requires enormous computational power and energy.

### Proof of Stake (PoS) -- Current Ethereum

Since September 2022 ("The Merge"), Ethereum uses Proof of Stake:

- **Validators** lock up (stake) 32 ETH as collateral
- Validators are randomly selected to propose and attest to blocks
- Honest behavior is rewarded; malicious behavior results in **slashing** (loss of staked ETH)
- Energy consumption reduced by ~99.95% compared to PoW

### Why PoS Matters for Developers

- Faster block times (~12 seconds per slot)
- More predictable finality
- Lower environmental impact
- Same developer experience -- smart contracts work identically

---

## Introduction to Ethereum

Ethereum is a **programmable blockchain**. While Bitcoin primarily handles value transfers, Ethereum allows developers to deploy and execute arbitrary code (smart contracts) on the blockchain.

**Founded**: Proposed by Vitalik Buterin in 2013, launched July 2015.

**Native Currency**: Ether (ETH), used to pay for computation (gas fees).

### Key Innovations

1. **Smart Contracts**: Self-executing programs stored on-chain
2. **EVM**: A Turing-complete virtual machine that runs contract bytecode
3. **Token Standards**: ERC-20 (fungible), ERC-721 (NFT), ERC-1155 (multi-token)
4. **DeFi**: Decentralized finance protocols built on Ethereum
5. **DAOs**: Decentralized autonomous organizations governed by smart contracts

---

## Ethereum Virtual Machine (EVM)

The EVM is the runtime environment for smart contracts on Ethereum.

### How it Works

1. You write a smart contract in **Solidity** (high-level language)
2. The Solidity compiler (`solc`) compiles it to **EVM bytecode**
3. The bytecode is deployed to the blockchain via a transaction
4. When someone calls your contract, every node on the network executes the bytecode
5. The result is verified by consensus and the state is updated globally

### Important Properties

- **Deterministic**: The same input always produces the same output on every node
- **Isolated (Sandboxed)**: Contracts cannot access the filesystem, network, or other processes
- **Stack-Based**: The EVM uses a stack machine architecture with a 1024-depth stack
- **World State**: All contract storage and balances form the "world state," which every block updates

---

## Accounts and Addresses

Ethereum has two types of accounts:

### Externally Owned Accounts (EOAs)

- Controlled by private keys (held by humans or hardware wallets)
- Can initiate transactions
- Have an ETH balance
- Address format: `0x` followed by 40 hexadecimal characters (e.g., `0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18`)

### Contract Accounts

- Controlled by their deployed code (no private key)
- Cannot initiate transactions (only respond to calls)
- Have an ETH balance AND storage
- Created when a smart contract is deployed

### How Addresses are Derived

EOA addresses are derived from the public key:
1. Generate a random 256-bit **private key**
2. Derive the **public key** using elliptic curve cryptography (secp256k1)
3. Hash the public key with **Keccak-256**
4. Take the last 20 bytes as the **address**

> **Security**: NEVER share your private key. Anyone with your private key has full control of your account.

---

## Gas and Transaction Fees

Every operation on Ethereum costs **gas**. Gas is a unit measuring computational effort.

### Gas Formula

```
Transaction Fee = Gas Used x Gas Price (in Gwei)
```

- **Gas Used**: The actual computation consumed (e.g., a simple transfer uses 21,000 gas)
- **Gas Price**: How much you are willing to pay per unit of gas (in Gwei; 1 Gwei = 0.000000001 ETH)

### EIP-1559 Fee Structure (Current)

Since August 2021, Ethereum uses a two-part fee:

- **Base Fee**: Algorithmically determined; burned (destroyed) after use
- **Priority Fee (Tip)**: Goes to the validator as an incentive for inclusion

```
Max Fee = Base Fee + Priority Fee
Total Cost = Gas Used x (Base Fee + Priority Fee)
```

### Common Gas Costs

| Operation | Approximate Gas |
|:----------|:----------------|
| ETH transfer | 21,000 |
| ERC-20 transfer | ~65,000 |
| ERC-20 approve | ~46,000 |
| Contract deployment | 100,000 - 5,000,000+ |
| NFT mint | ~100,000 - 200,000 |

### Tips for Reducing Gas

1. Use `calldata` instead of `memory` for read-only function parameters
2. Pack storage variables (multiple `uint128` in one slot vs. separate `uint256`)
3. Use `custom errors` instead of `require` with string messages
4. Minimize on-chain storage (store data off-chain when possible, e.g., IPFS)
5. Use events for data that does not need to be read by other contracts

---

## Smart Contracts

A smart contract is a program stored on the blockchain that automatically executes when predetermined conditions are met.

### Characteristics

- **Autonomous**: Once deployed, no one can stop them (unless the code has a self-destruct or pause mechanism)
- **Transparent**: The bytecode is public and verifiable
- **Irreversible**: Transactions executed by contracts cannot be undone
- **Composable**: Contracts can call other contracts, enabling complex systems

### Lifecycle

1. **Write**: Author the contract in Solidity
2. **Compile**: Convert to EVM bytecode using the Solidity compiler
3. **Test**: Run comprehensive tests on a local blockchain
4. **Deploy**: Send a deployment transaction to the network
5. **Verify**: Publish source code on Etherscan for transparency
6. **Interact**: Users call contract functions via transactions or view calls

---

## Tokens and Standards

### ERC-20: Fungible Tokens

The most widely adopted token standard. Every token is identical and interchangeable (like currency).

**Required Functions:**
- `totalSupply()`, `balanceOf()`, `transfer()`, `approve()`, `allowance()`, `transferFrom()`

**Examples**: USDC, DAI, LINK, UNI

### ERC-721: Non-Fungible Tokens (NFTs)

Each token is unique and has a distinct ID. Used for digital art, collectibles, property deeds, etc.

**Required Functions:**
- `balanceOf()`, `ownerOf()`, `transferFrom()`, `approve()`, `setApprovalForAll()`

**Examples**: CryptoPunks, Bored Ape Yacht Club, ENS Names

### ERC-1155: Multi-Token Standard

Allows a single contract to manage both fungible and non-fungible tokens, reducing gas costs for batch operations.

---

## Testnets vs. Mainnet

| Feature | Testnet | Mainnet |
|:--------|:--------|:--------|
| Real money? | No (test ETH) | Yes (real ETH) |
| Purpose | Development & testing | Production |
| Free to use? | Yes (faucets) | No (gas fees) |
| Persistence | May be reset | Permanent |

### Active Testnets

- **Sepolia**: Recommended testnet for application developers
- **Holesky**: Used primarily for staking/infrastructure testing

### Getting Test ETH

1. Visit a Sepolia faucet (e.g., `sepoliafaucet.com`, `faucets.chain.link`)
2. Enter your wallet address
3. Receive free test ETH (usually 0.5 - 1 ETH per request)
4. Use this ETH to deploy and interact with contracts on Sepolia

---

## Key Terminology

| Term | Definition |
|:-----|:-----------|
| **ABI** | Application Binary Interface -- a JSON description of a contract's functions and events |
| **Block** | A batch of validated transactions added to the chain |
| **Bytecode** | The compiled binary code that runs on the EVM |
| **dApp** | Decentralized Application -- a frontend connected to smart contracts |
| **DeFi** | Decentralized Finance -- financial services built on blockchain |
| **EOA** | Externally Owned Account -- a regular user wallet |
| **EVM** | Ethereum Virtual Machine -- the runtime for smart contracts |
| **Gas** | Unit measuring computational cost on Ethereum |
| **Gwei** | 0.000000001 ETH (10^-9 ETH); commonly used for gas prices |
| **Hash** | A fixed-length cryptographic fingerprint of data |
| **Mainnet** | The production Ethereum network with real value |
| **Mempool** | The pool of pending, unconfirmed transactions |
| **Nonce** | A counter that prevents transaction replay attacks |
| **Oracle** | A service that provides off-chain data to smart contracts (e.g., Chainlink) |
| **Solidity** | The primary programming language for Ethereum smart contracts |
| **Testnet** | A blockchain network for testing (no real value) |
| **Wei** | The smallest unit of ETH (1 ETH = 10^18 Wei) |

---

## Further Reading

- [Ethereum Whitepaper](https://ethereum.org/en/whitepaper/)
- [Ethereum Yellow Paper](https://ethereum.github.io/yellowpaper/paper.pdf)
- [EIP-1559 Explained](https://eips.ethereum.org/EIPS/eip-1559)
- [Ethereum Developer Documentation](https://ethereum.org/en/developers/)
- [Solidity Documentation](https://docs.soliditylang.org/)
