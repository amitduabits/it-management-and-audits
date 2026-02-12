/**
 * Smart Contract DevKit - Frontend Application
 *
 * This script handles wallet connection via MetaMask (or any EIP-1193 provider)
 * and provides functions to interact with all five deployed contracts using
 * ethers.js v6.
 *
 * Architecture:
 * - Single-page application with tab navigation
 * - Event-driven UI updates
 * - Transaction logging with status tracking
 * - Graceful error handling with user-friendly messages
 */

// =============================================================================
// Contract ABIs (minimal - include only the functions we call from the frontend)
// =============================================================================

const ABIS = {
  SimpleStorage: [
    "function get() view returns (uint256)",
    "function set(uint256 newValue)",
    "function increment(uint256 amount)",
    "function decrement(uint256 amount)",
    "function reset()",
    "function getDetails() view returns (uint256 value, uint256 totalUpdates, address contractOwner)",
    "function owner() view returns (address)",
    "function updateCount() view returns (uint256)",
    "event ValueChanged(uint256 indexed previousValue, uint256 indexed newValue, address indexed updatedBy, uint256 timestamp)",
  ],

  BasicToken: [
    "function name() view returns (string)",
    "function symbol() view returns (string)",
    "function decimals() view returns (uint8)",
    "function totalSupply() view returns (uint256)",
    "function balanceOf(address account) view returns (uint256)",
    "function transfer(address to, uint256 amount) returns (bool)",
    "function approve(address spender, uint256 amount) returns (bool)",
    "function allowance(address owner, address spender) view returns (uint256)",
    "function mint(address to, uint256 amount)",
    "function burn(uint256 amount)",
    "event Transfer(address indexed from, address indexed to, uint256 value)",
    "event Approval(address indexed owner, address indexed spender, uint256 value)",
  ],

  Escrow: [
    "function createEscrow(address payable seller, address arbiter, uint256 duration, string description) payable returns (uint256)",
    "function release(uint256 escrowId)",
    "function refund(uint256 escrowId)",
    "function raiseDispute(uint256 escrowId)",
    "function getEscrow(uint256 escrowId) view returns (tuple(address buyer, address seller, address arbiter, uint256 amount, uint256 createdAt, uint256 deadline, uint8 state, string description))",
    "function escrowCount() view returns (uint256)",
    "function isExpired(uint256 escrowId) view returns (bool)",
    "event EscrowCreated(uint256 indexed escrowId, address indexed buyer, address indexed seller, uint256 amount, uint256 deadline)",
    "event EscrowReleased(uint256 indexed escrowId, uint256 amountToSeller, uint256 fee)",
    "event EscrowRefunded(uint256 indexed escrowId, uint256 amount)",
  ],

  Voting: [
    "function votingTitle() view returns (string)",
    "function getVotingSummary() view returns (string title, uint256 proposalCount, uint256 registeredVoters, uint256 votesCast, bool isActive, bool isFinalized)",
    "function getProposal(uint256 proposalId) view returns (string name, string description, uint256 voteCount, address proposedBy)",
    "function getProposalCount() view returns (uint256)",
    "function getWinnerName() view returns (string)",
    "function vote(uint256 proposalId)",
    "function delegate(address to)",
    "function hasVoted(address voter) view returns (bool)",
    "event VoteCast(address indexed voter, uint256 indexed proposalId, uint256 weight)",
    "event VoteDelegated(address indexed from, address indexed to)",
  ],

  NFTMarketplace: [
    "function name() view returns (string)",
    "function symbol() view returns (string)",
    "function totalSupply() view returns (uint256)",
    "function balanceOf(address owner) view returns (uint256)",
    "function ownerOf(uint256 tokenId) view returns (address)",
    "function tokenURI(uint256 tokenId) view returns (string)",
    "function creators(uint256 tokenId) view returns (address)",
    "function mint(string uri) returns (uint256)",
    "function listItem(uint256 tokenId, uint256 price)",
    "function buyItem(uint256 tokenId) payable",
    "function cancelListing(uint256 tokenId)",
    "function getListing(uint256 tokenId) view returns (address seller, uint256 price, bool active)",
    "function pendingWithdrawals(address) view returns (uint256)",
    "function withdraw()",
    "function approve(address to, uint256 tokenId)",
    "function platformFeeBps() view returns (uint256)",
    "event ItemMinted(uint256 indexed tokenId, address indexed creator, string tokenURI)",
    "event ItemListed(uint256 indexed tokenId, address indexed seller, uint256 price)",
    "event ItemSold(uint256 indexed tokenId, address indexed seller, address indexed buyer, uint256 price)",
  ],
};

// =============================================================================
// Contract Addresses - UPDATE THESE AFTER DEPLOYMENT
// =============================================================================

const ADDRESSES = {
  SimpleStorage: "0x5FbDB2315678afecb367f032d93F642f64180aa3",
  BasicToken: "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
  Escrow: "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
  Voting: "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9",
  NFTMarketplace: "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9",
};

// =============================================================================
// Application State
// =============================================================================

let provider = null;
let signer = null;
let contracts = {};
let currentAccount = null;

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  setupTabNavigation();
  setupEventListeners();
  checkExistingConnection();
});

/**
 * Check if wallet was previously connected (page refresh persistence)
 */
async function checkExistingConnection() {
  if (typeof window.ethereum !== "undefined") {
    try {
      const accounts = await window.ethereum.request({ method: "eth_accounts" });
      if (accounts.length > 0) {
        await connectWallet();
      }
    } catch (err) {
      console.log("No existing connection found");
    }
  }
}

// =============================================================================
// Wallet Connection
// =============================================================================

/**
 * Connects to the user's MetaMask (or compatible) wallet.
 * Sets up the provider, signer, and contract instances.
 */
async function connectWallet() {
  if (typeof window.ethereum === "undefined") {
    showStatus("MetaMask is not installed. Please install it from metamask.io", "error");
    return;
  }

  try {
    // Request account access
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });

    // Create ethers.js provider and signer
    provider = new ethers.BrowserProvider(window.ethereum);
    signer = await provider.getSigner();
    currentAccount = accounts[0];

    // Initialize contract instances
    initializeContracts();

    // Update UI
    updateWalletUI(currentAccount);
    updateNetworkInfo();

    // Load initial data for the active tab
    loadActiveTabData();

    showStatus("Wallet connected successfully!", "success");

    // Listen for account and network changes
    window.ethereum.on("accountsChanged", handleAccountsChanged);
    window.ethereum.on("chainChanged", handleChainChanged);
  } catch (error) {
    showStatus(`Connection failed: ${error.message}`, "error");
  }
}

/**
 * Initializes ethers.js Contract instances for all five contracts
 */
function initializeContracts() {
  for (const [name, abi] of Object.entries(ABIS)) {
    if (ADDRESSES[name]) {
      contracts[name] = new ethers.Contract(ADDRESSES[name], abi, signer);
    }
  }
}

/**
 * Handles MetaMask account change
 */
function handleAccountsChanged(accounts) {
  if (accounts.length === 0) {
    showStatus("Wallet disconnected", "warning");
    resetUI();
  } else {
    currentAccount = accounts[0];
    updateWalletUI(currentAccount);
    loadActiveTabData();
  }
}

/**
 * Handles MetaMask network change
 */
function handleChainChanged() {
  window.location.reload();
}

// =============================================================================
// UI Helpers
// =============================================================================

/**
 * Updates the wallet display in the header
 */
function updateWalletUI(address) {
  const connectBtn = document.getElementById("connect-btn");
  const walletAddr = document.getElementById("wallet-address");

  connectBtn.textContent = "Connected";
  connectBtn.classList.add("connected");

  walletAddr.textContent = shortenAddress(address);
  walletAddr.title = address;
  walletAddr.classList.remove("hidden");
}

/**
 * Updates network badge in the header
 */
async function updateNetworkInfo() {
  const network = await provider.getNetwork();
  const networkNames = {
    1: "Mainnet",
    11155111: "Sepolia",
    31337: "Localhost",
    5: "Goerli",
  };

  const networkBadge = document.getElementById("network-badge");
  const networkName = document.getElementById("network-name");

  networkName.textContent = networkNames[Number(network.chainId)] || `Chain ${network.chainId}`;
  networkBadge.classList.remove("hidden");
}

/**
 * Resets UI to disconnected state
 */
function resetUI() {
  document.getElementById("connect-btn").textContent = "Connect Wallet";
  document.getElementById("connect-btn").classList.remove("connected");
  document.getElementById("wallet-address").classList.add("hidden");
  document.getElementById("network-badge").classList.add("hidden");
  contracts = {};
  signer = null;
  currentAccount = null;
}

/**
 * Shortens an Ethereum address for display
 */
function shortenAddress(address) {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

/**
 * Shows a status message banner
 */
function showStatus(message, type = "info") {
  const banner = document.getElementById("status-banner");
  const messageEl = document.getElementById("status-message");

  banner.className = `status-banner status-${type}`;
  messageEl.textContent = message;
  banner.classList.remove("hidden");

  // Auto-hide after 5 seconds for success messages
  if (type === "success") {
    setTimeout(() => banner.classList.add("hidden"), 5000);
  }
}

/**
 * Logs a transaction to the transaction log panel
 */
function logTransaction(action, txHash, status = "pending") {
  const logEntries = document.getElementById("tx-log-entries");
  const placeholder = logEntries.querySelector(".placeholder");
  if (placeholder) placeholder.remove();

  const entry = document.createElement("div");
  entry.className = `tx-entry tx-${status}`;
  entry.innerHTML = `
    <span class="tx-action">${action}</span>
    <span class="tx-hash" title="${txHash}">${txHash ? shortenAddress(txHash) : "..."}</span>
    <span class="tx-status">${status}</span>
    <span class="tx-time">${new Date().toLocaleTimeString()}</span>
  `;
  logEntries.prepend(entry);

  return entry;
}

/**
 * Updates a transaction log entry status
 */
function updateTxLog(entry, txHash, status) {
  entry.className = `tx-entry tx-${status}`;
  entry.querySelector(".tx-hash").textContent = txHash ? shortenAddress(txHash) : "...";
  entry.querySelector(".tx-hash").title = txHash || "";
  entry.querySelector(".tx-status").textContent = status;
}

// =============================================================================
// Tab Navigation
// =============================================================================

function setupTabNavigation() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Deactivate all tabs
      tabButtons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));

      // Activate clicked tab
      btn.classList.add("active");
      const tabId = `tab-${btn.dataset.tab}`;
      document.getElementById(tabId).classList.add("active");

      // Load data for the tab
      loadActiveTabData();
    });
  });
}

function loadActiveTabData() {
  const activeTab = document.querySelector(".tab-btn.active");
  if (!activeTab || !signer) return;

  switch (activeTab.dataset.tab) {
    case "storage":
      loadStorageData();
      break;
    case "token":
      loadTokenData();
      break;
    case "escrow":
      break; // Escrow data loaded on lookup
    case "voting":
      loadVotingData();
      break;
    case "nft":
      loadNFTData();
      break;
  }
}

// =============================================================================
// Event Listeners
// =============================================================================

function setupEventListeners() {
  // Wallet connection
  document.getElementById("connect-btn").addEventListener("click", connectWallet);

  // Status banner close
  document.getElementById("status-close").addEventListener("click", () => {
    document.getElementById("status-banner").classList.add("hidden");
  });

  // Transaction log clear
  document.getElementById("tx-log-clear").addEventListener("click", () => {
    document.getElementById("tx-log-entries").innerHTML =
      '<p class="placeholder">No transactions yet.</p>';
  });

  // ----- SimpleStorage -----
  document.getElementById("storage-refresh").addEventListener("click", loadStorageData);
  document.getElementById("storage-set-btn").addEventListener("click", storageSet);
  document.getElementById("storage-inc-btn").addEventListener("click", storageIncrement);
  document.getElementById("storage-dec-btn").addEventListener("click", storageDecrement);

  // ----- BasicToken -----
  document.getElementById("token-refresh").addEventListener("click", loadTokenData);
  document.getElementById("token-transfer-btn").addEventListener("click", tokenTransfer);
  document.getElementById("token-approve-btn").addEventListener("click", tokenApprove);

  // ----- Escrow -----
  document.getElementById("escrow-create-btn").addEventListener("click", escrowCreate);
  document.getElementById("escrow-lookup-btn").addEventListener("click", escrowLookup);
  document.getElementById("escrow-release-btn").addEventListener("click", escrowRelease);
  document.getElementById("escrow-refund-btn").addEventListener("click", escrowRefund);
  document.getElementById("escrow-dispute-btn").addEventListener("click", escrowDispute);

  // ----- Voting -----
  document.getElementById("voting-refresh").addEventListener("click", loadVotingData);
  document.getElementById("voting-vote-btn").addEventListener("click", votingVote);
  document.getElementById("voting-delegate-btn").addEventListener("click", votingDelegate);

  // ----- NFT Marketplace -----
  document.getElementById("nft-mint-btn").addEventListener("click", nftMint);
  document.getElementById("nft-list-btn").addEventListener("click", nftList);
  document.getElementById("nft-buy-btn").addEventListener("click", nftBuy);
  document.getElementById("nft-cancel-btn").addEventListener("click", nftCancel);
  document.getElementById("nft-lookup-btn").addEventListener("click", nftLookup);
  document.getElementById("nft-withdraw-btn").addEventListener("click", nftWithdraw);
}

// =============================================================================
// SimpleStorage Functions
// =============================================================================

async function loadStorageData() {
  if (!contracts.SimpleStorage) return;
  try {
    const [value, updates, owner] = await contracts.SimpleStorage.getDetails();
    document.getElementById("storage-current-value").textContent = value.toString();
    document.getElementById("storage-update-count").textContent = updates.toString();
    document.getElementById("storage-owner").textContent = shortenAddress(owner);
    document.getElementById("storage-owner").title = owner;
  } catch (error) {
    showStatus(`Failed to load storage data: ${error.message}`, "error");
  }
}

async function storageSet() {
  const value = document.getElementById("storage-set-input").value;
  if (!value) return showStatus("Please enter a value", "warning");

  const entry = logTransaction("SimpleStorage.set()", null);
  try {
    const tx = await contracts.SimpleStorage.set(value);
    updateTxLog(entry, tx.hash, "pending");
    showStatus("Transaction submitted, waiting for confirmation...", "info");

    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Value updated successfully!", "success");
    loadStorageData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Set failed: ${error.reason || error.message}`, "error");
  }
}

async function storageIncrement() {
  const amount = document.getElementById("storage-inc-input").value;
  if (!amount) return showStatus("Please enter an amount", "warning");

  const entry = logTransaction("SimpleStorage.increment()", null);
  try {
    const tx = await contracts.SimpleStorage.increment(amount);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Value incremented!", "success");
    loadStorageData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Increment failed: ${error.reason || error.message}`, "error");
  }
}

async function storageDecrement() {
  const amount = document.getElementById("storage-inc-input").value;
  if (!amount) return showStatus("Please enter an amount", "warning");

  const entry = logTransaction("SimpleStorage.decrement()", null);
  try {
    const tx = await contracts.SimpleStorage.decrement(amount);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Value decremented!", "success");
    loadStorageData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Decrement failed: ${error.reason || error.message}`, "error");
  }
}

// =============================================================================
// BasicToken Functions
// =============================================================================

async function loadTokenData() {
  if (!contracts.BasicToken) return;
  try {
    const name = await contracts.BasicToken.name();
    const symbol = await contracts.BasicToken.symbol();
    const totalSupply = await contracts.BasicToken.totalSupply();
    const decimals = await contracts.BasicToken.decimals();
    const balance = await contracts.BasicToken.balanceOf(currentAccount);

    document.getElementById("token-name").textContent = name;
    document.getElementById("token-symbol").textContent = symbol;
    document.getElementById("token-supply").textContent =
      `${ethers.formatUnits(totalSupply, decimals)} ${symbol}`;
    document.getElementById("token-balance").textContent =
      `${ethers.formatUnits(balance, decimals)} ${symbol}`;
  } catch (error) {
    showStatus(`Failed to load token data: ${error.message}`, "error");
  }
}

async function tokenTransfer() {
  const to = document.getElementById("token-transfer-to").value;
  const amount = document.getElementById("token-transfer-amount").value;
  if (!to || !amount) return showStatus("Please fill in all fields", "warning");

  const entry = logTransaction("BasicToken.transfer()", null);
  try {
    const decimals = await contracts.BasicToken.decimals();
    const parsedAmount = ethers.parseUnits(amount, decimals);

    const tx = await contracts.BasicToken.transfer(to, parsedAmount);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Transfer successful!", "success");
    loadTokenData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Transfer failed: ${error.reason || error.message}`, "error");
  }
}

async function tokenApprove() {
  const spender = document.getElementById("token-approve-spender").value;
  const amount = document.getElementById("token-approve-amount").value;
  if (!spender || !amount) return showStatus("Please fill in all fields", "warning");

  const entry = logTransaction("BasicToken.approve()", null);
  try {
    const decimals = await contracts.BasicToken.decimals();
    const parsedAmount = ethers.parseUnits(amount, decimals);

    const tx = await contracts.BasicToken.approve(spender, parsedAmount);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Approval granted!", "success");
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Approval failed: ${error.reason || error.message}`, "error");
  }
}

// =============================================================================
// Escrow Functions
// =============================================================================

async function escrowCreate() {
  const seller = document.getElementById("escrow-seller").value;
  const arbiter = document.getElementById("escrow-arbiter").value;
  const amount = document.getElementById("escrow-amount").value;
  const duration = document.getElementById("escrow-duration").value;
  const description = document.getElementById("escrow-description").value;

  if (!seller || !arbiter || !amount || !duration) {
    return showStatus("Please fill in all required fields", "warning");
  }

  const entry = logTransaction("Escrow.createEscrow()", null);
  try {
    const durationSeconds = parseInt(duration) * 86400; // Convert days to seconds
    const tx = await contracts.Escrow.createEscrow(
      seller,
      arbiter,
      durationSeconds,
      description || "No description",
      { value: ethers.parseEther(amount) }
    );
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Escrow created successfully!", "success");
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Escrow creation failed: ${error.reason || error.message}`, "error");
  }
}

async function escrowLookup() {
  const id = document.getElementById("escrow-lookup-id").value;
  if (id === "") return showStatus("Please enter an Escrow ID", "warning");

  try {
    const details = await contracts.Escrow.getEscrow(id);
    const states = ["Created", "Funded", "Released", "Refunded", "Disputed", "Resolved"];

    document.getElementById("escrow-info-buyer").textContent = shortenAddress(details.buyer);
    document.getElementById("escrow-info-seller").textContent = shortenAddress(details.seller);
    document.getElementById("escrow-info-amount").textContent = ethers.formatEther(details.amount) + " ETH";
    document.getElementById("escrow-info-state").textContent = states[details.state];
    document.getElementById("escrow-details").classList.remove("hidden");
  } catch (error) {
    showStatus(`Lookup failed: ${error.reason || error.message}`, "error");
  }
}

async function escrowRelease() {
  const id = document.getElementById("escrow-action-id").value;
  if (id === "") return showStatus("Please enter an Escrow ID", "warning");

  const entry = logTransaction("Escrow.release()", null);
  try {
    const tx = await contracts.Escrow.release(id);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Escrow released!", "success");
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Release failed: ${error.reason || error.message}`, "error");
  }
}

async function escrowRefund() {
  const id = document.getElementById("escrow-action-id").value;
  if (id === "") return showStatus("Please enter an Escrow ID", "warning");

  const entry = logTransaction("Escrow.refund()", null);
  try {
    const tx = await contracts.Escrow.refund(id);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Escrow refunded!", "success");
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Refund failed: ${error.reason || error.message}`, "error");
  }
}

async function escrowDispute() {
  const id = document.getElementById("escrow-action-id").value;
  if (id === "") return showStatus("Please enter an Escrow ID", "warning");

  const entry = logTransaction("Escrow.raiseDispute()", null);
  try {
    const tx = await contracts.Escrow.raiseDispute(id);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Dispute raised!", "success");
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Dispute failed: ${error.reason || error.message}`, "error");
  }
}

// =============================================================================
// Voting Functions
// =============================================================================

async function loadVotingData() {
  if (!contracts.Voting) return;
  try {
    const [title, proposalCount, registeredVoters, votesCast, isActive, isFinalized] =
      await contracts.Voting.getVotingSummary();

    document.getElementById("voting-title").textContent = title;
    document.getElementById("voting-status").textContent = isActive
      ? "Active"
      : isFinalized
      ? "Finalized"
      : "Not Started";
    document.getElementById("voting-proposals-count").textContent = proposalCount.toString();
    document.getElementById("voting-voters-count").textContent = registeredVoters.toString();
    document.getElementById("voting-votes-cast").textContent = votesCast.toString();

    try {
      const leader = await contracts.Voting.getWinnerName();
      document.getElementById("voting-leader").textContent = leader;
    } catch {
      document.getElementById("voting-leader").textContent = "No votes yet";
    }

    // Load proposals list
    const listEl = document.getElementById("voting-proposals-list");
    listEl.innerHTML = "";

    for (let i = 0; i < Number(proposalCount); i++) {
      const [name, description, votes] = await contracts.Voting.getProposal(i);
      const proposalEl = document.createElement("div");
      proposalEl.className = "proposal-item";
      proposalEl.innerHTML = `
        <div class="proposal-header">
          <span class="proposal-id">#${i}</span>
          <span class="proposal-name">${name}</span>
          <span class="proposal-votes">${votes} votes</span>
        </div>
        <p class="proposal-desc">${description}</p>
      `;
      listEl.appendChild(proposalEl);
    }
  } catch (error) {
    showStatus(`Failed to load voting data: ${error.message}`, "error");
  }
}

async function votingVote() {
  const proposalId = document.getElementById("voting-proposal-id").value;
  if (proposalId === "") return showStatus("Please enter a Proposal ID", "warning");

  const entry = logTransaction("Voting.vote()", null);
  try {
    const tx = await contracts.Voting.vote(proposalId);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Vote cast successfully!", "success");
    loadVotingData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Vote failed: ${error.reason || error.message}`, "error");
  }
}

async function votingDelegate() {
  const to = document.getElementById("voting-delegate-to").value;
  if (!to) return showStatus("Please enter a delegate address", "warning");

  const entry = logTransaction("Voting.delegate()", null);
  try {
    const tx = await contracts.Voting.delegate(to);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Vote delegated!", "success");
    loadVotingData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Delegation failed: ${error.reason || error.message}`, "error");
  }
}

// =============================================================================
// NFT Marketplace Functions
// =============================================================================

async function loadNFTData() {
  if (!contracts.NFTMarketplace) return;
  try {
    const totalSupply = await contracts.NFTMarketplace.totalSupply();
    const balance = await contracts.NFTMarketplace.balanceOf(currentAccount);
    const pending = await contracts.NFTMarketplace.pendingWithdrawals(currentAccount);

    document.getElementById("nft-total-supply").textContent = totalSupply.toString();
    document.getElementById("nft-your-count").textContent = balance.toString();
    document.getElementById("nft-pending-balance").textContent =
      ethers.formatEther(pending) + " ETH";
  } catch (error) {
    showStatus(`Failed to load NFT data: ${error.message}`, "error");
  }
}

async function nftMint() {
  const uri = document.getElementById("nft-mint-uri").value;
  if (!uri) return showStatus("Please enter a Token URI", "warning");

  const entry = logTransaction("NFTMarketplace.mint()", null);
  try {
    const tx = await contracts.NFTMarketplace.mint(uri);
    updateTxLog(entry, tx.hash, "pending");
    const receipt = await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");

    showStatus("NFT minted successfully!", "success");
    loadNFTData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Mint failed: ${error.reason || error.message}`, "error");
  }
}

async function nftList() {
  const tokenId = document.getElementById("nft-list-id").value;
  const price = document.getElementById("nft-list-price").value;
  if (!tokenId || !price) return showStatus("Please fill in all fields", "warning");

  const entry = logTransaction("NFTMarketplace.listItem()", null);
  try {
    const tx = await contracts.NFTMarketplace.listItem(
      tokenId,
      ethers.parseEther(price)
    );
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("NFT listed for sale!", "success");
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Listing failed: ${error.reason || error.message}`, "error");
  }
}

async function nftBuy() {
  const tokenId = document.getElementById("nft-action-id").value;
  if (!tokenId) return showStatus("Please enter a Token ID", "warning");

  const entry = logTransaction("NFTMarketplace.buyItem()", null);
  try {
    const [, price, active] = await contracts.NFTMarketplace.getListing(tokenId);
    if (!active) return showStatus("This NFT is not listed for sale", "warning");

    const tx = await contracts.NFTMarketplace.buyItem(tokenId, { value: price });
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("NFT purchased!", "success");
    loadNFTData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Purchase failed: ${error.reason || error.message}`, "error");
  }
}

async function nftCancel() {
  const tokenId = document.getElementById("nft-action-id").value;
  if (!tokenId) return showStatus("Please enter a Token ID", "warning");

  const entry = logTransaction("NFTMarketplace.cancelListing()", null);
  try {
    const tx = await contracts.NFTMarketplace.cancelListing(tokenId);
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Listing canceled!", "success");
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Cancel failed: ${error.reason || error.message}`, "error");
  }
}

async function nftLookup() {
  const tokenId = document.getElementById("nft-lookup-id").value;
  if (!tokenId) return showStatus("Please enter a Token ID", "warning");

  try {
    const owner = await contracts.NFTMarketplace.ownerOf(tokenId);
    const creator = await contracts.NFTMarketplace.creators(tokenId);
    const uri = await contracts.NFTMarketplace.tokenURI(tokenId);
    const [seller, price, active] = await contracts.NFTMarketplace.getListing(tokenId);

    document.getElementById("nft-info-owner").textContent = shortenAddress(owner);
    document.getElementById("nft-info-creator").textContent = shortenAddress(creator);
    document.getElementById("nft-info-uri").textContent = uri.length > 40 ? uri.slice(0, 40) + "..." : uri;
    document.getElementById("nft-info-uri").title = uri;
    document.getElementById("nft-info-listed").textContent = active ? "Yes" : "No";
    document.getElementById("nft-info-price").textContent = active
      ? ethers.formatEther(price) + " ETH"
      : "N/A";
    document.getElementById("nft-details").classList.remove("hidden");
  } catch (error) {
    showStatus(`Lookup failed: ${error.reason || error.message}`, "error");
  }
}

async function nftWithdraw() {
  const entry = logTransaction("NFTMarketplace.withdraw()", null);
  try {
    const tx = await contracts.NFTMarketplace.withdraw();
    updateTxLog(entry, tx.hash, "pending");
    await tx.wait();
    updateTxLog(entry, tx.hash, "confirmed");
    showStatus("Withdrawal successful!", "success");
    loadNFTData();
  } catch (error) {
    updateTxLog(entry, null, "failed");
    showStatus(`Withdrawal failed: ${error.reason || error.message}`, "error");
  }
}
