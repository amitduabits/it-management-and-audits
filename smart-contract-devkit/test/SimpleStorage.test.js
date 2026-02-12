/**
 * SimpleStorage Contract Tests
 *
 * Tests cover:
 * - Deployment and initialization
 * - Setting and getting values
 * - Ownership and access control
 * - Increment and decrement operations
 * - Event emission verification
 * - Edge cases and error conditions
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("SimpleStorage", function () {
  let simpleStorage;
  let owner;
  let user1;
  let user2;

  const INITIAL_VALUE = 42;

  /**
   * Deploy a fresh contract before each test to ensure isolation.
   * Each test starts from a clean state.
   */
  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();

    const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
    simpleStorage = await SimpleStorage.deploy(INITIAL_VALUE);
    await simpleStorage.waitForDeployment();
  });

  // =========================================================================
  // Deployment Tests
  // =========================================================================

  describe("Deployment", function () {
    it("should set the deployer as owner", async function () {
      expect(await simpleStorage.owner()).to.equal(owner.address);
    });

    it("should store the initial value correctly", async function () {
      expect(await simpleStorage.get()).to.equal(INITIAL_VALUE);
    });

    it("should initialize update count to zero", async function () {
      expect(await simpleStorage.updateCount()).to.equal(0);
    });

    it("should deploy with zero initial value", async function () {
      const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
      const zeroStorage = await SimpleStorage.deploy(0);
      await zeroStorage.waitForDeployment();

      expect(await zeroStorage.get()).to.equal(0);
    });
  });

  // =========================================================================
  // Set and Get Tests
  // =========================================================================

  describe("Set and Get", function () {
    it("should update the stored value", async function () {
      await simpleStorage.set(100);
      expect(await simpleStorage.get()).to.equal(100);
    });

    it("should increment update count on each set", async function () {
      await simpleStorage.set(100);
      await simpleStorage.set(200);
      await simpleStorage.set(300);
      expect(await simpleStorage.updateCount()).to.equal(3);
    });

    it("should track the last value for each address", async function () {
      await simpleStorage.connect(user1).set(111);
      await simpleStorage.connect(user2).set(222);

      expect(await simpleStorage.lastValueByAddress(user1.address)).to.equal(111);
      expect(await simpleStorage.lastValueByAddress(user2.address)).to.equal(222);
    });

    it("should allow any address to set a value", async function () {
      await simpleStorage.connect(user1).set(999);
      expect(await simpleStorage.get()).to.equal(999);
    });

    it("should revert when setting the same value", async function () {
      await expect(simpleStorage.set(INITIAL_VALUE))
        .to.be.revertedWithCustomError(simpleStorage, "ValueUnchanged")
        .withArgs(INITIAL_VALUE);
    });

    it("should emit ValueChanged event with correct arguments", async function () {
      await expect(simpleStorage.set(100))
        .to.emit(simpleStorage, "ValueChanged")
        .withArgs(INITIAL_VALUE, 100, owner.address, await getBlockTimestamp());
    });

    it("should handle large values correctly", async function () {
      const largeValue = ethers.MaxUint256;
      await simpleStorage.set(largeValue);
      expect(await simpleStorage.get()).to.equal(largeValue);
    });
  });

  // =========================================================================
  // getDetails Tests
  // =========================================================================

  describe("getDetails", function () {
    it("should return correct initial details", async function () {
      const [value, updates, contractOwner] = await simpleStorage.getDetails();
      expect(value).to.equal(INITIAL_VALUE);
      expect(updates).to.equal(0);
      expect(contractOwner).to.equal(owner.address);
    });

    it("should return updated details after modifications", async function () {
      await simpleStorage.set(100);
      await simpleStorage.set(200);

      const [value, updates, contractOwner] = await simpleStorage.getDetails();
      expect(value).to.equal(200);
      expect(updates).to.equal(2);
      expect(contractOwner).to.equal(owner.address);
    });
  });

  // =========================================================================
  // Increment and Decrement Tests
  // =========================================================================

  describe("Increment", function () {
    it("should increment the value by the specified amount", async function () {
      await simpleStorage.increment(8);
      expect(await simpleStorage.get()).to.equal(INITIAL_VALUE + 8);
    });

    it("should increment by zero (edge case)", async function () {
      // Incrementing by 0 changes nothing but still counts as update
      // However, the value stays the same, so ValueChanged fires with same prev
      // Actually, 42 + 0 = 42, so the event will show 42 -> 42. Let's check:
      await simpleStorage.increment(0);
      expect(await simpleStorage.get()).to.equal(INITIAL_VALUE);
    });

    it("should revert on overflow", async function () {
      // Set to max uint, then try to increment
      await simpleStorage.set(ethers.MaxUint256);
      await expect(simpleStorage.increment(1)).to.be.reverted;
    });
  });

  describe("Decrement", function () {
    it("should decrement the value by the specified amount", async function () {
      await simpleStorage.decrement(2);
      expect(await simpleStorage.get()).to.equal(INITIAL_VALUE - 2);
    });

    it("should revert on underflow", async function () {
      await expect(simpleStorage.decrement(INITIAL_VALUE + 1)).to.be.reverted;
    });

    it("should decrement to zero", async function () {
      await simpleStorage.decrement(INITIAL_VALUE);
      expect(await simpleStorage.get()).to.equal(0);
    });
  });

  // =========================================================================
  // Reset Tests
  // =========================================================================

  describe("Reset", function () {
    it("should reset the value to zero", async function () {
      await simpleStorage.set(999);
      await simpleStorage.reset();
      expect(await simpleStorage.get()).to.equal(0);
    });

    it("should only allow owner to reset", async function () {
      await expect(simpleStorage.connect(user1).reset())
        .to.be.revertedWithCustomError(simpleStorage, "NotOwner")
        .withArgs(user1.address);
    });

    it("should increment update count on reset", async function () {
      await simpleStorage.reset();
      expect(await simpleStorage.updateCount()).to.equal(1);
    });
  });

  // =========================================================================
  // Ownership Tests
  // =========================================================================

  describe("Ownership", function () {
    it("should transfer ownership correctly", async function () {
      await simpleStorage.transferOwnership(user1.address);
      expect(await simpleStorage.owner()).to.equal(user1.address);
    });

    it("should emit OwnershipTransferred event", async function () {
      await expect(simpleStorage.transferOwnership(user1.address))
        .to.emit(simpleStorage, "OwnershipTransferred")
        .withArgs(owner.address, user1.address);
    });

    it("should not allow non-owner to transfer ownership", async function () {
      await expect(simpleStorage.connect(user1).transferOwnership(user2.address))
        .to.be.revertedWithCustomError(simpleStorage, "NotOwner");
    });

    it("should not allow transfer to zero address", async function () {
      await expect(simpleStorage.transferOwnership(ethers.ZeroAddress))
        .to.be.revertedWithCustomError(simpleStorage, "ZeroAddressNotAllowed");
    });

    it("new owner should be able to call owner-only functions", async function () {
      await simpleStorage.transferOwnership(user1.address);
      await simpleStorage.connect(user1).reset();
      expect(await simpleStorage.get()).to.equal(0);
    });

    it("previous owner should lose owner-only access after transfer", async function () {
      await simpleStorage.transferOwnership(user1.address);
      await expect(simpleStorage.reset())
        .to.be.revertedWithCustomError(simpleStorage, "NotOwner");
    });
  });

  // =========================================================================
  // Helper Functions
  // =========================================================================

  /**
   * Gets the timestamp of the latest block.
   * Useful for verifying event arguments that include timestamps.
   */
  async function getBlockTimestamp() {
    const block = await ethers.provider.getBlock("latest");
    return block.timestamp;
  }
});
