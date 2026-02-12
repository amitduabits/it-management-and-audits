/**
 * Hardhat Configuration
 *
 * This file configures the Hardhat development environment including:
 * - Solidity compiler settings (version, optimizer, EVM target)
 * - Network configurations (localhost, Sepolia testnet)
 * - Path mappings for sources, tests, and artifacts
 * - Gas reporting settings
 *
 * Environment Variables (set in .env file):
 *   PRIVATE_KEY       - Your wallet private key for testnet deployments
 *   ALCHEMY_API_KEY   - Your Alchemy API key for RPC access
 *   ETHERSCAN_API_KEY - Your Etherscan API key for contract verification
 */

require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Pull environment variables with fallback defaults
const PRIVATE_KEY = process.env.PRIVATE_KEY || "0x" + "0".repeat(64);
const ALCHEMY_API_KEY = process.env.ALCHEMY_API_KEY || "";
const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || "";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  // ===========================================================================
  // Solidity Compiler Configuration
  // ===========================================================================
  solidity: {
    version: "0.8.19",
    settings: {
      // The optimizer reduces gas costs for deployment and function calls.
      // 200 runs is a balanced default for most use cases.
      optimizer: {
        enabled: true,
        runs: 200,
      },
      // Target the Shanghai EVM version (latest stable as of 2024)
      evmVersion: "shanghai",
      // Output selection for generating ABI and other artifacts
      outputSelection: {
        "*": {
          "*": ["abi", "evm.bytecode", "evm.deployedBytecode", "evm.methodIdentifiers"],
          "": ["ast"],
        },
      },
    },
  },

  // ===========================================================================
  // Network Configuration
  // ===========================================================================
  networks: {
    /**
     * Hardhat's built-in network (in-process).
     * Used automatically when no --network flag is specified.
     * Perfect for rapid testing during development.
     */
    hardhat: {
      chainId: 31337,
      // Mining configuration for predictable block times
      mining: {
        auto: true,
        interval: 0,
      },
    },

    /**
     * Localhost network for Hardhat Node.
     * Usage:
     *   1. Start node: npx hardhat node
     *   2. Deploy: npx hardhat run scripts/deploy.js --network localhost
     */
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },

    /**
     * Sepolia Testnet Configuration
     * - Free test ETH from faucets (e.g., sepoliafaucet.com)
     * - Uses Alchemy as the RPC provider
     *
     * Prerequisites:
     *   1. Create account at https://www.alchemy.com
     *   2. Create a Sepolia app and get the API key
     *   3. Get test ETH from a Sepolia faucet
     *   4. Set PRIVATE_KEY and ALCHEMY_API_KEY in .env
     */
    sepolia: {
      url: `https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}`,
      accounts: PRIVATE_KEY !== "0x" + "0".repeat(64) ? [PRIVATE_KEY] : [],
      chainId: 11155111,
      // Gas settings for Sepolia
      gasPrice: "auto",
    },
  },

  // ===========================================================================
  // Etherscan Verification
  // ===========================================================================
  etherscan: {
    apiKey: {
      sepolia: ETHERSCAN_API_KEY,
    },
  },

  // ===========================================================================
  // Path Configuration
  // ===========================================================================
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },

  // ===========================================================================
  // Gas Reporter Configuration
  // ===========================================================================
  gasReporter: {
    enabled: process.env.REPORT_GAS === "true",
    currency: "USD",
    outputFile: "gas-report.txt",
    noColors: true,
  },

  // ===========================================================================
  // Mocha Test Configuration
  // ===========================================================================
  mocha: {
    timeout: 60000, // 60 seconds timeout for tests
  },
};
