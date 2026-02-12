/**
 * Deployment Script for Smart Contract Development Kit
 *
 * Deploys all five contracts to the configured network:
 * 1. SimpleStorage
 * 2. BasicToken
 * 3. Escrow
 * 4. Voting
 * 5. NFTMarketplace
 *
 * Usage:
 *   npx hardhat run scripts/deploy.js --network localhost
 *   npx hardhat run scripts/deploy.js --network sepolia
 *
 * Prerequisites:
 *   - For localhost: Run `npx hardhat node` in a separate terminal
 *   - For Sepolia: Configure .env with PRIVATE_KEY and ALCHEMY_API_KEY
 */

const hre = require("hardhat");

async function main() {
  console.log("=".repeat(60));
  console.log("Smart Contract Development Kit - Deployment Script");
  console.log("=".repeat(60));
  console.log(`Network: ${hre.network.name}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  console.log("");

  const [deployer] = await hre.ethers.getSigners();
  const balance = await hre.ethers.provider.getBalance(deployer.address);

  console.log(`Deployer address: ${deployer.address}`);
  console.log(`Deployer balance: ${hre.ethers.formatEther(balance)} ETH`);
  console.log("-".repeat(60));

  // Object to store all deployed contract addresses
  const deployedContracts = {};

  // =========================================================================
  // 1. Deploy SimpleStorage
  // =========================================================================
  console.log("\n[1/5] Deploying SimpleStorage...");
  try {
    const SimpleStorage = await hre.ethers.getContractFactory("SimpleStorage");
    const simpleStorage = await SimpleStorage.deploy(42); // Initial value: 42
    await simpleStorage.waitForDeployment();

    const address = await simpleStorage.getAddress();
    deployedContracts.SimpleStorage = address;
    console.log(`  SimpleStorage deployed to: ${address}`);
    console.log(`  Initial value: 42`);
  } catch (error) {
    console.error(`  Failed to deploy SimpleStorage: ${error.message}`);
  }

  // =========================================================================
  // 2. Deploy BasicToken
  // =========================================================================
  console.log("\n[2/5] Deploying BasicToken...");
  try {
    const BasicToken = await hre.ethers.getContractFactory("BasicToken");
    const basicToken = await BasicToken.deploy(
      "DevKit Token",    // Token name
      "DKT",             // Token symbol
      1000000,           // Initial supply: 1 million tokens
      10000000           // Max cap: 10 million tokens
    );
    await basicToken.waitForDeployment();

    const address = await basicToken.getAddress();
    deployedContracts.BasicToken = address;
    console.log(`  BasicToken deployed to: ${address}`);
    console.log(`  Name: DevKit Token (DKT)`);
    console.log(`  Initial Supply: 1,000,000 DKT`);
    console.log(`  Max Cap: 10,000,000 DKT`);
  } catch (error) {
    console.error(`  Failed to deploy BasicToken: ${error.message}`);
  }

  // =========================================================================
  // 3. Deploy Escrow
  // =========================================================================
  console.log("\n[3/5] Deploying Escrow...");
  try {
    const Escrow = await hre.ethers.getContractFactory("Escrow");
    const escrow = await Escrow.deploy();
    await escrow.waitForDeployment();

    const address = await escrow.getAddress();
    deployedContracts.Escrow = address;
    console.log(`  Escrow deployed to: ${address}`);
    console.log(`  Platform Fee: 1% (100 basis points)`);
  } catch (error) {
    console.error(`  Failed to deploy Escrow: ${error.message}`);
  }

  // =========================================================================
  // 4. Deploy Voting
  // =========================================================================
  console.log("\n[4/5] Deploying Voting...");
  try {
    const Voting = await hre.ethers.getContractFactory("Voting");

    // Set voting period: starts now, ends in 7 days
    const currentBlock = await hre.ethers.provider.getBlock("latest");
    const votingStart = currentBlock.timestamp + 60;         // Starts in 1 minute
    const votingEnd = votingStart + 7 * 24 * 60 * 60;       // Ends in 7 days

    const proposalNames = [
      "Increase Development Budget",
      "Launch Community Grants Program",
      "Expand to Layer 2 Networks",
    ];
    const proposalDescriptions = [
      "Allocate 30% more resources to core protocol development",
      "Create a $500K grant pool for ecosystem projects",
      "Deploy contracts on Arbitrum, Optimism, and Polygon",
    ];

    const voting = await Voting.deploy(
      "Quarterly Governance Vote",
      votingStart,
      votingEnd,
      proposalNames,
      proposalDescriptions
    );
    await voting.waitForDeployment();

    const address = await voting.getAddress();
    deployedContracts.Voting = address;
    console.log(`  Voting deployed to: ${address}`);
    console.log(`  Title: Quarterly Governance Vote`);
    console.log(`  Proposals: ${proposalNames.length}`);
    console.log(`  Voting Start: ${new Date(votingStart * 1000).toISOString()}`);
    console.log(`  Voting End: ${new Date(votingEnd * 1000).toISOString()}`);
  } catch (error) {
    console.error(`  Failed to deploy Voting: ${error.message}`);
  }

  // =========================================================================
  // 5. Deploy NFTMarketplace
  // =========================================================================
  console.log("\n[5/5] Deploying NFTMarketplace...");
  try {
    const NFTMarketplace = await hre.ethers.getContractFactory("NFTMarketplace");
    const nftMarketplace = await NFTMarketplace.deploy(
      "DevKit NFT Collection",   // Collection name
      "DKNFT",                    // Collection symbol
      250                         // Platform fee: 2.5%
    );
    await nftMarketplace.waitForDeployment();

    const address = await nftMarketplace.getAddress();
    deployedContracts.NFTMarketplace = address;
    console.log(`  NFTMarketplace deployed to: ${address}`);
    console.log(`  Collection: DevKit NFT Collection (DKNFT)`);
    console.log(`  Platform Fee: 2.5% (250 basis points)`);
    console.log(`  Creator Royalty: 5% (500 basis points)`);
  } catch (error) {
    console.error(`  Failed to deploy NFTMarketplace: ${error.message}`);
  }

  // =========================================================================
  // Deployment Summary
  // =========================================================================
  console.log("\n" + "=".repeat(60));
  console.log("DEPLOYMENT SUMMARY");
  console.log("=".repeat(60));

  for (const [name, address] of Object.entries(deployedContracts)) {
    console.log(`  ${name.padEnd(20)} => ${address}`);
  }

  const finalBalance = await hre.ethers.provider.getBalance(deployer.address);
  const gasSpent = balance - finalBalance;

  console.log("");
  console.log(`  Gas spent: ${hre.ethers.formatEther(gasSpent)} ETH`);
  console.log(`  Remaining balance: ${hre.ethers.formatEther(finalBalance)} ETH`);
  console.log("=".repeat(60));

  // =========================================================================
  // Verification Instructions (for Etherscan)
  // =========================================================================
  if (hre.network.name !== "localhost" && hre.network.name !== "hardhat") {
    console.log("\nTo verify contracts on Etherscan, run:");
    console.log("");

    if (deployedContracts.SimpleStorage) {
      console.log(
        `  npx hardhat verify --network ${hre.network.name} ${deployedContracts.SimpleStorage} 42`
      );
    }
    if (deployedContracts.BasicToken) {
      console.log(
        `  npx hardhat verify --network ${hre.network.name} ${deployedContracts.BasicToken} "DevKit Token" "DKT" 1000000 10000000`
      );
    }
    if (deployedContracts.Escrow) {
      console.log(
        `  npx hardhat verify --network ${hre.network.name} ${deployedContracts.Escrow}`
      );
    }
    if (deployedContracts.NFTMarketplace) {
      console.log(
        `  npx hardhat verify --network ${hre.network.name} ${deployedContracts.NFTMarketplace} "DevKit NFT Collection" "DKNFT" 250`
      );
    }
  }

  return deployedContracts;
}

// Execute deployment
main()
  .then((contracts) => {
    console.log("\nDeployment completed successfully.");
    process.exit(0);
  })
  .catch((error) => {
    console.error("\nDeployment failed:", error);
    process.exit(1);
  });
