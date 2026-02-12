# Screenshots Guide

This directory is designated for screenshots documenting the development workflow, testing results, and deployment process. Use screenshots to create a visual record of your project's progress.

---

## Recommended Screenshots to Capture

### 1. Development Environment Setup

- [ ] **Terminal**: Output of `npm install` showing successful dependency installation
- [ ] **VS Code / IDE**: Project structure visible in the file explorer sidebar
- [ ] **Node.js Version**: Output of `node --version` confirming >= 18.0.0

### 2. Contract Compilation

- [ ] **Compilation Output**: Terminal showing `npx hardhat compile` with "Compiled N Solidity files successfully"
- [ ] **Artifacts Folder**: File explorer showing the generated `artifacts/` directory structure

### 3. Test Results

- [ ] **All Tests Passing**: Full output of `npx hardhat test` showing all test suites and results
- [ ] **Gas Report**: Output of `REPORT_GAS=true npx hardhat test` showing gas consumption table
- [ ] **Coverage Report**: Output of `npx hardhat coverage` showing line/branch coverage percentages

### 4. Local Deployment

- [ ] **Hardhat Node**: Terminal running `npx hardhat node` showing pre-funded accounts
- [ ] **Deployment Output**: Terminal showing `npx hardhat run scripts/deploy.js --network localhost` with all 5 contract addresses
- [ ] **Interaction Script**: Output of `npx hardhat run scripts/interact.js --network localhost`

### 5. MetaMask Configuration

- [ ] **MetaMask Installed**: Browser showing MetaMask extension icon
- [ ] **Sepolia Network**: MetaMask network selector showing Sepolia testnet selected
- [ ] **Local Network**: MetaMask configured with Hardhat Local (127.0.0.1:8545)
- [ ] **Test ETH**: MetaMask showing Sepolia ETH balance after faucet request
- [ ] **Imported Account**: MetaMask showing an imported Hardhat account with 10000 ETH
- [ ] **Custom Token**: MetaMask showing DKT token balance after adding the custom token

### 6. Sepolia Testnet Deployment

- [ ] **Deployment Output**: Terminal showing successful Sepolia deployment with contract addresses
- [ ] **Etherscan**: Contract page on sepolia.etherscan.io showing deployed bytecode
- [ ] **Verified Contract**: Etherscan showing green checkmark after source code verification
- [ ] **Transaction History**: Etherscan showing deployment transactions

### 7. Frontend Interface

- [ ] **Dashboard**: Browser showing the frontend with wallet not connected
- [ ] **Connected Wallet**: Frontend after MetaMask connection showing address and network
- [ ] **SimpleStorage Tab**: Showing stored value, set/increment controls
- [ ] **BasicToken Tab**: Showing token info, balance, transfer form
- [ ] **Escrow Tab**: Showing escrow creation form and lookup
- [ ] **Voting Tab**: Showing proposals list and vote casting
- [ ] **NFT Marketplace Tab**: Showing mint, list, and buy forms
- [ ] **Transaction Log**: The transaction log panel showing completed transactions

### 8. Contract Interactions

- [ ] **MetaMask Confirmation**: MetaMask pop-up showing a transaction ready to sign
- [ ] **Successful Transaction**: Frontend status banner showing "Transaction confirmed"
- [ ] **Event Logs**: Etherscan event tab showing emitted events

---

## How to Take Screenshots

### Windows

- **Full Screen**: Press `Win + Print Screen` (saves to Pictures/Screenshots)
- **Active Window**: Press `Alt + Print Screen` (copies to clipboard)
- **Snipping Tool**: Press `Win + Shift + S` for custom region selection

### macOS

- **Full Screen**: Press `Cmd + Shift + 3`
- **Selected Area**: Press `Cmd + Shift + 4`
- **Active Window**: Press `Cmd + Shift + 4`, then `Space`, then click the window

### Browser DevTools

For console output screenshots:
1. Press `F12` to open Developer Tools
2. Navigate to the Console tab
3. Take a screenshot of the relevant output

---

## Naming Convention

Use descriptive filenames with numbered prefixes for ordering:

```
screenshots/
  01-npm-install.png
  02-hardhat-compile.png
  03-test-results.png
  04-gas-report.png
  05-hardhat-node.png
  06-local-deployment.png
  07-metamask-sepolia.png
  08-metamask-local-network.png
  09-sepolia-faucet.png
  10-sepolia-deployment.png
  11-etherscan-verified.png
  12-frontend-dashboard.png
  13-frontend-connected.png
  14-frontend-storage.png
  15-frontend-token.png
  16-frontend-escrow.png
  17-frontend-voting.png
  18-frontend-nft.png
  19-metamask-confirm-tx.png
  20-transaction-log.png
```

---

## Tips for Clear Screenshots

1. **Maximize the terminal window** before capturing test output
2. **Use a clean browser window** (no extra tabs) for frontend screenshots
3. **Highlight important information** using annotation tools if needed
4. **Crop to relevant content** -- remove unnecessary whitespace or UI elements
5. **Use consistent resolution** -- aim for at least 1280x720
6. **Capture timestamps** when possible to show the sequence of operations
