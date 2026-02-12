# Screenshots and Visual Reference

> **NOTE**: This directory is reserved for screenshots of the Crypto Wallet
> Explorer in action. Screenshots should be captured from testnet operations
> only. NEVER capture screenshots containing real private keys, mnemonics,
> or mainnet transaction data.

---

## Expected CLI Output Previews

### 1. Wallet Generation (`generate-wallet`)

```
+----------------------------------------------------------------------+
|   CRYPTO WALLET EXPLORER -- EDUCATIONAL / TESTNET USE ONLY           |
+----------------------------------------------------------------------+

+----------+---------+---------+---------+
|  Col 1   |  Col 2  |  Col 3  |  Col 4  |
+----------+---------+---------+---------+
| 1. word  | 2. word | 3. word | 4. word |
| 5. word  | 6. word | 7. word | 8. word |
| 9. word  |10. word |11. word |12. word |
+----------+---------+---------+---------+

+-------------------+--------------------------------------------+
| Field             | Value                                      |
+-------------------+--------------------------------------------+
| Word Count        | 12                                         |
| Passphrase        | (none)                                     |
| Derivation Path   | m/44'/60'/0'/0/0                           |
| Ethereum Address  | 0xAbCdEf...1234                            |
| Private Key       | 0x1234...abcd                              |
+-------------------+--------------------------------------------+

+----------------------------------------------------------------------+
| NEVER use this wallet for real cryptocurrency. TESTNET ONLY.         |
+----------------------------------------------------------------------+
```

### 2. Key Derivation Visualization (`show-derivation`)

```
===================== Key Derivation Visualizer =====================

+--------------------------------------------------------------------+
| SECURITY WARNING                                                    |
|                                                                     |
| All keys and addresses shown are for EDUCATIONAL / TESTNET only.   |
| NEVER use these keys for real cryptocurrency.                       |
+--------------------------------------------------------------------+

Step 1: Mnemonic Generation (BIP-39)
+--------------------------------------------------+
| BIP-39 Mnemonic Phrase                           |
| 1. word1  2. word2  3. word3  4. word4           |
| 5. word5  6. word6  7. word7  8. word8           |
| 9. word9  10. word10 11. word11 12. word12       |
+--------------------------------------------------+

Step 2: Seed Derivation (BIP-39)
+--------------------------------------------------+
| Binary Seed (BIP-39)                             |
| Method: PBKDF2-HMAC-SHA512, 2048 iterations     |
| Seed: 5eb00bbd...                                |
+--------------------------------------------------+

Step 3: Master Key Derivation (BIP-32)
+--------------------------------------------------+
| Master Key (BIP-32)                              |
| HMAC-SHA512(key="Bitcoin seed", data=seed)       |
| Key: 0x1234...                                   |
| Chain Code: 0xabcd...                            |
+--------------------------------------------------+

Step 4: Child Key Derivation (BIP-44)
  m (master)
  +-- m/44' (purpose = BIP-44) [hardened]
      +-- m/44'/60' (coin_type = Ethereum) [hardened]
          +-- m/44'/60'/0' (account = 0) [hardened]
              +-- m/44'/60'/0'/0 (external chain)
                  +-- m/44'/60'/0'/0/0 (address index 0)

Step 5: Ethereum Address
+--------------------------------------------------+
| Ethereum Address                                 |
| Private Key -> secp256k1 -> Public Key           |
| -> Keccak-256 -> Last 20 bytes -> EIP-55         |
|                                                   |
| Address: 0xAbCdEf...1234                         |
+--------------------------------------------------+
```

### 3. Transaction Building (`build-tx`)

```
+----------------------------------------------------------------------+
|   CRYPTO WALLET EXPLORER -- EDUCATIONAL / TESTNET USE ONLY           |
+----------------------------------------------------------------------+

Building transaction...

+---------------------------+------------------------------------------+
| Transaction Analysis      |                                          |
+---------------------------+------------------------------------------+
| Transaction Type          | EIP-1559                                 |
| Network                   | Sepolia (ID: 11155111)                   |
| Recipient                 | 0xRecipient...                           |
| Value                     | 0.001 ETH                                |
| Gas Limit                 | 21000 units                              |
| Max Fee Per Gas           | 50 Gwei                                  |
| Max Priority Fee          | 2 Gwei                                   |
| Nonce                     | 0                                        |
+---------------------------+------------------------------------------+

Signing transaction...

+---------------------------+------------------------------------------+
| Signed Transaction        |                                          |
+---------------------------+------------------------------------------+
| Transaction Hash          | 0xabc123...                              |
| From                      | 0xSender...                              |
| To                        | 0xRecipient...                           |
| v                         | 1                                        |
| r                         | 0x...                                    |
| s                         | 0x...                                    |
+---------------------------+------------------------------------------+
```

### 4. Balance Checking (`check-balance`)

```
+----------------------------------------------------------------------+
|   CRYPTO WALLET EXPLORER -- EDUCATIONAL / TESTNET USE ONLY           |
+----------------------------------------------------------------------+

Checking balance for 0xYourAddress...

+---------------------------+------------------------------------------+
| ETH Balance (Sepolia)     |                                          |
+---------------------------+------------------------------------------+
| Address                   | 0xYourAddress...                         |
| Balance (ETH)             | 0.500000                                 |
| Balance (Wei)             | 500,000,000,000,000,000                  |
+---------------------------+------------------------------------------+

+---------------------------+------------------------------------------+
| ERC-20 Token Balances     |                                          |
+---------------------------+------------------------------------------+
| Chainlink (LINK)          | 0.000000 LINK                            |
| USD Coin (USDC)           | 0.000000 USDC                            |
| Dai Stablecoin (DAI)      | 0.000000 DAI                             |
| Wrapped Ether (WETH)      | 0.000000 WETH                            |
+---------------------------+------------------------------------------+

TESTNET ONLY: Balances represent testnet tokens with NO real value.
```

### 5. Block Explorer (`explore-block`)

```
+----------------------------------------------------------------------+
| Latest 5 Blocks (Sepolia)                                            |
+----------+-------------------+------+----------+-------+-------------+
| Block    | Time              | TXs  | Gas Used | Gas % | Base Fee    |
+----------+-------------------+------+----------+-------+-------------+
| 5,000,010| 2024-01-15 12:00  |  45  | 5,234,000| 17.4% | 12.5 Gwei  |
| 5,000,009| 2024-01-15 11:59  |  62  | 8,100,000| 27.0% | 12.3 Gwei  |
| 5,000,008| 2024-01-15 11:59  |  28  | 3,500,000| 11.7% | 12.1 Gwei  |
| 5,000,007| 2024-01-15 11:58  |  91  |12,000,000| 40.0% | 12.0 Gwei  |
| 5,000,006| 2024-01-15 11:58  |  55  | 6,800,000| 22.7% | 11.8 Gwei  |
+----------+-------------------+------+----------+-------+-------------+
```

---

## How to Capture Screenshots

When contributing screenshots to this project:

1. **Use testnet ONLY** -- never capture mainnet data
2. **Redact sensitive data** -- blur or obscure any private keys
   (even testnet keys, as a good practice)
3. **Use PNG format** -- for terminal screenshots, PNG preserves
   text clarity
4. **Name files descriptively** -- e.g., `wallet_generation.png`,
   `derivation_tree.png`
5. **Include terminal context** -- show the full command that produced
   the output

### Recommended Screenshot Tools

- **Windows**: Snipping Tool, ShareX
- **macOS**: Cmd+Shift+4, CleanShot X
- **Linux**: Flameshot, GNOME Screenshot
- **Terminal**: `script` command for text capture, or `rich` export

---

> **REMINDER**: All screenshots should show testnet data only.
> The Crypto Wallet Explorer is for educational purposes.
> NEVER use it for real cryptocurrency.
