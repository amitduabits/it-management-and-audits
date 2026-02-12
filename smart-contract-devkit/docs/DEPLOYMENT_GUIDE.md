# Deployment Guide

A step-by-step walkthrough for compiling, testing, and deploying the smart contracts included in this toolkit.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Compiling Contracts](#compiling-contracts)
4. [Running Tests](#running-tests)
5. [Local Deployment (Hardhat Node)](#local-deployment-hardhat-node)
6. [Sepolia Testnet Deployment](#sepolia-testnet-deployment)
7. [Contract Verification on Etherscan](#contract-verification-on-etherscan)
8. [Interacting with Deployed Contracts](#interacting-with-deployed-contracts)
9. [Using the Frontend](#using-the-frontend)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| **Node.js** | >= 18.0.0 | JavaScript runtime |
| **npm** | >= 9.0.0 | Package manager (comes with Node.js) |
| **Git** | Any recent | Version control |
| **MetaMask** | Latest | Browser wallet for interacting with dApps |

### Verify Installation

Open a terminal and run:

```bash
node --version    # Should show v18.x.x or higher
npm --version     # Should show 9.x.x or higher
git --version     # Should show git version 2.x.x
```

---

## Installation

### Step 1: Navigate to the Project

```bash
cd smart-contract-devkit
```

### Step 2: Install Dependencies

```bash
npm install
```

This installs all packages defined in `package.json`:
- **hardhat**: Development environment and task runner
- **ethers.js**: Ethereum library for contract interaction
- **chai**: Assertion library for testing
- **dotenv**: Environment variable management
- **hardhat-toolbox**: Bundle of common Hardhat plugins

### Step 3: Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your details:

```env
PRIVATE_KEY=your_wallet_private_key_here
ALCHEMY_API_KEY=your_alchemy_api_key_here
ETHERSCAN_API_KEY=your_etherscan_api_key_here
```

> **Security Warning**: NEVER commit your `.env` file. It is already in `.gitignore`.

---

## Compiling Contracts

```bash
npx hardhat compile
```

**Expected output:**

```
Compiled 5 Solidity files successfully
```

This creates:
- `artifacts/` -- Compiled contract artifacts (ABI + bytecode)
- `cache/` -- Compiler cache for faster recompilation

### Verify Compilation

Check that artifacts were created:

```bash
ls artifacts/contracts/
```

You should see folders for each contract: `SimpleStorage.sol`, `BasicToken.sol`, `Escrow.sol`, `Voting.sol`, `NFTMarketplace.sol`.

---

## Running Tests

### Run All Tests

```bash
npx hardhat test
```

### Run a Specific Test File

```bash
npx hardhat test test/SimpleStorage.test.js
npx hardhat test test/BasicToken.test.js
npx hardhat test test/Escrow.test.js
npx hardhat test test/Voting.test.js
npx hardhat test test/NFTMarketplace.test.js
```

### Run Tests with Gas Reporting

```bash
REPORT_GAS=true npx hardhat test
```

This outputs a table showing gas consumption for each function call.

### Run Tests with Coverage

```bash
npx hardhat coverage
```

This generates a code coverage report showing which lines of Solidity are exercised by tests.

---

## Local Deployment (Hardhat Node)

Local deployment is the fastest way to test your contracts. Hardhat provides a local blockchain with pre-funded accounts.

### Step 1: Start the Local Node

Open a terminal and run:

```bash
npx hardhat node
```

This starts a local JSON-RPC server at `http://127.0.0.1:8545` with 20 pre-funded accounts (10,000 ETH each).

**Keep this terminal running.**

### Step 2: Deploy Contracts

In a **new terminal**:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

**Expected output:**

```
============================================================
Smart Contract Development Kit - Deployment Script
============================================================
Network: localhost

[1/5] Deploying SimpleStorage...
  SimpleStorage deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3

[2/5] Deploying BasicToken...
  BasicToken deployed to: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

[3/5] Deploying Escrow...
  Escrow deployed to: 0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0

[4/5] Deploying Voting...
  Voting deployed to: 0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9

[5/5] Deploying NFTMarketplace...
  NFTMarketplace deployed to: 0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9
```

**Save these addresses** -- you will need them for the interaction script and frontend.

### Step 3: Interact with Contracts

```bash
npx hardhat run scripts/interact.js --network localhost
```

---

## Sepolia Testnet Deployment

### Step 1: Get an Alchemy API Key

1. Go to [alchemy.com](https://www.alchemy.com/) and create a free account
2. Create a new app, select **Ethereum** and **Sepolia**
3. Copy the API key and paste it into your `.env` file as `ALCHEMY_API_KEY`

### Step 2: Get Your Private Key from MetaMask

1. Open MetaMask
2. Click the three dots next to your account name
3. Select **Account Details**
4. Click **Show Private Key**
5. Enter your password and copy the key
6. Paste it into your `.env` file as `PRIVATE_KEY`

> **Security**: This private key controls your wallet. Never share it. Use a dedicated development wallet, not your main wallet.

### Step 3: Get Sepolia Test ETH

You need test ETH to pay for gas. Visit one of these faucets:

- [sepoliafaucet.com](https://sepoliafaucet.com)
- [faucets.chain.link](https://faucets.chain.link)
- [Alchemy Sepolia Faucet](https://sepoliafaucet.com/)

Enter your wallet address and request test ETH. You need at least 0.1 ETH for deployment.

### Step 4: Deploy to Sepolia

```bash
npx hardhat run scripts/deploy.js --network sepolia
```

Deployment will take longer than local (30-60 seconds per contract) as transactions need to be mined on the testnet.

### Step 5: Verify Deployment

After deployment, you can view your contracts on Sepolia Etherscan:

```
https://sepolia.etherscan.io/address/YOUR_CONTRACT_ADDRESS
```

---

## Contract Verification on Etherscan

Verifying your contract on Etherscan makes the source code publicly readable and allows users to interact with it directly through the Etherscan UI.

### Step 1: Get an Etherscan API Key

1. Go to [etherscan.io](https://etherscan.io/) and create an account
2. Navigate to **API Keys** in your profile
3. Create a new API key
4. Add it to your `.env` as `ETHERSCAN_API_KEY`

### Step 2: Verify Each Contract

```bash
# SimpleStorage (constructor arg: 42)
npx hardhat verify --network sepolia CONTRACT_ADDRESS 42

# BasicToken (constructor args: name, symbol, initialSupply, cap)
npx hardhat verify --network sepolia CONTRACT_ADDRESS "DevKit Token" "DKT" 1000000 10000000

# Escrow (no constructor args)
npx hardhat verify --network sepolia CONTRACT_ADDRESS

# NFTMarketplace (constructor args: name, symbol, feeBps)
npx hardhat verify --network sepolia CONTRACT_ADDRESS "DevKit NFT Collection" "DKNFT" 250
```

> Note: The Voting contract has complex constructor arguments. Use a verification script or constructor argument file for it.

---

## Interacting with Deployed Contracts

### Via Script

Update the contract addresses in `scripts/interact.js`, then:

```bash
npx hardhat run scripts/interact.js --network sepolia
```

### Via Hardhat Console

```bash
npx hardhat console --network sepolia
```

Then in the console:

```javascript
const contract = await ethers.getContractAt("SimpleStorage", "0xYOUR_ADDRESS");
const value = await contract.get();
console.log("Current value:", value.toString());

const tx = await contract.set(123);
await tx.wait();
console.log("Value updated!");
```

### Via Frontend

See the [Using the Frontend](#using-the-frontend) section below.

---

## Using the Frontend

### Step 1: Update Contract Addresses

Open `frontend/app.js` and update the `ADDRESSES` object with your deployed contract addresses:

```javascript
const ADDRESSES = {
  SimpleStorage: "0xYOUR_SIMPLE_STORAGE_ADDRESS",
  BasicToken: "0xYOUR_BASIC_TOKEN_ADDRESS",
  Escrow: "0xYOUR_ESCROW_ADDRESS",
  Voting: "0xYOUR_VOTING_ADDRESS",
  NFTMarketplace: "0xYOUR_NFT_MARKETPLACE_ADDRESS",
};
```

### Step 2: Serve the Frontend

You can use any static file server. The simplest options:

```bash
# Option 1: Python (if installed)
cd frontend
python -m http.server 3000

# Option 2: Node.js npx
npx serve frontend

# Option 3: VS Code Live Server extension
# Right-click index.html > Open with Live Server
```

### Step 3: Connect MetaMask

1. Open `http://localhost:3000` in your browser
2. Click **Connect Wallet**
3. Approve the MetaMask connection
4. Ensure MetaMask is set to the correct network (localhost:8545 or Sepolia)

### Step 4: Interact

Use the tab navigation to switch between contracts and perform operations.

---

## Troubleshooting

### "Nothing to compile"

If you see this, your contracts are already compiled. Run `npx hardhat clean` to clear the cache, then compile again.

### "Nonce too high" Error

This happens when your MetaMask nonce is out of sync with the local node (common after restarting `npx hardhat node`):

1. Open MetaMask > Settings > Advanced
2. Click **Clear Activity Tab Data**
3. Try again

### "Insufficient funds"

- **Local**: Make sure `npx hardhat node` is running and you are using one of the pre-funded accounts
- **Sepolia**: Get more test ETH from a faucet

### "Transaction reverted"

Check the error message in the console. Common causes:
- Calling an owner-only function from a non-owner account
- Insufficient token balance for a transfer
- Contract state does not allow the operation (e.g., escrow already released)

### "Could not detect network"

Ensure your MetaMask is connected to the correct network:
- **Local**: Custom RPC at `http://127.0.0.1:8545`, Chain ID `31337`
- **Sepolia**: Select Sepolia from the network dropdown

### CORS Errors in Frontend

If you get CORS errors, make sure you are serving the frontend via a web server (not opening the HTML file directly from the filesystem).

---

## Deployment Checklist

Before deploying to mainnet (production), complete this checklist:

- [ ] All tests pass (`npx hardhat test`)
- [ ] Gas report reviewed (`REPORT_GAS=true npx hardhat test`)
- [ ] Code coverage reviewed (`npx hardhat coverage`)
- [ ] Security audit completed (or at minimum, self-audit using tools like Slither)
- [ ] Constructor arguments double-checked
- [ ] Private key stored securely (hardware wallet recommended)
- [ ] Sufficient ETH in deployer wallet for gas
- [ ] Contract addresses documented after deployment
- [ ] Contracts verified on Etherscan
- [ ] Frontend updated with correct contract addresses
- [ ] Emergency stop (pause) functionality tested
- [ ] Ownership transfer plan documented
