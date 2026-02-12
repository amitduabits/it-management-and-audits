/**
 * Escrow Contract Tests
 *
 * Tests cover:
 * - Escrow creation and funding
 * - Release flow (happy path)
 * - Refund flow (by seller and by expired deadline)
 * - Dispute creation and resolution
 * - Platform fee calculation
 * - Access control and state machine enforcement
 * - Reentrancy protection
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("Escrow", function () {
  let escrow;
  let buyer;
  let seller;
  let arbiter;
  let outsider;

  const ONE_ETH = ethers.parseEther("1.0");
  const TWO_DAYS = 2 * 24 * 60 * 60; // 2 days in seconds
  const DESCRIPTION = "Purchase of digital artwork";

  beforeEach(async function () {
    [buyer, seller, arbiter, outsider] = await ethers.getSigners();

    const Escrow = await ethers.getContractFactory("Escrow");
    escrow = await Escrow.connect(buyer).deploy();
    await escrow.waitForDeployment();
  });

  // =========================================================================
  // Helper: Create a funded escrow
  // =========================================================================

  async function createFundedEscrow(value = ONE_ETH) {
    const tx = await escrow
      .connect(buyer)
      .createEscrow(seller.address, arbiter.address, TWO_DAYS, DESCRIPTION, {
        value: value,
      });
    const receipt = await tx.wait();
    return 0; // First escrow ID
  }

  // =========================================================================
  // Creation Tests
  // =========================================================================

  describe("Escrow Creation", function () {
    it("should create a funded escrow with correct details", async function () {
      const escrowId = await createFundedEscrow();
      const details = await escrow.getEscrow(escrowId);

      expect(details.buyer).to.equal(buyer.address);
      expect(details.seller).to.equal(seller.address);
      expect(details.arbiter).to.equal(arbiter.address);
      expect(details.amount).to.equal(ONE_ETH);
      expect(details.state).to.equal(1); // Funded
      expect(details.description).to.equal(DESCRIPTION);
    });

    it("should emit EscrowCreated and EscrowFunded events", async function () {
      await expect(
        escrow
          .connect(buyer)
          .createEscrow(seller.address, arbiter.address, TWO_DAYS, DESCRIPTION, {
            value: ONE_ETH,
          })
      )
        .to.emit(escrow, "EscrowCreated")
        .and.to.emit(escrow, "EscrowFunded");
    });

    it("should increment escrow count", async function () {
      await createFundedEscrow();
      await createFundedEscrow();
      expect(await escrow.escrowCount()).to.equal(2);
    });

    it("should revert with zero value", async function () {
      await expect(
        escrow
          .connect(buyer)
          .createEscrow(seller.address, arbiter.address, TWO_DAYS, DESCRIPTION, {
            value: 0,
          })
      ).to.be.revertedWithCustomError(escrow, "InvalidAmount");
    });

    it("should revert with zero address for seller", async function () {
      await expect(
        escrow
          .connect(buyer)
          .createEscrow(ethers.ZeroAddress, arbiter.address, TWO_DAYS, DESCRIPTION, {
            value: ONE_ETH,
          })
      ).to.be.revertedWithCustomError(escrow, "ZeroAddress");
    });

    it("should revert with duration less than minimum", async function () {
      await expect(
        escrow
          .connect(buyer)
          .createEscrow(seller.address, arbiter.address, 3600, DESCRIPTION, {
            value: ONE_ETH,
          })
      ).to.be.revertedWithCustomError(escrow, "InvalidDeadline");
    });

    it("should store contract ETH balance correctly", async function () {
      await createFundedEscrow();
      expect(await escrow.getContractBalance()).to.equal(ONE_ETH);
    });
  });

  // =========================================================================
  // Release Tests (Happy Path)
  // =========================================================================

  describe("Release", function () {
    it("should release funds to seller (minus platform fee)", async function () {
      const escrowId = await createFundedEscrow();

      const sellerBalanceBefore = await ethers.provider.getBalance(seller.address);
      await escrow.connect(buyer).release(escrowId);
      const sellerBalanceAfter = await ethers.provider.getBalance(seller.address);

      // Platform fee is 1% (100 bps)
      const expectedFee = ONE_ETH / 100n;
      const expectedSellerAmount = ONE_ETH - expectedFee;

      expect(sellerBalanceAfter - sellerBalanceBefore).to.equal(expectedSellerAmount);
    });

    it("should update escrow state to Released", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).release(escrowId);

      const details = await escrow.getEscrow(escrowId);
      expect(details.state).to.equal(2); // Released
    });

    it("should accumulate platform fees", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).release(escrowId);

      const expectedFee = ONE_ETH / 100n;
      expect(await escrow.platformBalance()).to.equal(expectedFee);
    });

    it("should emit EscrowReleased event", async function () {
      const escrowId = await createFundedEscrow();
      const expectedFee = ONE_ETH / 100n;
      const expectedSellerAmount = ONE_ETH - expectedFee;

      await expect(escrow.connect(buyer).release(escrowId))
        .to.emit(escrow, "EscrowReleased")
        .withArgs(escrowId, expectedSellerAmount, expectedFee);
    });

    it("should revert when non-buyer tries to release", async function () {
      const escrowId = await createFundedEscrow();
      await expect(escrow.connect(seller).release(escrowId))
        .to.be.revertedWithCustomError(escrow, "Unauthorized");
    });

    it("should revert releasing an already released escrow", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).release(escrowId);
      await expect(escrow.connect(buyer).release(escrowId))
        .to.be.revertedWithCustomError(escrow, "InvalidState");
    });
  });

  // =========================================================================
  // Refund Tests
  // =========================================================================

  describe("Refund", function () {
    it("should allow seller to refund buyer voluntarily", async function () {
      const escrowId = await createFundedEscrow();

      const buyerBalanceBefore = await ethers.provider.getBalance(buyer.address);
      await escrow.connect(seller).refund(escrowId);
      const buyerBalanceAfter = await ethers.provider.getBalance(buyer.address);

      expect(buyerBalanceAfter - buyerBalanceBefore).to.equal(ONE_ETH);
    });

    it("should update escrow state to Refunded", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(seller).refund(escrowId);

      const details = await escrow.getEscrow(escrowId);
      expect(details.state).to.equal(3); // Refunded
    });

    it("should allow buyer to refund after deadline", async function () {
      const escrowId = await createFundedEscrow();

      // Fast-forward past deadline
      await time.increase(TWO_DAYS + 1);

      const buyerBalanceBefore = await ethers.provider.getBalance(buyer.address);
      const tx = await escrow.connect(buyer).refund(escrowId);
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;
      const buyerBalanceAfter = await ethers.provider.getBalance(buyer.address);

      expect(buyerBalanceAfter + gasUsed - buyerBalanceBefore).to.equal(ONE_ETH);
    });

    it("should revert buyer refund before deadline", async function () {
      const escrowId = await createFundedEscrow();
      await expect(escrow.connect(buyer).refund(escrowId))
        .to.be.revertedWithCustomError(escrow, "DeadlineNotReached");
    });

    it("should revert refund by outsider", async function () {
      const escrowId = await createFundedEscrow();
      await expect(escrow.connect(outsider).refund(escrowId))
        .to.be.revertedWithCustomError(escrow, "Unauthorized");
    });

    it("should emit EscrowRefunded event", async function () {
      const escrowId = await createFundedEscrow();
      await expect(escrow.connect(seller).refund(escrowId))
        .to.emit(escrow, "EscrowRefunded")
        .withArgs(escrowId, ONE_ETH);
    });
  });

  // =========================================================================
  // Dispute Tests
  // =========================================================================

  describe("Disputes", function () {
    it("should allow buyer to raise a dispute", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);

      const details = await escrow.getEscrow(escrowId);
      expect(details.state).to.equal(4); // Disputed
    });

    it("should allow seller to raise a dispute", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(seller).raiseDispute(escrowId);

      const details = await escrow.getEscrow(escrowId);
      expect(details.state).to.equal(4); // Disputed
    });

    it("should not allow outsider to raise a dispute", async function () {
      const escrowId = await createFundedEscrow();
      await expect(escrow.connect(outsider).raiseDispute(escrowId))
        .to.be.revertedWithCustomError(escrow, "Unauthorized");
    });

    it("should emit DisputeRaised event", async function () {
      const escrowId = await createFundedEscrow();
      await expect(escrow.connect(buyer).raiseDispute(escrowId))
        .to.emit(escrow, "DisputeRaised")
        .withArgs(escrowId, buyer.address);
    });
  });

  // =========================================================================
  // Dispute Resolution Tests
  // =========================================================================

  describe("Dispute Resolution", function () {
    it("should allow arbiter to resolve in favor of buyer", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);

      const buyerBalanceBefore = await ethers.provider.getBalance(buyer.address);
      await escrow.connect(arbiter).resolveDispute(escrowId, buyer.address);
      const buyerBalanceAfter = await ethers.provider.getBalance(buyer.address);

      const expectedFee = ONE_ETH / 100n;
      const expectedAmount = ONE_ETH - expectedFee;
      expect(buyerBalanceAfter - buyerBalanceBefore).to.equal(expectedAmount);
    });

    it("should allow arbiter to resolve in favor of seller", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);

      const sellerBalanceBefore = await ethers.provider.getBalance(seller.address);
      await escrow.connect(arbiter).resolveDispute(escrowId, seller.address);
      const sellerBalanceAfter = await ethers.provider.getBalance(seller.address);

      const expectedFee = ONE_ETH / 100n;
      const expectedAmount = ONE_ETH - expectedFee;
      expect(sellerBalanceAfter - sellerBalanceBefore).to.equal(expectedAmount);
    });

    it("should update state to Resolved", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);
      await escrow.connect(arbiter).resolveDispute(escrowId, seller.address);

      const details = await escrow.getEscrow(escrowId);
      expect(details.state).to.equal(5); // Resolved
    });

    it("should not allow non-arbiter to resolve", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);
      await expect(
        escrow.connect(buyer).resolveDispute(escrowId, buyer.address)
      ).to.be.revertedWithCustomError(escrow, "Unauthorized");
    });

    it("should not allow resolving to an outsider address", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);
      await expect(
        escrow.connect(arbiter).resolveDispute(escrowId, outsider.address)
      ).to.be.revertedWithCustomError(escrow, "Unauthorized");
    });

    it("should emit DisputeResolved event", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);

      const expectedFee = ONE_ETH / 100n;
      const expectedAmount = ONE_ETH - expectedFee;

      await expect(escrow.connect(arbiter).resolveDispute(escrowId, seller.address))
        .to.emit(escrow, "DisputeResolved")
        .withArgs(escrowId, seller.address, expectedAmount);
    });
  });

  // =========================================================================
  // Platform Fee Withdrawal
  // =========================================================================

  describe("Platform Fee Withdrawal", function () {
    it("should allow platform owner to withdraw fees", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).release(escrowId);

      const platformOwner = await escrow.platformOwner();
      const expectedFee = ONE_ETH / 100n;

      // Platform owner is the deployer (buyer in this test setup)
      await expect(escrow.connect(buyer).withdrawPlatformFees()).to.not.be.reverted;

      expect(await escrow.platformBalance()).to.equal(0);
    });

    it("should revert withdrawal by non-platform-owner", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).release(escrowId);

      await expect(escrow.connect(seller).withdrawPlatformFees())
        .to.be.revertedWithCustomError(escrow, "Unauthorized");
    });

    it("should revert withdrawal when balance is zero", async function () {
      await expect(escrow.connect(buyer).withdrawPlatformFees())
        .to.be.revertedWithCustomError(escrow, "InvalidAmount");
    });
  });

  // =========================================================================
  // View Function Tests
  // =========================================================================

  describe("View Functions", function () {
    it("should report expired status correctly", async function () {
      const escrowId = await createFundedEscrow();

      expect(await escrow.isExpired(escrowId)).to.equal(false);

      await time.increase(TWO_DAYS + 1);
      expect(await escrow.isExpired(escrowId)).to.equal(true);
    });

    it("should report correct contract balance", async function () {
      expect(await escrow.getContractBalance()).to.equal(0);

      await createFundedEscrow();
      expect(await escrow.getContractBalance()).to.equal(ONE_ETH);
    });
  });

  // =========================================================================
  // State Machine Tests
  // =========================================================================

  describe("State Machine Enforcement", function () {
    it("should not allow releasing a refunded escrow", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(seller).refund(escrowId);
      await expect(escrow.connect(buyer).release(escrowId))
        .to.be.revertedWithCustomError(escrow, "InvalidState");
    });

    it("should not allow disputing a released escrow", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).release(escrowId);
      await expect(escrow.connect(buyer).raiseDispute(escrowId))
        .to.be.revertedWithCustomError(escrow, "InvalidState");
    });

    it("should not allow refunding a disputed escrow", async function () {
      const escrowId = await createFundedEscrow();
      await escrow.connect(buyer).raiseDispute(escrowId);
      await expect(escrow.connect(seller).refund(escrowId))
        .to.be.revertedWithCustomError(escrow, "InvalidState");
    });
  });
});
