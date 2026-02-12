# Smart Contract Reference

Complete function-by-function documentation for each contract in the Smart Contract DevKit.

---

## Table of Contents

1. [SimpleStorage](#1-simplestorage)
2. [BasicToken (ERC-20)](#2-basictoken-erc-20)
3. [Escrow](#3-escrow)
4. [Voting](#4-voting)
5. [NFTMarketplace (ERC-721)](#5-nftmarketplace-erc-721)

---

## 1. SimpleStorage

**File**: `contracts/SimpleStorage.sol`
**Purpose**: Stores and retrieves a single `uint256` value on-chain. Demonstrates state variables, events, modifiers, access control, and basic arithmetic.

### Constructor

```solidity
constructor(uint256 initialValue)
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `initialValue` | `uint256` | The value stored upon deployment |

The deployer becomes the contract owner.

### State Variables

| Variable | Type | Visibility | Description |
|:---------|:-----|:-----------|:------------|
| `owner` | `address` | public | Contract deployer/owner |
| `updateCount` | `uint256` | public | Total number of value updates |
| `lastValueByAddress` | `mapping(address => uint256)` | public | Last value each address stored |
| `lastUpdateTimestamp` | `mapping(address => uint256)` | public | Timestamp of each address's last update |

### Functions

#### `set(uint256 newValue)` -- external

Updates the stored value. Reverts if the new value equals the current value.

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `newValue` | `uint256` | The new value to store |

**Emits**: `ValueChanged(previousValue, newValue, updatedBy, timestamp)`

---

#### `get()` -- external view returns (uint256)

Returns the currently stored value. No gas cost when called off-chain.

---

#### `getDetails()` -- external view returns (uint256, uint256, address)

Returns the stored value, total update count, and owner address.

---

#### `reset()` -- external, onlyOwner

Sets the stored value to zero. Only callable by the owner.

**Emits**: `ValueChanged(previousValue, 0, owner, timestamp)`

---

#### `increment(uint256 amount)` -- external

Adds `amount` to the stored value. Reverts on overflow (Solidity 0.8.x built-in).

---

#### `decrement(uint256 amount)` -- external

Subtracts `amount` from the stored value. Reverts on underflow.

---

#### `transferOwnership(address newOwner)` -- external, onlyOwner

Transfers ownership to a new address. Cannot transfer to the zero address.

**Emits**: `OwnershipTransferred(previousOwner, newOwner)`

### Events

| Event | Parameters | Description |
|:------|:-----------|:------------|
| `ValueChanged` | `previousValue (indexed), newValue (indexed), updatedBy (indexed), timestamp` | Emitted on every value update |
| `OwnershipTransferred` | `previousOwner (indexed), newOwner (indexed)` | Emitted on ownership transfer |

---

## 2. BasicToken (ERC-20)

**File**: `contracts/BasicToken.sol`
**Purpose**: A fully ERC-20 compliant fungible token with minting, burning, pausable transfers, and allowance safety helpers.

### Constructor

```solidity
constructor(string _name, string _symbol, uint256 _initialSupply, uint256 _cap)
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `_name` | `string` | Token name (e.g., "DevKit Token") |
| `_symbol` | `string` | Token symbol (e.g., "DKT") |
| `_initialSupply` | `uint256` | Tokens to mint to deployer (whole units) |
| `_cap` | `uint256` | Maximum total supply (whole units) |

### ERC-20 Standard Functions

#### `totalSupply()` -- view returns (uint256)
Returns total tokens in circulation.

#### `balanceOf(address account)` -- view returns (uint256)
Returns token balance of `account`.

#### `transfer(address to, uint256 amount)` -- returns (bool)
Transfers `amount` tokens from caller to `to`. Requires sufficient balance. Reverts when paused.

**Emits**: `Transfer(from, to, amount)`

#### `approve(address spender, uint256 amount)` -- returns (bool)
Sets allowance for `spender` to spend `amount` of caller's tokens.

**Emits**: `Approval(owner, spender, amount)`

#### `allowance(address owner, address spender)` -- view returns (uint256)
Returns remaining allowance.

#### `transferFrom(address from, address to, uint256 amount)` -- returns (bool)
Transfers tokens on behalf of `from` using caller's allowance. Decreases allowance.

**Emits**: `Transfer(from, to, amount)` and `Approval(from, caller, newAllowance)`

### Extended Functions

#### `increaseAllowance(address spender, uint256 addedValue)` -- returns (bool)
Safely increases the allowance (mitigates race condition).

#### `decreaseAllowance(address spender, uint256 subtractedValue)` -- returns (bool)
Safely decreases the allowance.

#### `mint(address to, uint256 amount)` -- onlyOwner
Creates `amount` new tokens for `to`. Reverts if total supply would exceed the cap.

**Emits**: `Transfer(address(0), to, amount)`

#### `burn(uint256 amount)`
Destroys `amount` tokens from caller's balance. Any holder can burn their own tokens.

**Emits**: `Transfer(caller, address(0), amount)`

#### `pause()` -- onlyOwner
Pauses all token transfers. **Emits**: `Paused(account)`

#### `unpause()` -- onlyOwner
Unpauses all token transfers. **Emits**: `Unpaused(account)`

#### `transferOwnership(address newOwner)` -- onlyOwner
Transfers minting rights to a new address.

---

## 3. Escrow

**File**: `contracts/Escrow.sol`
**Purpose**: Two-party escrow with deposit, release, refund, dispute resolution, and platform fees. Implements reentrancy guard and checks-effects-interactions pattern.

### Constructor

```solidity
constructor()
```

The deployer becomes the platform owner who receives fees.

### Escrow States

| State | Value | Description |
|:------|:------|:------------|
| Created | 0 | Escrow created but not funded |
| Funded | 1 | Buyer deposited ETH |
| Released | 2 | Funds sent to seller |
| Refunded | 3 | Funds returned to buyer |
| Disputed | 4 | Dispute raised by buyer or seller |
| Resolved | 5 | Arbiter resolved the dispute |

### Functions

#### `createEscrow(address seller, address arbiter, uint256 duration, string description)` -- payable returns (uint256)

Creates and funds a new escrow in a single transaction.

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `seller` | `address payable` | The party who will receive funds |
| `arbiter` | `address` | Neutral third party for disputes |
| `duration` | `uint256` | Escrow duration in seconds (min: 1 day) |
| `description` | `string` | Text description of the agreement |
| `msg.value` | `ETH` | The escrow amount (must be > 0) |

**Returns**: The new escrow's ID
**Emits**: `EscrowCreated(...)`, `EscrowFunded(...)`

---

#### `release(uint256 escrowId)` -- onlyBuyer, nonReentrant

Releases funds to the seller minus platform fee (1%).

**Requires**: Escrow in `Funded` state
**Emits**: `EscrowReleased(escrowId, sellerAmount, fee)`

---

#### `refund(uint256 escrowId)` -- nonReentrant

Returns all funds to the buyer.
- **Seller** can refund at any time (voluntary)
- **Buyer** can refund only after the deadline has passed

**Requires**: Escrow in `Funded` state
**Emits**: `EscrowRefunded(escrowId, amount)`

---

#### `raiseDispute(uint256 escrowId)`

Transitions escrow to `Disputed` state. Only buyer or seller can raise.

**Requires**: Escrow in `Funded` state
**Emits**: `DisputeRaised(escrowId, raisedBy)`

---

#### `resolveDispute(uint256 escrowId, address recipient)` -- onlyArbiter, nonReentrant

Arbiter sends funds to the winning party (buyer or seller) minus platform fee.

**Requires**: Escrow in `Disputed` state, recipient must be buyer or seller
**Emits**: `DisputeResolved(escrowId, recipient, amount)`

---

#### `getEscrow(uint256 escrowId)` -- view returns (EscrowDetails)

Returns full details of an escrow.

#### `isExpired(uint256 escrowId)` -- view returns (bool)

Checks if the escrow deadline has passed.

#### `withdrawPlatformFees()` -- nonReentrant

Platform owner withdraws accumulated fees.

---

## 4. Voting

**File**: `contracts/Voting.sol`
**Purpose**: Decentralized voting with proposal creation, weighted voting, transitive delegation, and result finalization.

### Constructor

```solidity
constructor(
    string _title,
    uint256 _votingStart,
    uint256 _votingEnd,
    string[] proposalNames,
    string[] proposalDescriptions
)
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `_title` | `string` | Name of the voting session |
| `_votingStart` | `uint256` | Unix timestamp when voting begins |
| `_votingEnd` | `uint256` | Unix timestamp when voting ends |
| `proposalNames` | `string[]` | Array of proposal titles |
| `proposalDescriptions` | `string[]` | Array of proposal descriptions |

The deployer becomes the chairperson and is auto-registered as a voter.

### Functions

#### `registerVoter(address voter)` -- onlyChairperson

Registers a single voter with weight 1.

#### `registerVotersBatch(address[] voterAddresses)` -- onlyChairperson

Batch-registers multiple voters. Skips duplicates and zero addresses without reverting.

#### `addProposal(string name, string description)` -- onlyChairperson returns (uint256)

Adds a new proposal. Can be called before voting ends.

#### `vote(uint256 proposalId)` -- onlyDuringVoting, onlyRegistered

Casts a vote for the specified proposal. Vote weight may be > 1 if other voters delegated.

**Emits**: `VoteCast(voter, proposalId, weight)`

#### `delegate(address to)` -- onlyDuringVoting, onlyRegistered

Delegates your vote to another registered voter. Delegation is transitive (follows chain up to 50 levels). If the delegate already voted, weight is added to their chosen proposal.

**Emits**: `VoteDelegated(from, finalDelegate)`

#### `finalize()` -- onlyChairperson, onlyAfterVoting

Records the winning proposal permanently on-chain.

**Emits**: `VotingFinalized(winningProposalId, winnerName, voteCount)`

#### `extendVoting(uint256 newEnd)` -- onlyChairperson

Extends the voting deadline. Cannot shorten.

#### `getProposal(uint256 id)` -- view returns (string, string, uint256, address)

Returns proposal name, description, vote count, and proposer.

#### `getWinningProposal()` -- view returns (uint256)

Returns the index of the proposal with the most votes.

#### `getWinnerName()` -- view returns (string)

Returns the name of the winning proposal.

#### `getVotingSummary()` -- view returns (...)

Returns title, proposal count, registered voters, votes cast, active status, and finalized status.

---

## 5. NFTMarketplace (ERC-721)

**File**: `contracts/NFTMarketplace.sol`
**Purpose**: Full ERC-721 implementation with integrated marketplace for minting, listing, buying, and withdrawing proceeds. Includes platform fees and creator royalties.

### Constructor

```solidity
constructor(string _name, string _symbol, uint256 _platformFeeBps)
```

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `_name` | `string` | Collection name (e.g., "DevKit NFT") |
| `_symbol` | `string` | Collection symbol (e.g., "DKNFT") |
| `_platformFeeBps` | `uint256` | Platform fee in basis points (max 1000 = 10%) |

### Constants

| Name | Value | Description |
|:-----|:------|:------------|
| `CREATOR_ROYALTY_BPS` | 500 | 5% royalty on secondary sales |

### ERC-721 Functions

#### `balanceOf(address owner)` -- view returns (uint256)
#### `ownerOf(uint256 tokenId)` -- view returns (address)
#### `approve(address to, uint256 tokenId)`
#### `getApproved(uint256 tokenId)` -- view returns (address)
#### `setApprovalForAll(address operator, bool approved)`
#### `isApprovedForAll(address owner, address operator)` -- view returns (bool)
#### `transferFrom(address from, address to, uint256 tokenId)`
#### `safeTransferFrom(address from, address to, uint256 tokenId)`
#### `safeTransferFrom(address from, address to, uint256 tokenId, bytes data)`
#### `tokenURI(uint256 tokenId)` -- view returns (string)
#### `supportsInterface(bytes4 interfaceId)` -- pure returns (bool)

### Marketplace Functions

#### `mint(string uri)` -- returns (uint256 tokenId)

Mints a new NFT to the caller. The caller becomes both owner and creator. Token IDs start at 1 and auto-increment.

**Emits**: `Transfer(address(0), caller, tokenId)`, `ItemMinted(tokenId, creator, uri)`

---

#### `listItem(uint256 tokenId, uint256 price)`

Lists an owned NFT for sale.

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `tokenId` | `uint256` | The token to list |
| `price` | `uint256` | Sale price in wei (must be > 0) |

**Requires**: Caller must own the token, token must not already be listed.
**Emits**: `ItemListed(tokenId, seller, price)`

---

#### `buyItem(uint256 tokenId)` -- payable, nonReentrant

Purchases a listed NFT. Payment distribution:

| Recipient | Amount | Condition |
|:----------|:-------|:----------|
| Platform | `price * platformFeeBps / 10000` | Always |
| Creator | `price * 500 / 10000` (5%) | Only on secondary sales (creator != seller) |
| Seller | Remainder | Always |

Excess ETH is refunded to the buyer. Funds are not sent directly; they accumulate in `pendingWithdrawals` (pull payment pattern).

**Emits**: `ItemSold(tokenId, seller, buyer, price)`

---

#### `cancelListing(uint256 tokenId)`

Removes an active listing. Only the seller can cancel.

**Emits**: `ListingCanceled(tokenId, seller)`

---

#### `withdraw()` -- nonReentrant

Withdraws accumulated funds (sale proceeds, royalties, or platform fees) for the caller.

**Emits**: `Withdrawal(account, amount)`

---

#### `getListing(uint256 tokenId)` -- view returns (address, uint256, bool)

Returns seller address, price, and active status.

#### `updatePlatformFee(uint256 newFeeBps)` -- onlyContractOwner

Updates the platform fee (max 10%).

**Emits**: `PlatformFeeUpdated(newFeeBps)`

### Payment Flow Diagram

```
Buyer sends ETH
    |
    +---> Platform Fee (2.5%) ---> pendingWithdrawals[platformOwner]
    |
    +---> Creator Royalty (5%) --> pendingWithdrawals[creator]
    |     (only on secondary sales)
    |
    +---> Seller Proceeds -------> pendingWithdrawals[seller]
    |
    +---> Excess refund ---------> returned to buyer immediately

Each party calls withdraw() to claim their funds.
```
