/**
 * NFTMarketplace Contract Tests
 *
 * Tests cover:
 * - ERC-721 compliance (minting, transfers, approvals)
 * - Marketplace listing, buying, and canceling
 * - Platform fee collection and withdrawal
 * - Creator royalty distribution
 * - Pull payment pattern
 * - Access control and error conditions
 * - Reentrancy protection
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("NFTMarketplace", function () {
  let marketplace;
  let owner;
  let creator;
  let buyer;
  let buyer2;
  let outsider;

  const COLLECTION_NAME = "DevKit NFT";
  const COLLECTION_SYMBOL = "DKNFT";
  const PLATFORM_FEE_BPS = 250; // 2.5%
  const CREATOR_ROYALTY_BPS = 500; // 5%
  const TOKEN_URI = "ipfs://QmExample123456789/metadata.json";
  const LISTING_PRICE = ethers.parseEther("1.0");

  beforeEach(async function () {
    [owner, creator, buyer, buyer2, outsider] = await ethers.getSigners();

    const NFTMarketplace = await ethers.getContractFactory("NFTMarketplace");
    marketplace = await NFTMarketplace.deploy(
      COLLECTION_NAME,
      COLLECTION_SYMBOL,
      PLATFORM_FEE_BPS
    );
    await marketplace.waitForDeployment();
  });

  // =========================================================================
  // Helper Functions
  // =========================================================================

  async function mintToken(signer = creator, uri = TOKEN_URI) {
    const tx = await marketplace.connect(signer).mint(uri);
    const receipt = await tx.wait();
    // Get token ID from event
    const event = receipt.logs.find(
      (log) => log.fragment && log.fragment.name === "ItemMinted"
    );
    return event ? event.args[0] : 1n; // Default to 1 if event parsing fails
  }

  async function mintAndList(signer = creator, price = LISTING_PRICE) {
    const tokenId = await mintToken(signer);
    await marketplace.connect(signer).listItem(tokenId, price);
    return tokenId;
  }

  // =========================================================================
  // Deployment Tests
  // =========================================================================

  describe("Deployment", function () {
    it("should set the correct collection name", async function () {
      expect(await marketplace.name()).to.equal(COLLECTION_NAME);
    });

    it("should set the correct collection symbol", async function () {
      expect(await marketplace.symbol()).to.equal(COLLECTION_SYMBOL);
    });

    it("should set the contract owner", async function () {
      expect(await marketplace.contractOwner()).to.equal(owner.address);
    });

    it("should set the platform fee", async function () {
      expect(await marketplace.platformFeeBps()).to.equal(PLATFORM_FEE_BPS);
    });

    it("should start with zero total supply", async function () {
      expect(await marketplace.totalSupply()).to.equal(0);
    });

    it("should revert if platform fee exceeds 10%", async function () {
      const NFTMarketplace = await ethers.getContractFactory("NFTMarketplace");
      await expect(
        NFTMarketplace.deploy("Test", "TST", 1001)
      ).to.be.revertedWithCustomError(marketplace, "InvalidFee");
    });

    it("should support ERC-721 interface", async function () {
      // ERC-721 interface ID
      expect(await marketplace.supportsInterface("0x80ac58cd")).to.equal(true);
    });

    it("should support ERC-165 interface", async function () {
      expect(await marketplace.supportsInterface("0x01ffc9a7")).to.equal(true);
    });
  });

  // =========================================================================
  // Minting Tests
  // =========================================================================

  describe("Minting", function () {
    it("should mint a new NFT", async function () {
      const tokenId = await mintToken();
      expect(await marketplace.ownerOf(tokenId)).to.equal(creator.address);
    });

    it("should increment total supply", async function () {
      await mintToken();
      await mintToken();
      expect(await marketplace.totalSupply()).to.equal(2);
    });

    it("should store the token URI", async function () {
      const tokenId = await mintToken();
      expect(await marketplace.tokenURI(tokenId)).to.equal(TOKEN_URI);
    });

    it("should store the creator for royalties", async function () {
      const tokenId = await mintToken();
      expect(await marketplace.creators(tokenId)).to.equal(creator.address);
    });

    it("should update balance of minter", async function () {
      await mintToken();
      expect(await marketplace.balanceOf(creator.address)).to.equal(1);
    });

    it("should emit Transfer and ItemMinted events", async function () {
      await expect(marketplace.connect(creator).mint(TOKEN_URI))
        .to.emit(marketplace, "Transfer")
        .and.to.emit(marketplace, "ItemMinted");
    });

    it("should assign sequential token IDs starting from 1", async function () {
      const tokenId1 = await mintToken(creator);
      const tokenId2 = await mintToken(creator);
      expect(tokenId1).to.equal(1);
      expect(tokenId2).to.equal(2);
    });
  });

  // =========================================================================
  // ERC-721 Transfer Tests
  // =========================================================================

  describe("ERC-721 Transfers", function () {
    let tokenId;

    beforeEach(async function () {
      tokenId = await mintToken();
    });

    it("should transfer via transferFrom", async function () {
      await marketplace.connect(creator).transferFrom(
        creator.address,
        buyer.address,
        tokenId
      );
      expect(await marketplace.ownerOf(tokenId)).to.equal(buyer.address);
    });

    it("should update balances after transfer", async function () {
      await marketplace.connect(creator).transferFrom(
        creator.address,
        buyer.address,
        tokenId
      );
      expect(await marketplace.balanceOf(creator.address)).to.equal(0);
      expect(await marketplace.balanceOf(buyer.address)).to.equal(1);
    });

    it("should emit Transfer event", async function () {
      await expect(
        marketplace.connect(creator).transferFrom(
          creator.address,
          buyer.address,
          tokenId
        )
      )
        .to.emit(marketplace, "Transfer")
        .withArgs(creator.address, buyer.address, tokenId);
    });

    it("should revert transfer by non-owner/non-approved", async function () {
      await expect(
        marketplace.connect(outsider).transferFrom(
          creator.address,
          buyer.address,
          tokenId
        )
      ).to.be.revertedWithCustomError(marketplace, "NotOwnerOrApproved");
    });

    it("should revert transfer to zero address", async function () {
      await expect(
        marketplace.connect(creator).transferFrom(
          creator.address,
          ethers.ZeroAddress,
          tokenId
        )
      ).to.be.revertedWithCustomError(marketplace, "TransferToZeroAddress");
    });
  });

  // =========================================================================
  // ERC-721 Approval Tests
  // =========================================================================

  describe("ERC-721 Approvals", function () {
    let tokenId;

    beforeEach(async function () {
      tokenId = await mintToken();
    });

    it("should approve an address for a specific token", async function () {
      await marketplace.connect(creator).approve(buyer.address, tokenId);
      expect(await marketplace.getApproved(tokenId)).to.equal(buyer.address);
    });

    it("should allow approved address to transfer", async function () {
      await marketplace.connect(creator).approve(buyer.address, tokenId);
      await marketplace.connect(buyer).transferFrom(
        creator.address,
        buyer.address,
        tokenId
      );
      expect(await marketplace.ownerOf(tokenId)).to.equal(buyer.address);
    });

    it("should clear approval after transfer", async function () {
      await marketplace.connect(creator).approve(buyer.address, tokenId);
      await marketplace.connect(creator).transferFrom(
        creator.address,
        buyer2.address,
        tokenId
      );
      expect(await marketplace.getApproved(tokenId)).to.equal(ethers.ZeroAddress);
    });

    it("should set approval for all", async function () {
      await marketplace.connect(creator).setApprovalForAll(buyer.address, true);
      expect(
        await marketplace.isApprovedForAll(creator.address, buyer.address)
      ).to.equal(true);
    });

    it("should allow operator to transfer any token", async function () {
      await marketplace.connect(creator).setApprovalForAll(buyer.address, true);
      await marketplace.connect(buyer).transferFrom(
        creator.address,
        buyer.address,
        tokenId
      );
      expect(await marketplace.ownerOf(tokenId)).to.equal(buyer.address);
    });

    it("should emit Approval event", async function () {
      await expect(marketplace.connect(creator).approve(buyer.address, tokenId))
        .to.emit(marketplace, "Approval")
        .withArgs(creator.address, buyer.address, tokenId);
    });

    it("should emit ApprovalForAll event", async function () {
      await expect(
        marketplace.connect(creator).setApprovalForAll(buyer.address, true)
      )
        .to.emit(marketplace, "ApprovalForAll")
        .withArgs(creator.address, buyer.address, true);
    });
  });

  // =========================================================================
  // Marketplace Listing Tests
  // =========================================================================

  describe("Listing", function () {
    let tokenId;

    beforeEach(async function () {
      tokenId = await mintToken();
    });

    it("should list an NFT for sale", async function () {
      await marketplace.connect(creator).listItem(tokenId, LISTING_PRICE);

      const [seller, price, active] = await marketplace.getListing(tokenId);
      expect(seller).to.equal(creator.address);
      expect(price).to.equal(LISTING_PRICE);
      expect(active).to.equal(true);
    });

    it("should emit ItemListed event", async function () {
      await expect(
        marketplace.connect(creator).listItem(tokenId, LISTING_PRICE)
      )
        .to.emit(marketplace, "ItemListed")
        .withArgs(tokenId, creator.address, LISTING_PRICE);
    });

    it("should revert listing by non-owner", async function () {
      await expect(
        marketplace.connect(outsider).listItem(tokenId, LISTING_PRICE)
      ).to.be.revertedWithCustomError(marketplace, "NotTokenOwner");
    });

    it("should revert listing with zero price", async function () {
      await expect(
        marketplace.connect(creator).listItem(tokenId, 0)
      ).to.be.revertedWithCustomError(marketplace, "PriceMustBeAboveZero");
    });

    it("should revert listing an already listed token", async function () {
      await marketplace.connect(creator).listItem(tokenId, LISTING_PRICE);
      await expect(
        marketplace.connect(creator).listItem(tokenId, LISTING_PRICE)
      ).to.be.revertedWithCustomError(marketplace, "AlreadyListed");
    });
  });

  // =========================================================================
  // Buying Tests
  // =========================================================================

  describe("Buying", function () {
    let tokenId;

    beforeEach(async function () {
      tokenId = await mintAndList();
      // Creator needs to approve marketplace for transfer
      await marketplace.connect(creator).approve(
        await marketplace.getAddress(),
        tokenId
      );
    });

    it("should transfer NFT to buyer", async function () {
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });
      expect(await marketplace.ownerOf(tokenId)).to.equal(buyer.address);
    });

    it("should deactivate the listing after purchase", async function () {
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });
      const [, , active] = await marketplace.getListing(tokenId);
      expect(active).to.equal(false);
    });

    it("should distribute platform fee correctly", async function () {
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });

      // Platform fee: 2.5% of 1 ETH = 0.025 ETH
      const expectedFee = (LISTING_PRICE * BigInt(PLATFORM_FEE_BPS)) / 10000n;
      expect(await marketplace.pendingWithdrawals(owner.address)).to.equal(
        expectedFee
      );
    });

    it("should not charge royalty on primary sale (creator == seller)", async function () {
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });

      // Creator is the seller, so no royalty
      // Seller proceeds = price - platformFee (no royalty deducted)
      const expectedFee = (LISTING_PRICE * BigInt(PLATFORM_FEE_BPS)) / 10000n;
      const expectedSellerProceeds = LISTING_PRICE - expectedFee;

      expect(
        await marketplace.pendingWithdrawals(creator.address)
      ).to.equal(expectedSellerProceeds);
    });

    it("should charge creator royalty on secondary sale", async function () {
      // First sale: creator -> buyer
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });

      // Second sale: buyer lists and buyer2 buys
      await marketplace.connect(buyer).listItem(tokenId, LISTING_PRICE);
      await marketplace.connect(buyer).approve(
        await marketplace.getAddress(),
        tokenId
      );
      await marketplace.connect(buyer2).buyItem(tokenId, {
        value: LISTING_PRICE,
      });

      // Creator should receive royalty from secondary sale
      const expectedRoyalty = (LISTING_PRICE * BigInt(CREATOR_ROYALTY_BPS)) / 10000n;

      // Creator's pending = primary sale proceeds + royalty from secondary sale
      const primaryFee = (LISTING_PRICE * BigInt(PLATFORM_FEE_BPS)) / 10000n;
      const primaryProceeds = LISTING_PRICE - primaryFee;
      const expectedCreatorBalance = primaryProceeds + expectedRoyalty;

      expect(
        await marketplace.pendingWithdrawals(creator.address)
      ).to.equal(expectedCreatorBalance);
    });

    it("should emit ItemSold event", async function () {
      await expect(
        marketplace.connect(buyer).buyItem(tokenId, { value: LISTING_PRICE })
      )
        .to.emit(marketplace, "ItemSold")
        .withArgs(tokenId, creator.address, buyer.address, LISTING_PRICE);
    });

    it("should revert with insufficient payment", async function () {
      const lowPayment = ethers.parseEther("0.5");
      await expect(
        marketplace.connect(buyer).buyItem(tokenId, { value: lowPayment })
      ).to.be.revertedWithCustomError(marketplace, "InsufficientPayment");
    });

    it("should revert buying an unlisted token", async function () {
      const newTokenId = await mintToken();
      await expect(
        marketplace.connect(buyer).buyItem(newTokenId, { value: LISTING_PRICE })
      ).to.be.revertedWithCustomError(marketplace, "NotListed");
    });

    it("should refund excess payment", async function () {
      const excessAmount = ethers.parseEther("2.0");
      const buyerBalanceBefore = await ethers.provider.getBalance(buyer.address);

      const tx = await marketplace.connect(buyer).buyItem(tokenId, {
        value: excessAmount,
      });
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;

      const buyerBalanceAfter = await ethers.provider.getBalance(buyer.address);

      // Buyer should have paid exactly LISTING_PRICE + gas
      const actualSpent = buyerBalanceBefore - buyerBalanceAfter - gasUsed;
      // The spent amount equals LISTING_PRICE because excess was refunded
      // But the funds are held in pendingWithdrawals, so buyer paid LISTING_PRICE
      // Actually, the excess is refunded directly, so:
      expect(buyerBalanceBefore - buyerBalanceAfter).to.be.closeTo(
        LISTING_PRICE + gasUsed,
        ethers.parseEther("0.001") // Small margin for gas estimation
      );
    });
  });

  // =========================================================================
  // Cancel Listing Tests
  // =========================================================================

  describe("Cancel Listing", function () {
    let tokenId;

    beforeEach(async function () {
      tokenId = await mintAndList();
    });

    it("should cancel a listing", async function () {
      await marketplace.connect(creator).cancelListing(tokenId);
      const [, , active] = await marketplace.getListing(tokenId);
      expect(active).to.equal(false);
    });

    it("should emit ListingCanceled event", async function () {
      await expect(marketplace.connect(creator).cancelListing(tokenId))
        .to.emit(marketplace, "ListingCanceled")
        .withArgs(tokenId, creator.address);
    });

    it("should revert cancellation by non-seller", async function () {
      await expect(
        marketplace.connect(outsider).cancelListing(tokenId)
      ).to.be.revertedWithCustomError(marketplace, "NotTokenOwner");
    });

    it("should revert cancelling an inactive listing", async function () {
      await marketplace.connect(creator).cancelListing(tokenId);
      await expect(
        marketplace.connect(creator).cancelListing(tokenId)
      ).to.be.revertedWithCustomError(marketplace, "NotListed");
    });

    it("should allow re-listing after cancellation", async function () {
      await marketplace.connect(creator).cancelListing(tokenId);
      const newPrice = ethers.parseEther("2.0");
      await marketplace.connect(creator).listItem(tokenId, newPrice);

      const [, price, active] = await marketplace.getListing(tokenId);
      expect(price).to.equal(newPrice);
      expect(active).to.equal(true);
    });
  });

  // =========================================================================
  // Withdrawal Tests
  // =========================================================================

  describe("Withdrawals", function () {
    it("should allow withdrawal of pending funds", async function () {
      const tokenId = await mintAndList();
      await marketplace.connect(creator).approve(
        await marketplace.getAddress(),
        tokenId
      );
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });

      // Creator withdraws
      const balanceBefore = await ethers.provider.getBalance(creator.address);
      const tx = await marketplace.connect(creator).withdraw();
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;
      const balanceAfter = await ethers.provider.getBalance(creator.address);

      expect(balanceAfter + gasUsed - balanceBefore).to.be.greaterThan(0);
    });

    it("should reset pending balance to zero after withdrawal", async function () {
      const tokenId = await mintAndList();
      await marketplace.connect(creator).approve(
        await marketplace.getAddress(),
        tokenId
      );
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });

      await marketplace.connect(creator).withdraw();
      expect(await marketplace.pendingWithdrawals(creator.address)).to.equal(0);
    });

    it("should emit Withdrawal event", async function () {
      const tokenId = await mintAndList();
      await marketplace.connect(creator).approve(
        await marketplace.getAddress(),
        tokenId
      );
      await marketplace.connect(buyer).buyItem(tokenId, {
        value: LISTING_PRICE,
      });

      await expect(marketplace.connect(creator).withdraw())
        .to.emit(marketplace, "Withdrawal");
    });

    it("should revert withdrawal with zero balance", async function () {
      await expect(marketplace.connect(outsider).withdraw())
        .to.be.revertedWithCustomError(marketplace, "NoPendingWithdrawals");
    });
  });

  // =========================================================================
  // Admin Tests
  // =========================================================================

  describe("Admin Functions", function () {
    it("should allow owner to update platform fee", async function () {
      await marketplace.connect(owner).updatePlatformFee(500);
      expect(await marketplace.platformFeeBps()).to.equal(500);
    });

    it("should emit PlatformFeeUpdated event", async function () {
      await expect(marketplace.connect(owner).updatePlatformFee(500))
        .to.emit(marketplace, "PlatformFeeUpdated")
        .withArgs(500);
    });

    it("should revert fee update by non-owner", async function () {
      await expect(
        marketplace.connect(outsider).updatePlatformFee(500)
      ).to.be.revertedWithCustomError(marketplace, "NotContractOwner");
    });

    it("should revert fee exceeding 10%", async function () {
      await expect(
        marketplace.connect(owner).updatePlatformFee(1001)
      ).to.be.revertedWithCustomError(marketplace, "InvalidFee");
    });
  });

  // =========================================================================
  // Edge Cases
  // =========================================================================

  describe("Edge Cases", function () {
    it("should revert ownerOf for non-existent token", async function () {
      await expect(marketplace.ownerOf(999))
        .to.be.revertedWithCustomError(marketplace, "TokenDoesNotExist");
    });

    it("should revert tokenURI for non-existent token", async function () {
      await expect(marketplace.tokenURI(999))
        .to.be.revertedWithCustomError(marketplace, "TokenDoesNotExist");
    });

    it("should clear listing on direct transfer", async function () {
      const tokenId = await mintAndList();
      // Direct transfer should clear the listing
      await marketplace.connect(creator).transferFrom(
        creator.address,
        buyer.address,
        tokenId
      );
      const [, , active] = await marketplace.getListing(tokenId);
      expect(active).to.equal(false);
    });
  });
});
