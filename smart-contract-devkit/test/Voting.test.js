/**
 * Voting Contract Tests
 *
 * Tests cover:
 * - Contract deployment and initialization
 * - Voter registration (single and batch)
 * - Proposal management
 * - Voting mechanics
 * - Vote delegation (including transitive delegation)
 * - Result tallying and finalization
 * - Time-based access control
 * - Edge cases and error conditions
 */

const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("Voting", function () {
  let voting;
  let chairperson;
  let voter1;
  let voter2;
  let voter3;
  let voter4;
  let outsider;

  const TITLE = "Board Election 2025";
  let votingStart;
  let votingEnd;

  const PROPOSAL_NAMES = ["Proposal Alpha", "Proposal Beta", "Proposal Gamma"];
  const PROPOSAL_DESCS = [
    "Expand operations to new markets",
    "Invest in research and development",
    "Increase community engagement programs",
  ];

  beforeEach(async function () {
    [chairperson, voter1, voter2, voter3, voter4, outsider] =
      await ethers.getSigners();

    // Set voting period: starts 1 minute from now, ends 1 day later
    const currentTime = await time.latest();
    votingStart = currentTime + 60;
    votingEnd = votingStart + 86400; // 24 hours

    const Voting = await ethers.getContractFactory("Voting");
    voting = await Voting.deploy(
      TITLE,
      votingStart,
      votingEnd,
      PROPOSAL_NAMES,
      PROPOSAL_DESCS
    );
    await voting.waitForDeployment();

    // Register voters
    await voting.registerVoter(voter1.address);
    await voting.registerVoter(voter2.address);
    await voting.registerVoter(voter3.address);
  });

  // =========================================================================
  // Deployment Tests
  // =========================================================================

  describe("Deployment", function () {
    it("should set the chairperson correctly", async function () {
      expect(await voting.chairperson()).to.equal(chairperson.address);
    });

    it("should set the voting title", async function () {
      expect(await voting.votingTitle()).to.equal(TITLE);
    });

    it("should create initial proposals", async function () {
      expect(await voting.getProposalCount()).to.equal(3);
    });

    it("should store proposal details correctly", async function () {
      const [name, description, voteCount, proposedBy] =
        await voting.getProposal(0);
      expect(name).to.equal(PROPOSAL_NAMES[0]);
      expect(description).to.equal(PROPOSAL_DESCS[0]);
      expect(voteCount).to.equal(0);
      expect(proposedBy).to.equal(chairperson.address);
    });

    it("should set correct voting period", async function () {
      expect(await voting.votingStart()).to.equal(votingStart);
      expect(await voting.votingEnd()).to.equal(votingEnd);
    });

    it("should register chairperson as voter automatically", async function () {
      expect(await voting.isRegistered(chairperson.address)).to.equal(true);
    });

    it("should revert if end <= start", async function () {
      const Voting = await ethers.getContractFactory("Voting");
      const now = await time.latest();
      await expect(
        Voting.deploy(TITLE, now + 100, now + 50, PROPOSAL_NAMES, PROPOSAL_DESCS)
      ).to.be.revertedWithCustomError(voting, "InvalidTimeRange");
    });

    it("should not be finalized initially", async function () {
      expect(await voting.finalized()).to.equal(false);
    });
  });

  // =========================================================================
  // Registration Tests
  // =========================================================================

  describe("Voter Registration", function () {
    it("should register a new voter", async function () {
      await voting.registerVoter(voter4.address);
      expect(await voting.isRegistered(voter4.address)).to.equal(true);
    });

    it("should increment total voters count", async function () {
      // chairperson + 3 voters = 4
      expect(await voting.totalVoters()).to.equal(4);
    });

    it("should emit VoterRegistered event", async function () {
      await expect(voting.registerVoter(voter4.address))
        .to.emit(voting, "VoterRegistered")
        .withArgs(voter4.address);
    });

    it("should revert duplicate registration", async function () {
      await expect(voting.registerVoter(voter1.address))
        .to.be.revertedWithCustomError(voting, "VoterAlreadyRegistered");
    });

    it("should revert registration of zero address", async function () {
      await expect(voting.registerVoter(ethers.ZeroAddress))
        .to.be.revertedWithCustomError(voting, "ZeroAddress");
    });

    it("should only allow chairperson to register voters", async function () {
      await expect(voting.connect(voter1).registerVoter(voter4.address))
        .to.be.revertedWithCustomError(voting, "NotChairperson");
    });
  });

  describe("Batch Registration", function () {
    it("should register multiple voters at once", async function () {
      const newVoters = [voter4.address, outsider.address];
      await voting.registerVotersBatch(newVoters);

      expect(await voting.isRegistered(voter4.address)).to.equal(true);
      expect(await voting.isRegistered(outsider.address)).to.equal(true);
    });

    it("should skip already registered voters without reverting", async function () {
      const mixedVoters = [voter1.address, voter4.address]; // voter1 already registered
      await voting.registerVotersBatch(mixedVoters);
      expect(await voting.isRegistered(voter4.address)).to.equal(true);
    });

    it("should emit VotersBatchRegistered event", async function () {
      await expect(voting.registerVotersBatch([voter4.address]))
        .to.emit(voting, "VotersBatchRegistered");
    });
  });

  // =========================================================================
  // Proposal Tests
  // =========================================================================

  describe("Proposal Management", function () {
    it("should allow chairperson to add proposals", async function () {
      await voting.addProposal("Proposal Delta", "A new initiative");
      expect(await voting.getProposalCount()).to.equal(4);
    });

    it("should emit ProposalCreated event", async function () {
      await expect(voting.addProposal("New Proposal", "Description"))
        .to.emit(voting, "ProposalCreated")
        .withArgs(3, "New Proposal", chairperson.address);
    });

    it("should not allow non-chairperson to add proposals", async function () {
      await expect(
        voting.connect(voter1).addProposal("Rogue Proposal", "Desc")
      ).to.be.revertedWithCustomError(voting, "NotChairperson");
    });
  });

  // =========================================================================
  // Voting Tests
  // =========================================================================

  describe("Voting", function () {
    beforeEach(async function () {
      // Advance to voting period
      await time.increaseTo(votingStart + 1);
    });

    it("should allow registered voter to cast a vote", async function () {
      await voting.connect(voter1).vote(0);
      expect(await voting.hasVoted(voter1.address)).to.equal(true);
    });

    it("should increment proposal vote count", async function () {
      await voting.connect(voter1).vote(0);
      const [, , voteCount] = await voting.getProposal(0);
      expect(voteCount).to.equal(1);
    });

    it("should increment total votes cast", async function () {
      await voting.connect(voter1).vote(0);
      await voting.connect(voter2).vote(1);
      expect(await voting.totalVotesCast()).to.equal(2);
    });

    it("should emit VoteCast event", async function () {
      await expect(voting.connect(voter1).vote(0))
        .to.emit(voting, "VoteCast")
        .withArgs(voter1.address, 0, 1);
    });

    it("should revert double voting", async function () {
      await voting.connect(voter1).vote(0);
      await expect(voting.connect(voter1).vote(1))
        .to.be.revertedWithCustomError(voting, "AlreadyVoted");
    });

    it("should revert vote from unregistered voter", async function () {
      await expect(voting.connect(outsider).vote(0))
        .to.be.revertedWithCustomError(voting, "VoterNotRegistered");
    });

    it("should revert vote for invalid proposal", async function () {
      await expect(voting.connect(voter1).vote(99))
        .to.be.revertedWithCustomError(voting, "InvalidProposal");
    });

    it("should revert vote before voting period", async function () {
      // Deploy a new contract with future voting start
      const now = await time.latest();
      const Voting = await ethers.getContractFactory("Voting");
      const futureVoting = await Voting.deploy(
        "Future Vote",
        now + 3600,
        now + 7200,
        ["A"],
        ["Desc A"]
      );
      await futureVoting.waitForDeployment();
      await futureVoting.registerVoter(voter1.address);

      await expect(futureVoting.connect(voter1).vote(0))
        .to.be.revertedWithCustomError(futureVoting, "VotingNotActive");
    });

    it("should revert vote after voting period", async function () {
      await time.increaseTo(votingEnd + 1);
      await expect(voting.connect(voter1).vote(0))
        .to.be.revertedWithCustomError(voting, "VotingNotActive");
    });
  });

  // =========================================================================
  // Delegation Tests
  // =========================================================================

  describe("Delegation", function () {
    beforeEach(async function () {
      await voting.registerVoter(voter4.address);
      await time.increaseTo(votingStart + 1);
    });

    it("should allow delegation to another voter", async function () {
      await voting.connect(voter1).delegate(voter2.address);
      expect(await voting.hasVoted(voter1.address)).to.equal(true);

      // voter2 should now have weight 2
      const voterInfo = await voting.voters(voter2.address);
      expect(voterInfo.weight).to.equal(2);
    });

    it("should emit VoteDelegated event", async function () {
      await expect(voting.connect(voter1).delegate(voter2.address))
        .to.emit(voting, "VoteDelegated")
        .withArgs(voter1.address, voter2.address);
    });

    it("should handle transitive delegation", async function () {
      // voter1 delegates to voter2, voter2 delegates to voter3
      await voting.connect(voter1).delegate(voter2.address);
      await voting.connect(voter2).delegate(voter3.address);

      // voter3 should have weight 3 (own + voter1 + voter2)
      const voterInfo = await voting.voters(voter3.address);
      expect(voterInfo.weight).to.equal(3);
    });

    it("should add weight to proposal if delegate already voted", async function () {
      // voter2 votes first
      await voting.connect(voter2).vote(1);

      // voter1 delegates to voter2 (who already voted)
      await voting.connect(voter1).delegate(voter2.address);

      // Proposal 1 should have 2 votes (voter2's 1 + voter1's 1)
      const [, , voteCount] = await voting.getProposal(1);
      expect(voteCount).to.equal(2);
    });

    it("should revert self-delegation", async function () {
      await expect(voting.connect(voter1).delegate(voter1.address))
        .to.be.revertedWithCustomError(voting, "SelfDelegationNotAllowed");
    });

    it("should revert delegation after already voting", async function () {
      await voting.connect(voter1).vote(0);
      await expect(voting.connect(voter1).delegate(voter2.address))
        .to.be.revertedWithCustomError(voting, "AlreadyVoted");
    });

    it("should revert delegation to unregistered voter", async function () {
      await expect(voting.connect(voter1).delegate(outsider.address))
        .to.be.revertedWithCustomError(voting, "VoterNotRegistered");
    });
  });

  // =========================================================================
  // Result and Finalization Tests
  // =========================================================================

  describe("Results and Finalization", function () {
    beforeEach(async function () {
      await time.increaseTo(votingStart + 1);

      // Cast votes: Proposal 1 gets 2 votes, others get 1 each
      await voting.connect(voter1).vote(1);
      await voting.connect(voter2).vote(1);
      await voting.connect(voter3).vote(0);
    });

    it("should return the winning proposal", async function () {
      expect(await voting.getWinningProposal()).to.equal(1);
    });

    it("should return the winner name", async function () {
      expect(await voting.getWinnerName()).to.equal("Proposal Beta");
    });

    it("should finalize after voting ends", async function () {
      await time.increaseTo(votingEnd + 1);
      await voting.finalize();

      expect(await voting.finalized()).to.equal(true);
      expect(await voting.winningProposalId()).to.equal(1);
    });

    it("should emit VotingFinalized event", async function () {
      await time.increaseTo(votingEnd + 1);
      await expect(voting.finalize())
        .to.emit(voting, "VotingFinalized")
        .withArgs(1, "Proposal Beta", 2);
    });

    it("should revert finalization during voting", async function () {
      await expect(voting.finalize())
        .to.be.revertedWithCustomError(voting, "VotingStillActive");
    });

    it("should revert double finalization", async function () {
      await time.increaseTo(votingEnd + 1);
      await voting.finalize();
      await expect(voting.finalize())
        .to.be.revertedWithCustomError(voting, "AlreadyFinalized");
    });

    it("should only allow chairperson to finalize", async function () {
      await time.increaseTo(votingEnd + 1);
      await expect(voting.connect(voter1).finalize())
        .to.be.revertedWithCustomError(voting, "NotChairperson");
    });
  });

  // =========================================================================
  // Voting Extension Tests
  // =========================================================================

  describe("Voting Extension", function () {
    it("should allow chairperson to extend voting", async function () {
      const newEnd = votingEnd + 86400;
      await voting.extendVoting(newEnd);
      expect(await voting.votingEnd()).to.equal(newEnd);
    });

    it("should emit VotingPeriodExtended event", async function () {
      const newEnd = votingEnd + 86400;
      await expect(voting.extendVoting(newEnd))
        .to.emit(voting, "VotingPeriodExtended")
        .withArgs(newEnd);
    });

    it("should revert shortening the voting period", async function () {
      await expect(voting.extendVoting(votingEnd - 100)).to.be.revertedWith(
        "New end must be after current end"
      );
    });
  });

  // =========================================================================
  // Summary View Tests
  // =========================================================================

  describe("Voting Summary", function () {
    it("should return correct summary before voting starts", async function () {
      const [title, proposalCount, registeredVoters, votesCast, isActive, isFinalized] =
        await voting.getVotingSummary();

      expect(title).to.equal(TITLE);
      expect(proposalCount).to.equal(3);
      expect(registeredVoters).to.equal(4); // chairperson + 3
      expect(votesCast).to.equal(0);
      expect(isActive).to.equal(false);
      expect(isFinalized).to.equal(false);
    });

    it("should reflect active status during voting period", async function () {
      await time.increaseTo(votingStart + 1);
      const [, , , , isActive] = await voting.getVotingSummary();
      expect(isActive).to.equal(true);
    });

    it("should reflect votes cast in summary", async function () {
      await time.increaseTo(votingStart + 1);
      await voting.connect(voter1).vote(0);
      await voting.connect(voter2).vote(1);

      const [, , , votesCast] = await voting.getVotingSummary();
      expect(votesCast).to.equal(2);
    });
  });
});
