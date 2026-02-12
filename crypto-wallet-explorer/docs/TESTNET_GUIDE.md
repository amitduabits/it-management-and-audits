# Testnet Guide: Getting Sepolia ETH

> **WARNING**: This guide is for the Sepolia testnet ONLY.
> Testnet ETH has NO real monetary value. The Crypto Wallet Explorer is
> an educational tool and should NEVER be used with real cryptocurrency.

---

## Table of Contents

1. [What Is a Testnet?](#what-is-a-testnet)
2. [Why Sepolia?](#why-sepolia)
3. [Getting Testnet ETH (Faucets)](#getting-testnet-eth-faucets)
4. [Setting Up MetaMask for Sepolia](#setting-up-metamask-for-sepolia)
5. [Verifying Your Testnet Balance](#verifying-your-testnet-balance)
6. [Using Testnet ETH with This Tool](#using-testnet-eth-with-this-tool)
7. [Sepolia Block Explorers](#sepolia-block-explorers)
8. [Troubleshooting](#troubleshooting)
9. [Testnet vs. Mainnet Comparison](#testnet-vs-mainnet-comparison)

---

## What Is a Testnet?

A testnet (test network) is a separate Ethereum blockchain used for
development and testing. It mirrors the mainnet's functionality but
uses tokens that have **no real-world value**.

```
+-------------------+     +-------------------+
|   MAINNET         |     |   TESTNET         |
|                   |     |   (Sepolia)       |
| Real ETH          |     | Test ETH          |
| Real value        |     | No value          |
| Real consequences |     | Safe to experiment|
| Production dApps  |     | Development/testing|
| Chain ID: 1       |     | Chain ID: 11155111|
+-------------------+     +-------------------+
```

### Key Properties of Testnets

- **Free tokens**: ETH is distributed free from "faucets"
- **No value**: Testnet tokens cannot be exchanged for real money
- **Same functionality**: Smart contracts, transactions, and EVM
  behavior are identical to mainnet
- **May be reset**: Testnets can be reset or deprecated
- **Faster block times**: Some testnets have faster block production

---

## Why Sepolia?

Sepolia is the **recommended testnet** for application development as of
2023. It replaced Goerli and Rinkeby.

| Feature | Sepolia | Goerli (deprecated) |
|---------|---------|---------------------|
| Status | Active, recommended | Deprecated (2024) |
| Chain ID | 11155111 | 5 |
| Consensus | Proof of Stake | Proof of Stake |
| Block time | ~12 seconds | ~12 seconds |
| Faucet availability | Good | Limited |
| Long-term support | Yes | No |

### Sepolia Network Details

```
Network Name:    Sepolia
Chain ID:        11155111
Currency Symbol: SepoliaETH (or just ETH on testnet)
Block Explorer:  https://sepolia.etherscan.io
RPC URL:         https://rpc.sepolia.org
                 https://sepolia.infura.io/v3/YOUR_KEY
                 https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY
```

---

## Getting Testnet ETH (Faucets)

Faucets are web services that distribute free testnet ETH. Here are
the most reliable options:

### Faucet Options

#### 1. Alchemy Sepolia Faucet
- **URL**: https://www.alchemy.com/faucets/ethereum-sepolia
- **Amount**: 0.5 SepoliaETH per request
- **Requirements**: Free Alchemy account
- **Cooldown**: 24 hours

#### 2. Infura Sepolia Faucet
- **URL**: https://www.infura.io/faucet/sepolia
- **Amount**: 0.5 SepoliaETH per request
- **Requirements**: Free Infura account
- **Cooldown**: 24 hours

#### 3. Google Cloud Sepolia Faucet
- **URL**: https://cloud.google.com/application/web3/faucet/ethereum/sepolia
- **Amount**: 0.05 SepoliaETH per request
- **Requirements**: Google Cloud account
- **Cooldown**: 24 hours

#### 4. Chainlink Sepolia Faucet
- **URL**: https://faucets.chain.link/sepolia
- **Amount**: 0.1 SepoliaETH per request
- **Requirements**: None (some may require social login)
- **Cooldown**: Varies

### How to Use a Faucet

```
Step 1: Generate an address using the Crypto Wallet Explorer
        $ python -m src.cli generate-wallet

        Your testnet address: 0xYourAddress...

Step 2: Visit one of the faucets listed above

Step 3: Paste your testnet address into the faucet

Step 4: Complete any verification (CAPTCHA, social login)

Step 5: Click "Send" or "Request"

Step 6: Wait for the transaction to confirm (~15-30 seconds)

Step 7: Verify your balance:
        $ python -m src.cli check-balance --address 0xYourAddress
```

### Faucet Tips

- **Be patient**: Faucets may have high demand and slow distribution
- **Try multiple**: If one faucet is empty, try another
- **Don't hoard**: Request only what you need for testing
- **Check cooldowns**: Most faucets limit requests to once per 24 hours
- **Use a real browser**: Some faucets block automated requests

---

## Setting Up MetaMask for Sepolia

While the Crypto Wallet Explorer has its own wallet generation, you
may want MetaMask for a visual interface.

### Adding Sepolia to MetaMask

```
1. Open MetaMask

2. Click the network dropdown (top of window)

3. Click "Show test networks" or "Add network"

4. If Sepolia is not listed, add it manually:
   - Network Name:   Sepolia Test Network
   - RPC URL:        https://rpc.sepolia.org
   - Chain ID:       11155111
   - Currency Symbol: SepoliaETH
   - Block Explorer: https://sepolia.etherscan.io

5. Select "Sepolia Test Network" from the dropdown

6. Your MetaMask is now connected to Sepolia
```

### Important Note

> **NEVER import a private key or mnemonic from the Crypto Wallet Explorer
> into MetaMask or any other wallet for real use.** Our generated keys are
> educational only and should be considered compromised. If you use
> MetaMask with Sepolia, generate a separate wallet within MetaMask itself.

---

## Verifying Your Testnet Balance

### Using the CLI

```bash
# Check ETH balance
python -m src.cli check-balance --address 0xYourAddress

# Check with token balances too
python -m src.cli check-balance --address 0xYourAddress --tokens
```

### Using Etherscan

1. Visit https://sepolia.etherscan.io
2. Enter your address in the search bar
3. View your balance, transactions, and token holdings

### Using Web3.py (Programmatic)

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://rpc.sepolia.org"))
balance = w3.eth.get_balance("0xYourAddress")
print(f"Balance: {w3.from_wei(balance, 'ether')} SepoliaETH")
```

---

## Using Testnet ETH with This Tool

### Sending a Test Transaction

```bash
# 1. Generate a wallet
python -m src.cli generate-wallet
# Note the address and private key

# 2. Get testnet ETH from a faucet (see above)

# 3. Build and sign a transaction
python -m src.cli build-tx \
    --to 0xRecipientAddress \
    --value 0.001 \
    --private-key 0xYourPrivateKey

# 4. Build and actually broadcast
python -m src.cli build-tx \
    --to 0xRecipientAddress \
    --value 0.001 \
    --private-key 0xYourPrivateKey \
    --broadcast
```

### Exploring a Transaction

```bash
# After broadcasting, you'll get a transaction hash
python -m src.cli explore-tx --tx-hash 0xYourTxHash
```

### Exploring Blocks

```bash
# View the latest block
python -m src.cli explore-block

# View the 5 most recent blocks
python -m src.cli explore-block --latest 5

# View a specific block with transactions
python -m src.cli explore-block --block-number 5000000 --show-txs
```

---

## Sepolia Block Explorers

| Explorer | URL |
|----------|-----|
| Etherscan | https://sepolia.etherscan.io |
| Blockscout | https://eth-sepolia.blockscout.com |
| OKLink | https://www.oklink.com/sepolia |

### Using Etherscan

Etherscan provides detailed information about:

- **Addresses**: Balance, transactions, token transfers
- **Transactions**: Status, gas usage, input data, logs
- **Blocks**: Transactions, gas utilization, base fee
- **Contracts**: Source code, ABI, read/write functions

---

## Troubleshooting

### "Transaction Failed"

```
Possible causes:
1. Insufficient balance (not enough SepoliaETH for value + gas)
2. Nonce too low (transaction already mined with this nonce)
3. Gas limit too low (increase --gas-limit)
4. Smart contract reverted (check the contract logic)

Solutions:
- Get more SepoliaETH from a faucet
- Check your nonce with:
  python -m src.cli check-balance --address 0xYourAddress
- Increase gas limit for contract interactions
```

### "API Key Required"

```
The Etherscan API requires an API key for most endpoints.

1. Visit https://etherscan.io/apis
2. Create a free account
3. Generate an API key
4. Set the environment variable:
   export ETHERSCAN_API_KEY=your_key_here
   (or add to .env file)
```

### "RPC Error / Connection Failed"

```
The public Sepolia RPC endpoint may be rate-limited or down.

Solutions:
1. Use Infura:
   export INFURA_PROJECT_ID=your_project_id
   (free at https://infura.io)

2. Use Alchemy:
   Use their Sepolia endpoint

3. Try the public endpoint later:
   https://rpc.sepolia.org
```

### "Faucet Not Working"

```
Faucets may be temporarily empty or rate-limited.

Solutions:
1. Try a different faucet (see list above)
2. Wait for the cooldown period
3. Check if the faucet requires a minimum mainnet balance
4. Try from a different IP address
5. Ensure your address is valid (0x + 40 hex characters)
```

---

## Testnet vs. Mainnet Comparison

```
+-------------------+-------------------+
|     TESTNET       |     MAINNET       |
+-------------------+-------------------+
| Free ETH          | Real ETH ($$$)    |
| No value          | Real value        |
| For development   | For production    |
| Can be reset      | Permanent         |
| Low security      | High security     |
| Few validators    | Many validators   |
| May have bugs     | Battle-tested     |
| Fast iteration    | Careful deployment|
+-------------------+-------------------+

IMPORTANT:
- Code that works on testnet should also work on mainnet
- Gas costs are the same (in terms of gas units)
- Smart contract behavior is identical
- The ONLY difference is the economic value of ETH
```

### When to Move to Mainnet

This educational tool should NEVER be used on mainnet. However,
when developing real applications:

1. Develop and test thoroughly on Sepolia
2. Audit your smart contracts
3. Test with small amounts on mainnet first
4. Use proper security practices (hardware wallets, multi-sig)
5. Monitor your contracts after deployment

---

> **FINAL REMINDER**: The Crypto Wallet Explorer is for educational use only.
> Testnet ETH has no real value. NEVER use generated wallets for real funds.
> Always use established, audited software for real cryptocurrency.
