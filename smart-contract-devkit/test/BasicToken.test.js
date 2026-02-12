/**
 * BasicToken Contract Tests
 *
 * Tests cover:
 * - ERC-20 standard compliance
 * - Token deployment and initialization
 * - Transfers, approvals, and allowances
 * - Minting and burning
 * - Pausable functionality
 * - Edge cases and security scenarios
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BasicToken", function () {
  let token;
  let owner;
  let alice;
  let bob;
  let charlie;

  const TOKEN_NAME = "DevKit Token";
  const TOKEN_SYMBOL = "DKT";
  const INITIAL_SUPPLY = 1000000; // 1 million tokens (whole units)
  const MAX_CAP = 10000000;       // 10 million tokens (whole units)
  const DECIMALS = 18;

  // Helper: Convert whole tokens to smallest unit
  function tokens(amount) {
    return ethers.parseUnits(amount.toString(), DECIMALS);
  }

  beforeEach(async function () {
    [owner, alice, bob, charlie] = await ethers.getSigners();

    const BasicToken = await ethers.getContractFactory("BasicToken");
    token = await BasicToken.deploy(TOKEN_NAME, TOKEN_SYMBOL, INITIAL_SUPPLY, MAX_CAP);
    await token.waitForDeployment();
  });

  // =========================================================================
  // Deployment Tests
  // =========================================================================

  describe("Deployment", function () {
    it("should set the correct token name", async function () {
      expect(await token.name()).to.equal(TOKEN_NAME);
    });

    it("should set the correct token symbol", async function () {
      expect(await token.symbol()).to.equal(TOKEN_SYMBOL);
    });

    it("should set decimals to 18", async function () {
      expect(await token.decimals()).to.equal(DECIMALS);
    });

    it("should mint initial supply to deployer", async function () {
      expect(await token.balanceOf(owner.address)).to.equal(tokens(INITIAL_SUPPLY));
    });

    it("should set total supply to initial supply", async function () {
      expect(await token.totalSupply()).to.equal(tokens(INITIAL_SUPPLY));
    });

    it("should set the cap correctly", async function () {
      expect(await token.cap()).to.equal(tokens(MAX_CAP));
    });

    it("should set deployer as owner", async function () {
      expect(await token.owner()).to.equal(owner.address);
    });

    it("should not be paused initially", async function () {
      expect(await token.paused()).to.equal(false);
    });

    it("should revert if cap < initial supply", async function () {
      const BasicToken = await ethers.getContractFactory("BasicToken");
      await expect(
        BasicToken.deploy("Test", "TST", 100, 50)
      ).to.be.revertedWith("Cap must be >= initial supply");
    });
  });

  // =========================================================================
  // Transfer Tests
  // =========================================================================

  describe("Transfers", function () {
    it("should transfer tokens between accounts", async function () {
      const amount = tokens(100);
      await token.transfer(alice.address, amount);

      expect(await token.balanceOf(alice.address)).to.equal(amount);
      expect(await token.balanceOf(owner.address)).to.equal(
        tokens(INITIAL_SUPPLY) - amount
      );
    });

    it("should emit Transfer event", async function () {
      const amount = tokens(100);
      await expect(token.transfer(alice.address, amount))
        .to.emit(token, "Transfer")
        .withArgs(owner.address, alice.address, amount);
    });

    it("should revert when transferring more than balance", async function () {
      const tooMuch = tokens(INITIAL_SUPPLY + 1);
      await expect(token.transfer(alice.address, tooMuch))
        .to.be.revertedWithCustomError(token, "InsufficientBalance");
    });

    it("should revert when transferring to zero address", async function () {
      await expect(token.transfer(ethers.ZeroAddress, tokens(100)))
        .to.be.revertedWithCustomError(token, "ZeroAddress");
    });

    it("should handle zero-amount transfers", async function () {
      await expect(token.transfer(alice.address, 0)).to.not.be.reverted;
    });

    it("should allow chained transfers", async function () {
      const amount = tokens(50);
      await token.transfer(alice.address, amount);
      await token.connect(alice).transfer(bob.address, amount);
      expect(await token.balanceOf(bob.address)).to.equal(amount);
      expect(await token.balanceOf(alice.address)).to.equal(0);
    });
  });

  // =========================================================================
  // Approval & Allowance Tests
  // =========================================================================

  describe("Approvals and Allowances", function () {
    it("should approve a spender", async function () {
      await token.approve(alice.address, tokens(500));
      expect(await token.allowance(owner.address, alice.address)).to.equal(
        tokens(500)
      );
    });

    it("should emit Approval event", async function () {
      await expect(token.approve(alice.address, tokens(500)))
        .to.emit(token, "Approval")
        .withArgs(owner.address, alice.address, tokens(500));
    });

    it("should allow transferFrom with sufficient allowance", async function () {
      await token.approve(alice.address, tokens(200));
      await token.connect(alice).transferFrom(owner.address, bob.address, tokens(100));

      expect(await token.balanceOf(bob.address)).to.equal(tokens(100));
      expect(await token.allowance(owner.address, alice.address)).to.equal(
        tokens(100)
      );
    });

    it("should revert transferFrom with insufficient allowance", async function () {
      await token.approve(alice.address, tokens(50));
      await expect(
        token.connect(alice).transferFrom(owner.address, bob.address, tokens(100))
      ).to.be.revertedWithCustomError(token, "InsufficientAllowance");
    });

    it("should revert approval to zero address", async function () {
      await expect(token.approve(ethers.ZeroAddress, tokens(100)))
        .to.be.revertedWithCustomError(token, "ZeroAddress");
    });
  });

  // =========================================================================
  // Increase / Decrease Allowance Tests
  // =========================================================================

  describe("Increase and Decrease Allowance", function () {
    it("should increase allowance correctly", async function () {
      await token.approve(alice.address, tokens(100));
      await token.increaseAllowance(alice.address, tokens(50));
      expect(await token.allowance(owner.address, alice.address)).to.equal(
        tokens(150)
      );
    });

    it("should decrease allowance correctly", async function () {
      await token.approve(alice.address, tokens(100));
      await token.decreaseAllowance(alice.address, tokens(30));
      expect(await token.allowance(owner.address, alice.address)).to.equal(
        tokens(70)
      );
    });

    it("should revert decreasing allowance below zero", async function () {
      await token.approve(alice.address, tokens(50));
      await expect(token.decreaseAllowance(alice.address, tokens(100)))
        .to.be.revertedWithCustomError(token, "AllowanceUnderflow");
    });
  });

  // =========================================================================
  // Minting Tests
  // =========================================================================

  describe("Minting", function () {
    it("should allow owner to mint tokens", async function () {
      const mintAmount = tokens(1000);
      await token.mint(alice.address, mintAmount);

      expect(await token.balanceOf(alice.address)).to.equal(mintAmount);
      expect(await token.totalSupply()).to.equal(tokens(INITIAL_SUPPLY) + mintAmount);
    });

    it("should emit Transfer event from zero address on mint", async function () {
      await expect(token.mint(alice.address, tokens(1000)))
        .to.emit(token, "Transfer")
        .withArgs(ethers.ZeroAddress, alice.address, tokens(1000));
    });

    it("should revert minting beyond cap", async function () {
      const overCapAmount = tokens(MAX_CAP);
      await expect(token.mint(alice.address, overCapAmount))
        .to.be.revertedWithCustomError(token, "CapExceeded");
    });

    it("should not allow non-owner to mint", async function () {
      await expect(token.connect(alice).mint(bob.address, tokens(100)))
        .to.be.revertedWithCustomError(token, "NotOwner");
    });

    it("should revert minting to zero address", async function () {
      await expect(token.mint(ethers.ZeroAddress, tokens(100)))
        .to.be.revertedWithCustomError(token, "ZeroAddress");
    });
  });

  // =========================================================================
  // Burning Tests
  // =========================================================================

  describe("Burning", function () {
    it("should allow token holder to burn their tokens", async function () {
      const burnAmount = tokens(100);
      const initialBalance = await token.balanceOf(owner.address);

      await token.burn(burnAmount);

      expect(await token.balanceOf(owner.address)).to.equal(
        initialBalance - burnAmount
      );
      expect(await token.totalSupply()).to.equal(
        tokens(INITIAL_SUPPLY) - burnAmount
      );
    });

    it("should emit Transfer event to zero address on burn", async function () {
      await expect(token.burn(tokens(100)))
        .to.emit(token, "Transfer")
        .withArgs(owner.address, ethers.ZeroAddress, tokens(100));
    });

    it("should revert burning more than balance", async function () {
      await expect(token.connect(alice).burn(tokens(1)))
        .to.be.revertedWithCustomError(token, "InsufficientBalance");
    });
  });

  // =========================================================================
  // Pause Tests
  // =========================================================================

  describe("Pausable", function () {
    it("should allow owner to pause", async function () {
      await token.pause();
      expect(await token.paused()).to.equal(true);
    });

    it("should emit Paused event", async function () {
      await expect(token.pause())
        .to.emit(token, "Paused")
        .withArgs(owner.address);
    });

    it("should block transfers when paused", async function () {
      await token.pause();
      await expect(token.transfer(alice.address, tokens(100)))
        .to.be.revertedWithCustomError(token, "ContractPaused");
    });

    it("should block transferFrom when paused", async function () {
      await token.approve(alice.address, tokens(100));
      await token.pause();
      await expect(
        token.connect(alice).transferFrom(owner.address, bob.address, tokens(50))
      ).to.be.revertedWithCustomError(token, "ContractPaused");
    });

    it("should allow transfers after unpause", async function () {
      await token.pause();
      await token.unpause();
      await expect(token.transfer(alice.address, tokens(100))).to.not.be.reverted;
    });

    it("should not allow non-owner to pause", async function () {
      await expect(token.connect(alice).pause())
        .to.be.revertedWithCustomError(token, "NotOwner");
    });

    it("should revert if already paused", async function () {
      await token.pause();
      await expect(token.pause())
        .to.be.revertedWithCustomError(token, "ContractPaused");
    });

    it("should revert unpause when not paused", async function () {
      await expect(token.unpause())
        .to.be.revertedWithCustomError(token, "ContractNotPaused");
    });
  });

  // =========================================================================
  // Ownership Transfer Tests
  // =========================================================================

  describe("Ownership Transfer", function () {
    it("should transfer ownership", async function () {
      await token.transferOwnership(alice.address);
      expect(await token.owner()).to.equal(alice.address);
    });

    it("should emit OwnershipTransferred event", async function () {
      await expect(token.transferOwnership(alice.address))
        .to.emit(token, "OwnershipTransferred")
        .withArgs(owner.address, alice.address);
    });

    it("new owner should have minting rights", async function () {
      await token.transferOwnership(alice.address);
      await token.connect(alice).mint(bob.address, tokens(500));
      expect(await token.balanceOf(bob.address)).to.equal(tokens(500));
    });
  });
});
