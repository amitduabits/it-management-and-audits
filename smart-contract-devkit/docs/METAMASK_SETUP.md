# MetaMask Setup and Sepolia Faucet Guide

This guide walks you through installing MetaMask, configuring it for local development and the Sepolia testnet, and obtaining test ETH from faucets.

---

## Table of Contents

1. [What is MetaMask?](#what-is-metamask)
2. [Installing MetaMask](#installing-metamask)
3. [Creating a Wallet](#creating-a-wallet)
4. [Understanding the Interface](#understanding-the-interface)
5. [Adding the Sepolia Testnet](#adding-the-sepolia-testnet)
6. [Adding the Local Hardhat Network](#adding-the-local-hardhat-network)
7. [Getting Sepolia Test ETH](#getting-sepolia-test-eth)
8. [Importing Hardhat Accounts](#importing-hardhat-accounts)
9. [Adding Custom Tokens](#adding-custom-tokens)
10. [Security Best Practices](#security-best-practices)
11. [Common Issues and Fixes](#common-issues-and-fixes)

---

## What is MetaMask?

MetaMask is a cryptocurrency wallet and gateway to blockchain applications. It:

- Stores your private keys securely in your browser
- Signs transactions on your behalf
- Connects your browser to Ethereum and EVM-compatible networks
- Manages multiple accounts and networks

MetaMask is available as a **browser extension** (Chrome, Firefox, Brave, Edge) and as a **mobile app** (iOS, Android).

---

## Installing MetaMask

### Browser Extension (Recommended for Development)

1. Visit [metamask.io](https://metamask.io/)
2. Click **Download** and select your browser
3. You will be redirected to your browser's extension store
4. Click **Add to Chrome** (or your browser equivalent)
5. Confirm the installation

The MetaMask fox icon will appear in your browser toolbar.

> **Important**: Only install MetaMask from the official website or your browser's official extension store. Never install from third-party sources.

---

## Creating a Wallet

### First-Time Setup

1. Click the MetaMask icon in your browser toolbar
2. Click **Create a new wallet**
3. Read and accept the terms
4. Create a strong **password** (this is for local encryption, not your blockchain account)
5. MetaMask will display your **Secret Recovery Phrase** (12 words)

### Securing Your Recovery Phrase

Your Secret Recovery Phrase is the master key to ALL accounts in your wallet.

**Critical security steps:**

- Write it down on paper (not digitally)
- Store it in a safe, secure location
- NEVER share it with anyone
- NEVER enter it on any website
- NEVER store it in a text file, email, or cloud storage
- Consider using a metal backup (fireproof/waterproof)

> If you lose your recovery phrase, you lose access to your wallet permanently. No one can recover it for you.

### Verify Your Recovery Phrase

MetaMask will ask you to confirm your recovery phrase by selecting the words in the correct order. This ensures you wrote it down correctly.

---

## Understanding the Interface

After setup, the MetaMask interface shows:

```
+---------------------------------------+
|  Network Selector (top)               |
|  [Ethereum Mainnet v]                 |
+---------------------------------------+
|  Account Name                         |
|  0x742d...2bD18                       |
|  Balance: 0 ETH                       |
+---------------------------------------+
|  [Send]  [Swap]  [Bridge]            |
+---------------------------------------+
|  Tokens | NFTs | Activity             |
+---------------------------------------+
```

### Key Sections

| Section | Purpose |
|:--------|:--------|
| **Network Selector** | Switch between Ethereum networks (Mainnet, Sepolia, custom) |
| **Account** | Your wallet address and ETH balance |
| **Send** | Send ETH or tokens to another address |
| **Activity** | Transaction history |
| **Tokens** | List of token balances (ETH + ERC-20 tokens) |

---

## Adding the Sepolia Testnet

Sepolia should be available by default in MetaMask. To enable it:

1. Click the **network selector** at the top of MetaMask
2. Click **Show test networks** (if not visible)
3. Toggle **Show test networks** to ON in Settings > Advanced
4. Select **Sepolia** from the dropdown

### Sepolia Network Details

| Setting | Value |
|:--------|:------|
| Network Name | Sepolia |
| RPC URL | https://sepolia.infura.io/v3/ (or your Alchemy URL) |
| Chain ID | 11155111 |
| Currency Symbol | SepoliaETH |
| Block Explorer | https://sepolia.etherscan.io |

---

## Adding the Local Hardhat Network

To interact with your locally running Hardhat node, add it as a custom network:

### Step 1: Start Hardhat Node

```bash
npx hardhat node
```

### Step 2: Add Network to MetaMask

1. Click the network selector
2. Click **Add network** > **Add a network manually**
3. Enter the following details:

| Setting | Value |
|:--------|:------|
| Network Name | Hardhat Local |
| New RPC URL | http://127.0.0.1:8545 |
| Chain ID | 31337 |
| Currency Symbol | ETH |
| Block Explorer URL | (leave blank) |

4. Click **Save**
5. Select **Hardhat Local** from the network dropdown

---

## Getting Sepolia Test ETH

Test ETH has no real value -- it is free and used only for testing on the Sepolia network.

### Faucet Options

#### Option 1: Alchemy Sepolia Faucet

1. Go to [sepoliafaucet.com](https://sepoliafaucet.com)
2. Sign in with your Alchemy account
3. Enter your wallet address
4. Click **Send Me ETH**
5. Receive 0.5 ETH (amount may vary)

#### Option 2: Chainlink Faucet

1. Go to [faucets.chain.link](https://faucets.chain.link)
2. Connect your wallet or enter your address
3. Select **Sepolia** network
4. Click **Send Request**
5. Wait for the transaction to confirm

#### Option 3: Google Cloud Sepolia Faucet

1. Go to [cloud.google.com/application/web3/faucet](https://cloud.google.com/application/web3/faucet/ethereum/sepolia)
2. Enter your wallet address
3. Complete the verification
4. Receive test ETH

### Checking Your Balance

1. Switch MetaMask to the Sepolia network
2. Your balance should update within 30-60 seconds after the faucet transaction confirms
3. You can also check on [sepolia.etherscan.io](https://sepolia.etherscan.io)

> **Tip**: Faucets often have rate limits (e.g., once per day). If one faucet is empty, try another.

---

## Importing Hardhat Accounts

When you run `npx hardhat node`, it creates 20 pre-funded test accounts. You can import these into MetaMask for local testing.

### Step 1: Get Private Keys

When the Hardhat node starts, it displays accounts like:

```
Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

Account #1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 (10000 ETH)
Private Key: 0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
```

### Step 2: Import into MetaMask

1. Click the account icon (circle) in MetaMask
2. Click **Add account or hardware wallet**
3. Select **Import account**
4. Paste the private key (from the Hardhat node output)
5. Click **Import**
6. Repeat for additional accounts as needed

> **Warning**: These are well-known development keys. NEVER use them on mainnet or store real ETH in these accounts.

---

## Adding Custom Tokens

After deploying the BasicToken contract, you can add it to MetaMask to see your token balance.

### Step 1: Get the Token Contract Address

From the deployment output:
```
BasicToken deployed to: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
```

### Step 2: Add Token in MetaMask

1. Switch to the correct network (Hardhat Local or Sepolia)
2. Scroll down in MetaMask and click **Import tokens**
3. Enter:
   - **Token Contract Address**: `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512`
   - **Token Symbol**: `DKT` (should auto-fill)
   - **Token Decimals**: `18` (should auto-fill)
4. Click **Next**, then **Import**

Your DKT token balance should now appear in MetaMask.

---

## Security Best Practices

### For Development

1. **Use a dedicated development wallet** -- Do NOT use your main wallet with real funds for development
2. **Never hardcode private keys** in source code -- Use `.env` files and `.gitignore`
3. **Clear activity data** regularly when switching between local and testnet to avoid nonce issues

### For Production

1. **Use a hardware wallet** (Ledger, Trezor) for mainnet deployments
2. **Verify contract addresses** before interacting with them
3. **Review transaction details** in MetaMask before signing
4. **Be cautious of phishing** -- Always verify the URL before connecting your wallet
5. **Use separate wallets** for different purposes (development, personal, organization)

### Red Flags to Watch For

- Websites asking for your Secret Recovery Phrase
- Pop-ups asking you to "verify" or "sync" your wallet
- Token approval requests for unlimited amounts from unknown contracts
- DMs claiming to be MetaMask support

---

## Common Issues and Fixes

### Issue: "Nonce too high" or Transaction Stuck

**Cause**: MetaMask's transaction count is out of sync with the local node (happens after restarting `npx hardhat node`).

**Fix**:
1. MetaMask > Settings > Advanced
2. Click **Clear activity tab data**
3. This resets the nonce counter

### Issue: Wrong Network

**Cause**: MetaMask is connected to a different network than your contracts are deployed on.

**Fix**: Check the network selector and switch to the correct network (Hardhat Local for local, Sepolia for testnet).

### Issue: "Internal JSON-RPC error"

**Cause**: Usually means the transaction was reverted by the smart contract.

**Fix**:
- Check if you have sufficient ETH for gas
- Check if the function requires a specific role (owner, etc.)
- Check if the contract state allows the operation

### Issue: MetaMask Not Detecting Local Network

**Cause**: Hardhat node is not running, or the RPC URL is incorrect.

**Fix**:
1. Ensure `npx hardhat node` is running in a terminal
2. Verify the RPC URL is `http://127.0.0.1:8545`
3. Verify the Chain ID is `31337`

### Issue: Token Balance Shows 0

**Cause**: Token is imported on the wrong network or with the wrong address.

**Fix**:
1. Make sure you are on the correct network
2. Verify the token contract address matches your deployment
3. Remove and re-import the token

### Issue: "Chain ID mismatch"

**Cause**: The chain ID in MetaMask does not match the network you are connecting to.

**Fix**:
1. Remove the custom network from MetaMask
2. Re-add it with the correct Chain ID (31337 for Hardhat, 11155111 for Sepolia)
