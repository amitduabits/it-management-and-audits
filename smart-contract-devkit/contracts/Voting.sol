// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Voting
 * @notice A decentralized voting system with proposal creation, weighted voting,
 *         delegation, and result tallying.
 * @dev Implements the following features:
 *      - Dynamic proposal creation by the chairperson
 *      - One-vote-per-address enforcement
 *      - Vote delegation (transitive -- if A delegates to B and B delegates to C,
 *        then A's vote ultimately goes to C)
 *      - Time-bound voting periods
 *      - Result tallying with tie detection
 *
 *      Security Considerations:
 *      - Only registered voters can participate
 *      - Delegation loops are prevented by checking chain length
 *      - Voting is time-restricted to prevent late manipulation
 *      - Double-voting is impossible due to boolean tracking
 */
contract Voting {
    // =========================================================================
    // Structs
    // =========================================================================

    /**
     * @notice Represents a single voter
     * @dev weight: Number of votes this voter controls (increases via delegation)
     *      voted: Whether this voter has already voted
     *      delegate: Address this voter has delegated to (address(0) if none)
     *      votedProposalId: The proposal this voter voted for (only valid if voted == true)
     */
    struct Voter {
        uint256 weight;
        bool voted;
        address delegate;
        uint256 votedProposalId;
    }

    /**
     * @notice Represents a voting proposal
     */
    struct Proposal {
        string name;           // Short title for the proposal
        string description;    // Detailed description
        uint256 voteCount;     // Accumulated vote count
        address proposedBy;    // Who created this proposal
        uint256 createdAt;     // Timestamp of creation
    }

    // =========================================================================
    // State Variables
    // =========================================================================

    /// @notice The address that created the voting contract and manages it
    address public chairperson;

    /// @notice The name/title of this voting session
    string public votingTitle;

    /// @notice Timestamp when voting begins
    uint256 public votingStart;

    /// @notice Timestamp when voting ends
    uint256 public votingEnd;

    /// @notice Whether the results have been finalized
    bool public finalized;

    /// @notice The ID of the winning proposal (set after finalization)
    uint256 public winningProposalId;

    /// @notice Total number of registered voters
    uint256 public totalVoters;

    /// @notice Total votes cast so far
    uint256 public totalVotesCast;

    /// @notice All proposals in this voting session
    Proposal[] public proposals;

    /// @notice Maps addresses to their voter information
    mapping(address => Voter) public voters;

    /// @notice Tracks whether an address is registered
    mapping(address => bool) public isRegistered;

    // =========================================================================
    // Events
    // =========================================================================

    event VoterRegistered(address indexed voter);
    event VotersBatchRegistered(uint256 count);
    event ProposalCreated(uint256 indexed proposalId, string name, address indexed proposedBy);
    event VoteCast(address indexed voter, uint256 indexed proposalId, uint256 weight);
    event VoteDelegated(address indexed from, address indexed to);
    event VotingFinalized(uint256 indexed winningProposalId, string winnerName, uint256 voteCount);
    event VotingPeriodExtended(uint256 newEnd);

    // =========================================================================
    // Custom Errors
    // =========================================================================

    error NotChairperson(address caller);
    error VoterAlreadyRegistered(address voter);
    error VoterNotRegistered(address voter);
    error AlreadyVoted(address voter);
    error VotingNotActive();
    error VotingStillActive();
    error InvalidProposal(uint256 proposalId);
    error AlreadyFinalized();
    error SelfDelegationNotAllowed();
    error DelegationLoopDetected();
    error DelegateAlreadyVoted();
    error InvalidTimeRange();
    error ZeroAddress();
    error NoProposals();

    // =========================================================================
    // Modifiers
    // =========================================================================

    modifier onlyChairperson() {
        if (msg.sender != chairperson) revert NotChairperson(msg.sender);
        _;
    }

    modifier onlyDuringVoting() {
        if (block.timestamp < votingStart || block.timestamp > votingEnd)
            revert VotingNotActive();
        _;
    }

    modifier onlyAfterVoting() {
        if (block.timestamp <= votingEnd) revert VotingStillActive();
        _;
    }

    modifier onlyRegistered(address voter) {
        if (!isRegistered[voter]) revert VoterNotRegistered(voter);
        _;
    }

    // =========================================================================
    // Constructor
    // =========================================================================

    /**
     * @notice Creates a new voting session
     * @param _title The name of this voting session
     * @param _votingStart Unix timestamp when voting begins
     * @param _votingEnd Unix timestamp when voting ends
     * @param proposalNames Array of initial proposal names
     * @param proposalDescriptions Array of initial proposal descriptions
     *
     * @dev The chairperson is automatically registered as a voter.
     */
    constructor(
        string memory _title,
        uint256 _votingStart,
        uint256 _votingEnd,
        string[] memory proposalNames,
        string[] memory proposalDescriptions
    ) {
        if (_votingEnd <= _votingStart) revert InvalidTimeRange();
        require(
            proposalNames.length == proposalDescriptions.length,
            "Mismatched arrays"
        );

        chairperson = msg.sender;
        votingTitle = _title;
        votingStart = _votingStart;
        votingEnd = _votingEnd;

        // Register chairperson as voter
        voters[msg.sender].weight = 1;
        isRegistered[msg.sender] = true;
        totalVoters = 1;

        // Create initial proposals
        for (uint256 i = 0; i < proposalNames.length; i++) {
            proposals.push(
                Proposal({
                    name: proposalNames[i],
                    description: proposalDescriptions[i],
                    voteCount: 0,
                    proposedBy: msg.sender,
                    createdAt: block.timestamp
                })
            );
            emit ProposalCreated(i, proposalNames[i], msg.sender);
        }

        emit VoterRegistered(msg.sender);
    }

    // =========================================================================
    // Registration Functions
    // =========================================================================

    /**
     * @notice Registers a single voter
     * @param voter The address to register
     * @dev Only the chairperson can register voters. Each voter starts with weight 1.
     */
    function registerVoter(address voter) external onlyChairperson {
        if (voter == address(0)) revert ZeroAddress();
        if (isRegistered[voter]) revert VoterAlreadyRegistered(voter);

        voters[voter].weight = 1;
        isRegistered[voter] = true;
        totalVoters++;

        emit VoterRegistered(voter);
    }

    /**
     * @notice Batch-registers multiple voters in a single transaction
     * @param voterAddresses Array of addresses to register
     * @dev More gas-efficient than calling registerVoter() multiple times
     */
    function registerVotersBatch(address[] calldata voterAddresses)
        external
        onlyChairperson
    {
        for (uint256 i = 0; i < voterAddresses.length; i++) {
            address voter = voterAddresses[i];
            if (voter == address(0)) continue;
            if (isRegistered[voter]) continue;

            voters[voter].weight = 1;
            isRegistered[voter] = true;
            totalVoters++;

            emit VoterRegistered(voter);
        }

        emit VotersBatchRegistered(voterAddresses.length);
    }

    // =========================================================================
    // Proposal Functions
    // =========================================================================

    /**
     * @notice Adds a new proposal to the ballot
     * @param name Short title for the proposal
     * @param description Detailed description
     * @return proposalId The index of the new proposal
     * @dev Only the chairperson can add proposals before voting starts
     */
    function addProposal(string calldata name, string calldata description)
        external
        onlyChairperson
        returns (uint256 proposalId)
    {
        require(block.timestamp < votingEnd, "Cannot add after voting ends");

        proposalId = proposals.length;
        proposals.push(
            Proposal({
                name: name,
                description: description,
                voteCount: 0,
                proposedBy: msg.sender,
                createdAt: block.timestamp
            })
        );

        emit ProposalCreated(proposalId, name, msg.sender);
    }

    // =========================================================================
    // Voting Functions
    // =========================================================================

    /**
     * @notice Casts a vote for a specific proposal
     * @param proposalId The index of the proposal to vote for
     *
     * @dev Requirements:
     *      - Caller must be a registered voter
     *      - Caller must not have already voted
     *      - Voting must be within the active period
     *      - proposalId must be valid
     *
     *      The vote is weighted by the voter's weight (which may be > 1 if
     *      other voters delegated to this voter).
     */
    function vote(uint256 proposalId)
        external
        onlyDuringVoting
        onlyRegistered(msg.sender)
    {
        Voter storage sender = voters[msg.sender];

        if (sender.voted) revert AlreadyVoted(msg.sender);
        if (proposalId >= proposals.length) revert InvalidProposal(proposalId);

        // Mark as voted before updating proposal (checks-effects-interactions)
        sender.voted = true;
        sender.votedProposalId = proposalId;

        proposals[proposalId].voteCount += sender.weight;
        totalVotesCast += sender.weight;

        emit VoteCast(msg.sender, proposalId, sender.weight);
    }

    /**
     * @notice Delegates your vote to another registered voter
     * @param to The address to delegate to
     *
     * @dev Delegation is transitive: if A -> B -> C, then A's weight goes to C.
     *      This function follows the delegation chain to find the final delegate.
     *
     *      Security:
     *      - Self-delegation is not allowed
     *      - Loop detection with max chain length of 50
     *      - Cannot delegate if you have already voted
     *      - If the final delegate has already voted, the weight is added
     *        directly to the proposal they voted for
     */
    function delegate(address to)
        external
        onlyDuringVoting
        onlyRegistered(msg.sender)
        onlyRegistered(to)
    {
        Voter storage sender = voters[msg.sender];

        if (sender.voted) revert AlreadyVoted(msg.sender);
        if (to == msg.sender) revert SelfDelegationNotAllowed();

        // Follow the delegation chain to the final delegate
        // Limit chain length to prevent gas exhaustion attacks
        address currentDelegate = to;
        for (uint256 i = 0; i < 50; i++) {
            address nextDelegate = voters[currentDelegate].delegate;
            if (nextDelegate == address(0)) break;
            if (nextDelegate == msg.sender) revert DelegationLoopDetected();
            currentDelegate = nextDelegate;
        }

        // Mark sender as having voted (delegating counts as voting)
        sender.voted = true;
        sender.delegate = to;

        Voter storage finalDelegate = voters[currentDelegate];

        if (finalDelegate.voted) {
            // If the delegate already voted, add weight to their chosen proposal
            proposals[finalDelegate.votedProposalId].voteCount += sender.weight;
            totalVotesCast += sender.weight;
        } else {
            // Otherwise, increase the delegate's voting weight
            finalDelegate.weight += sender.weight;
        }

        emit VoteDelegated(msg.sender, currentDelegate);
    }

    // =========================================================================
    // Result Functions
    // =========================================================================

    /**
     * @notice Determines the winning proposal
     * @return winningId The index of the proposal with the most votes
     * @dev Can be called by anyone after voting ends. Does not modify state.
     */
    function getWinningProposal() public view returns (uint256 winningId) {
        if (proposals.length == 0) revert NoProposals();

        uint256 highestVoteCount = 0;
        for (uint256 i = 0; i < proposals.length; i++) {
            if (proposals[i].voteCount > highestVoteCount) {
                highestVoteCount = proposals[i].voteCount;
                winningId = i;
            }
        }
    }

    /**
     * @notice Returns the name of the winning proposal
     * @return The name string of the winning proposal
     */
    function getWinnerName() external view returns (string memory) {
        return proposals[getWinningProposal()].name;
    }

    /**
     * @notice Finalizes the voting session and records the winner
     * @dev Only callable by the chairperson after voting ends.
     *      Once finalized, the result is permanently recorded on-chain.
     */
    function finalize() external onlyChairperson onlyAfterVoting {
        if (finalized) revert AlreadyFinalized();
        if (proposals.length == 0) revert NoProposals();

        finalized = true;
        winningProposalId = getWinningProposal();

        Proposal memory winner = proposals[winningProposalId];
        emit VotingFinalized(winningProposalId, winner.name, winner.voteCount);
    }

    /**
     * @notice Extends the voting deadline
     * @param newEnd The new end timestamp (must be after current end)
     * @dev Only the chairperson can extend. Cannot shorten the period.
     */
    function extendVoting(uint256 newEnd) external onlyChairperson {
        require(newEnd > votingEnd, "New end must be after current end");
        require(!finalized, "Already finalized");

        votingEnd = newEnd;
        emit VotingPeriodExtended(newEnd);
    }

    // =========================================================================
    // View / Utility Functions
    // =========================================================================

    /**
     * @notice Returns the total number of proposals
     * @return The number of proposals
     */
    function getProposalCount() external view returns (uint256) {
        return proposals.length;
    }

    /**
     * @notice Returns full details of a proposal
     * @param proposalId The index of the proposal
     * @return name The proposal name
     * @return description The proposal description
     * @return voteCount The current vote count
     * @return proposedBy Who created the proposal
     */
    function getProposal(uint256 proposalId)
        external
        view
        returns (
            string memory name,
            string memory description,
            uint256 voteCount,
            address proposedBy
        )
    {
        if (proposalId >= proposals.length) revert InvalidProposal(proposalId);
        Proposal memory p = proposals[proposalId];
        return (p.name, p.description, p.voteCount, p.proposedBy);
    }

    /**
     * @notice Checks if a given address has voted
     * @param voter The address to check
     * @return True if the voter has voted or delegated
     */
    function hasVoted(address voter) external view returns (bool) {
        return voters[voter].voted;
    }

    /**
     * @notice Returns a summary of the current voting status
     * @return title The voting session title
     * @return proposalCount Number of proposals
     * @return registeredVoters Number of registered voters
     * @return votesCast Total votes cast so far
     * @return isActive Whether voting is currently open
     * @return isFinalized Whether results have been finalized
     */
    function getVotingSummary()
        external
        view
        returns (
            string memory title,
            uint256 proposalCount,
            uint256 registeredVoters,
            uint256 votesCast,
            bool isActive,
            bool isFinalized
        )
    {
        bool active = (block.timestamp >= votingStart && block.timestamp <= votingEnd);
        return (
            votingTitle,
            proposals.length,
            totalVoters,
            totalVotesCast,
            active,
            finalized
        );
    }
}
