/**
 * Contract Interaction Script
 *
 * Demonstrates how to interact with deployed contracts programmatically.
 * This script connects to your deployed contracts and performs example
 * operations on each one.
 *
 * Usage:
 *   npx hardhat run scripts/interact.js --network localhost
 *   npx hardhat run scripts/interact.js --network sepolia
 *
 * Prerequisites:
 *   - Contracts must already be deployed
 *   - Update the CONTRACT_ADDRESSES object below with your deployed addresses
 */

const hre = require("hardhat");

// ============================================================================
// UPDATE THESE ADDRESSES after deployment
// ============================================================================
const CONTRACT_ADDRESSES = {
  SimpleStorage: "0x5FbDB2315678afecb367f032d93F642f64180aa3",
  BasicToken: "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
  Escrow: "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
  Voting: "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9",
  NFTMarketplace: "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9",
};

// ============================================================================
// Helper: Print section header
// ============================================================================
function section(title) {
  console.log("\n" + "=".repeat(60));
  console.log(`  ${title}`);
  console.log("=".repeat(60));
}

// ============================================================================
// SimpleStorage Interactions
// ============================================================================
async function interactSimpleStorage() {
  section("SimpleStorage Interactions");

  const contract = await hre.ethers.getContractAt(
    "SimpleStorage",
    CONTRACT_ADDRESSES.SimpleStorage
  );

  // Read current value
  const currentValue = await contract.get();
  console.log(`\n  Current stored value: ${currentValue}`);

  // Set a new value
  console.log("\n  Setting value to 100...");
  const setTx = await contract.set(100);
  await setTx.wait();
  console.log(`  Transaction hash: ${setTx.hash}`);

  // Read updated value
  const newValue = await contract.get();
  console.log(`  Updated value: ${newValue}`);

  // Increment
  console.log("\n  Incrementing by 50...");
  const incTx = await contract.increment(50);
  await incTx.wait();

  const afterIncrement = await contract.get();
  console.log(`  Value after increment: ${afterIncrement}`);

  // Get details
  const [value, updates, owner] = await contract.getDetails();
  console.log(`\n  Contract Details:`);
  console.log(`    Value: ${value}`);
  console.log(`    Update Count: ${updates}`);
  console.log(`    Owner: ${owner}`);
}

// ============================================================================
// BasicToken Interactions
// ============================================================================
async function interactBasicToken() {
  section("BasicToken Interactions");

  const [signer, recipient] = await hre.ethers.getSigners();

  const contract = await hre.ethers.getContractAt(
    "BasicToken",
    CONTRACT_ADDRESSES.BasicToken
  );

  // Token info
  const name = await contract.name();
  const symbol = await contract.symbol();
  const totalSupply = await contract.totalSupply();
  const decimals = await contract.decimals();

  console.log(`\n  Token: ${name} (${symbol})`);
  console.log(`  Decimals: ${decimals}`);
  console.log(`  Total Supply: ${hre.ethers.formatUnits(totalSupply, decimals)} ${symbol}`);

  // Check balance
  const balance = await contract.balanceOf(signer.address);
  console.log(`  Your balance: ${hre.ethers.formatUnits(balance, decimals)} ${symbol}`);

  // Transfer tokens
  if (recipient) {
    const transferAmount = hre.ethers.parseUnits("100", decimals);
    console.log(`\n  Transferring 100 ${symbol} to ${recipient.address}...`);

    const transferTx = await contract.transfer(recipient.address, transferAmount);
    await transferTx.wait();
    console.log(`  Transaction hash: ${transferTx.hash}`);

    const recipientBalance = await contract.balanceOf(recipient.address);
    console.log(
      `  Recipient balance: ${hre.ethers.formatUnits(recipientBalance, decimals)} ${symbol}`
    );
  }

  // Approve and check allowance
  if (recipient) {
    const approveAmount = hre.ethers.parseUnits("500", decimals);
    console.log(`\n  Approving ${recipient.address} to spend 500 ${symbol}...`);

    const approveTx = await contract.approve(recipient.address, approveAmount);
    await approveTx.wait();

    const allowance = await contract.allowance(signer.address, recipient.address);
    console.log(
      `  Allowance: ${hre.ethers.formatUnits(allowance, decimals)} ${symbol}`
    );
  }

  // Mint new tokens (owner only)
  const mintAmount = hre.ethers.parseUnits("1000", decimals);
  console.log(`\n  Minting 1000 ${symbol} to deployer...`);
  try {
    const mintTx = await contract.mint(signer.address, mintAmount);
    await mintTx.wait();
    const newBalance = await contract.balanceOf(signer.address);
    console.log(
      `  New balance: ${hre.ethers.formatUnits(newBalance, decimals)} ${symbol}`
    );
  } catch (error) {
    console.log(`  Mint failed (likely not owner): ${error.message}`);
  }
}

// ============================================================================
// Escrow Interactions
// ============================================================================
async function interactEscrow() {
  section("Escrow Interactions");

  const [buyer, seller, arbiter] = await hre.ethers.getSigners();

  const contract = await hre.ethers.getContractAt(
    "Escrow",
    CONTRACT_ADDRESSES.Escrow
  );

  // Create an escrow
  const escrowAmount = hre.ethers.parseEther("0.1");
  const duration = 2 * 24 * 60 * 60; // 2 days
  const description = "Test escrow for digital goods";

  console.log(`\n  Creating escrow...`);
  console.log(`    Buyer: ${buyer.address}`);
  console.log(`    Seller: ${seller.address}`);
  console.log(`    Arbiter: ${arbiter.address}`);
  console.log(`    Amount: ${hre.ethers.formatEther(escrowAmount)} ETH`);
  console.log(`    Duration: 2 days`);

  const createTx = await contract.createEscrow(
    seller.address,
    arbiter.address,
    duration,
    description,
    { value: escrowAmount }
  );
  const receipt = await createTx.wait();
  console.log(`  Transaction hash: ${createTx.hash}`);

  // Read escrow details
  const escrowId = 0; // First escrow
  const details = await contract.getEscrow(escrowId);
  const states = ["Created", "Funded", "Released", "Refunded", "Disputed", "Resolved"];

  console.log(`\n  Escrow #${escrowId} Details:`);
  console.log(`    State: ${states[details.state]}`);
  console.log(`    Amount: ${hre.ethers.formatEther(details.amount)} ETH`);
  console.log(`    Description: ${details.description}`);
  console.log(`    Expired: ${await contract.isExpired(escrowId)}`);

  // Release the escrow
  console.log(`\n  Releasing escrow funds to seller...`);
  const releaseTx = await contract.release(escrowId);
  await releaseTx.wait();
  console.log(`  Transaction hash: ${releaseTx.hash}`);

  const updatedDetails = await contract.getEscrow(escrowId);
  console.log(`  New State: ${states[updatedDetails.state]}`);

  // Check platform balance
  const platformBalance = await contract.platformBalance();
  console.log(`  Platform fees accrued: ${hre.ethers.formatEther(platformBalance)} ETH`);

  // Check contract balance
  const contractBalance = await contract.getContractBalance();
  console.log(`  Contract balance: ${hre.ethers.formatEther(contractBalance)} ETH`);
}

// ============================================================================
// Voting Interactions
// ============================================================================
async function interactVoting() {
  section("Voting Interactions");

  const [chairperson, voter1, voter2] = await hre.ethers.getSigners();

  const contract = await hre.ethers.getContractAt(
    "Voting",
    CONTRACT_ADDRESSES.Voting
  );

  // Get voting summary
  const [title, proposalCount, registeredVoters, votesCast, isActive, isFinalized] =
    await contract.getVotingSummary();

  console.log(`\n  Voting Session: ${title}`);
  console.log(`    Proposals: ${proposalCount}`);
  console.log(`    Registered Voters: ${registeredVoters}`);
  console.log(`    Votes Cast: ${votesCast}`);
  console.log(`    Active: ${isActive}`);
  console.log(`    Finalized: ${isFinalized}`);

  // List all proposals
  console.log(`\n  Proposals:`);
  for (let i = 0; i < proposalCount; i++) {
    const [name, description, votes, proposedBy] = await contract.getProposal(i);
    console.log(`    [${i}] ${name}: ${votes} votes`);
    console.log(`        ${description}`);
  }

  // Register voters (if not already registered)
  if (voter1) {
    try {
      console.log(`\n  Registering voter: ${voter1.address}...`);
      const regTx = await contract.registerVoter(voter1.address);
      await regTx.wait();
      console.log(`  Voter registered successfully.`);
    } catch (error) {
      console.log(`  Already registered or error: ${error.message.slice(0, 80)}...`);
    }
  }

  // Cast a vote (if voting is active)
  if (isActive && voter1) {
    try {
      console.log(`\n  Casting vote for Proposal 0...`);
      const voteTx = await contract.connect(voter1).vote(0);
      await voteTx.wait();
      console.log(`  Vote cast successfully.`);
    } catch (error) {
      console.log(`  Vote failed: ${error.message.slice(0, 80)}...`);
    }
  }

  // Get current winner
  try {
    const winnerName = await contract.getWinnerName();
    console.log(`\n  Current leader: ${winnerName}`);
  } catch (error) {
    console.log(`\n  Could not determine leader: ${error.message.slice(0, 50)}...`);
  }
}

// ============================================================================
// NFTMarketplace Interactions
// ============================================================================
async function interactNFTMarketplace() {
  section("NFTMarketplace Interactions");

  const [deployer, buyer] = await hre.ethers.getSigners();

  const contract = await hre.ethers.getContractAt(
    "NFTMarketplace",
    CONTRACT_ADDRESSES.NFTMarketplace
  );

  // Collection info
  const name = await contract.name();
  const symbol = await contract.symbol();
  const totalSupply = await contract.totalSupply();
  const platformFee = await contract.platformFeeBps();

  console.log(`\n  Collection: ${name} (${symbol})`);
  console.log(`  Total Supply: ${totalSupply}`);
  console.log(`  Platform Fee: ${Number(platformFee) / 100}%`);

  // Mint an NFT
  const tokenURI = "ipfs://QmExampleHash123456789/metadata.json";
  console.log(`\n  Minting new NFT...`);
  console.log(`    Token URI: ${tokenURI}`);

  const mintTx = await contract.mint(tokenURI);
  const mintReceipt = await mintTx.wait();
  console.log(`  Transaction hash: ${mintTx.hash}`);

  // Find the token ID from events
  const mintEvent = mintReceipt.logs.find(
    (log) => log.fragment && log.fragment.name === "ItemMinted"
  );
  const tokenId = mintEvent ? mintEvent.args[0] : 1n;
  console.log(`  Minted Token ID: ${tokenId}`);

  // Check ownership
  const tokenOwner = await contract.ownerOf(tokenId);
  console.log(`  Owner: ${tokenOwner}`);
  console.log(`  Creator: ${await contract.creators(tokenId)}`);

  // List the NFT for sale
  const listingPrice = hre.ethers.parseEther("0.5");
  console.log(`\n  Listing Token #${tokenId} for 0.5 ETH...`);

  const listTx = await contract.listItem(tokenId, listingPrice);
  await listTx.wait();
  console.log(`  Listed successfully.`);

  // Read listing details
  const [seller, price, active] = await contract.getListing(tokenId);
  console.log(`  Listing Details:`);
  console.log(`    Seller: ${seller}`);
  console.log(`    Price: ${hre.ethers.formatEther(price)} ETH`);
  console.log(`    Active: ${active}`);

  // Buy the NFT (with a different account)
  if (buyer) {
    console.log(`\n  Buying Token #${tokenId} as ${buyer.address}...`);

    // First, approve the marketplace to transfer
    const marketplaceAddress = await contract.getAddress();
    const approveTx = await contract.approve(marketplaceAddress, tokenId);
    await approveTx.wait();

    try {
      const buyTx = await contract.connect(buyer).buyItem(tokenId, {
        value: listingPrice,
      });
      await buyTx.wait();
      console.log(`  Purchase successful!`);

      const newOwner = await contract.ownerOf(tokenId);
      console.log(`  New owner: ${newOwner}`);

      // Check pending withdrawals
      const sellerPending = await contract.pendingWithdrawals(deployer.address);
      console.log(
        `  Seller pending withdrawal: ${hre.ethers.formatEther(sellerPending)} ETH`
      );
    } catch (error) {
      console.log(`  Purchase failed: ${error.message.slice(0, 80)}...`);
    }
  }
}

// ============================================================================
// Main Execution
// ============================================================================
async function main() {
  console.log("=".repeat(60));
  console.log("Smart Contract Development Kit - Interaction Script");
  console.log("=".repeat(60));
  console.log(`Network: ${hre.network.name}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);

  const [signer] = await hre.ethers.getSigners();
  console.log(`Signer: ${signer.address}`);

  try {
    await interactSimpleStorage();
  } catch (error) {
    console.error(`\nSimpleStorage interaction failed: ${error.message}`);
  }

  try {
    await interactBasicToken();
  } catch (error) {
    console.error(`\nBasicToken interaction failed: ${error.message}`);
  }

  try {
    await interactEscrow();
  } catch (error) {
    console.error(`\nEscrow interaction failed: ${error.message}`);
  }

  try {
    await interactVoting();
  } catch (error) {
    console.error(`\nVoting interaction failed: ${error.message}`);
  }

  try {
    await interactNFTMarketplace();
  } catch (error) {
    console.error(`\nNFTMarketplace interaction failed: ${error.message}`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("Interaction script completed.");
  console.log("=".repeat(60));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Script failed:", error);
    process.exit(1);
  });
