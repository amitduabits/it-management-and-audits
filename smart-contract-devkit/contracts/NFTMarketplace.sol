// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title NFTMarketplace
 * @notice A full ERC-721 implementation with an integrated marketplace for
 *         minting, listing, buying, and canceling NFT sales.
 * @dev Implements the ERC-721 standard from scratch (no OpenZeppelin imports)
 *      with a built-in marketplace. This approach ensures full transparency
 *      of every line of logic.
 *
 *      ERC-721 Functions Implemented:
 *      - balanceOf, ownerOf
 *      - approve, getApproved
 *      - setApprovalForAll, isApprovedForAll
 *      - transferFrom, safeTransferFrom
 *
 *      Marketplace Functions:
 *      - mint: Create new NFTs with metadata URI
 *      - listItem: List an owned NFT for sale
 *      - buyItem: Purchase a listed NFT
 *      - cancelListing: Remove a listing
 *
 *      Security Patterns:
 *      - Reentrancy guard on all ETH-transferring functions
 *      - Checks-Effects-Interactions pattern throughout
 *      - Pull payment for royalties
 */
contract NFTMarketplace {
    // =========================================================================
    // ERC-721 State Variables
    // =========================================================================

    /// @notice Token name
    string public name;

    /// @notice Token symbol
    string public symbol;

    /// @notice Total tokens minted
    uint256 public totalSupply;

    /// @notice Maps token ID to owner address
    mapping(uint256 => address) private _owners;

    /// @notice Maps owner address to token count
    mapping(address => uint256) private _balances;

    /// @notice Maps token ID to approved address
    mapping(uint256 => address) private _tokenApprovals;

    /// @notice Maps owner => operator => approved status
    mapping(address => mapping(address => bool)) private _operatorApprovals;

    /// @notice Maps token ID to its metadata URI
    mapping(uint256 => string) private _tokenURIs;

    // =========================================================================
    // Marketplace State Variables
    // =========================================================================

    /// @notice Represents an active marketplace listing
    struct Listing {
        address seller;     // The address selling the NFT
        uint256 price;      // Sale price in wei
        bool active;        // Whether the listing is active
    }

    /// @notice The contract deployer / platform admin
    address public contractOwner;

    /// @notice Platform fee in basis points (250 = 2.5%)
    uint256 public platformFeeBps;

    /// @notice Maps token ID to its marketplace listing
    mapping(uint256 => Listing) public listings;

    /// @notice Maps addresses to their accumulated royalty/fee balance
    mapping(address => uint256) public pendingWithdrawals;

    /// @notice Reentrancy lock
    bool private _locked;

    /// @notice Next token ID to mint
    uint256 private _nextTokenId;

    /// @notice Maps token ID to its creator (for royalties)
    mapping(uint256 => address) public creators;

    /// @notice Creator royalty in basis points (500 = 5%)
    uint256 public constant CREATOR_ROYALTY_BPS = 500;

    // =========================================================================
    // ERC-721 Events
    // =========================================================================

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    // =========================================================================
    // Marketplace Events
    // =========================================================================

    event ItemMinted(uint256 indexed tokenId, address indexed creator, string tokenURI);
    event ItemListed(uint256 indexed tokenId, address indexed seller, uint256 price);
    event ItemSold(uint256 indexed tokenId, address indexed seller, address indexed buyer, uint256 price);
    event ListingCanceled(uint256 indexed tokenId, address indexed seller);
    event Withdrawal(address indexed account, uint256 amount);
    event PlatformFeeUpdated(uint256 newFeeBps);

    // =========================================================================
    // Custom Errors
    // =========================================================================

    error NotOwnerOrApproved();
    error TokenDoesNotExist(uint256 tokenId);
    error TransferToZeroAddress();
    error MintToZeroAddress();
    error ApprovalToCurrentOwner();
    error NotTokenOwner(uint256 tokenId);
    error AlreadyListed(uint256 tokenId);
    error NotListed(uint256 tokenId);
    error PriceMustBeAboveZero();
    error InsufficientPayment(uint256 required, uint256 sent);
    error NotContractOwner();
    error ReentrancyDetected();
    error TransferFailed();
    error NoPendingWithdrawals();
    error InvalidFee();
    error NotERC721Receiver();

    // =========================================================================
    // Modifiers
    // =========================================================================

    modifier nonReentrant() {
        if (_locked) revert ReentrancyDetected();
        _locked = true;
        _;
        _locked = false;
    }

    modifier onlyContractOwner() {
        if (msg.sender != contractOwner) revert NotContractOwner();
        _;
    }

    modifier tokenExists(uint256 tokenId) {
        if (_owners[tokenId] == address(0)) revert TokenDoesNotExist(tokenId);
        _;
    }

    // =========================================================================
    // Constructor
    // =========================================================================

    /**
     * @notice Deploys the NFT marketplace
     * @param _name Token collection name
     * @param _symbol Token collection symbol
     * @param _platformFeeBps Platform fee in basis points
     */
    constructor(string memory _name, string memory _symbol, uint256 _platformFeeBps) {
        if (_platformFeeBps > 1000) revert InvalidFee(); // Max 10%
        name = _name;
        symbol = _symbol;
        contractOwner = msg.sender;
        platformFeeBps = _platformFeeBps;
        _nextTokenId = 1; // Token IDs start at 1
    }

    // =========================================================================
    // ERC-721 Core Functions
    // =========================================================================

    /**
     * @notice Returns the number of tokens owned by an address
     * @param owner The address to query
     * @return The token count
     */
    function balanceOf(address owner) external view returns (uint256) {
        require(owner != address(0), "Query for zero address");
        return _balances[owner];
    }

    /**
     * @notice Returns the owner of a specific token
     * @param tokenId The token to query
     * @return The owner address
     */
    function ownerOf(uint256 tokenId) public view tokenExists(tokenId) returns (address) {
        return _owners[tokenId];
    }

    /**
     * @notice Approves another address to transfer a specific token
     * @param to The address to approve
     * @param tokenId The token to approve transfer of
     */
    function approve(address to, uint256 tokenId) external {
        address tokenOwner = ownerOf(tokenId);
        if (to == tokenOwner) revert ApprovalToCurrentOwner();
        require(
            msg.sender == tokenOwner || _operatorApprovals[tokenOwner][msg.sender],
            "Not owner or operator"
        );

        _tokenApprovals[tokenId] = to;
        emit Approval(tokenOwner, to, tokenId);
    }

    /**
     * @notice Returns the approved address for a token
     * @param tokenId The token to query
     * @return The approved address (or address(0) if none)
     */
    function getApproved(uint256 tokenId) public view tokenExists(tokenId) returns (address) {
        return _tokenApprovals[tokenId];
    }

    /**
     * @notice Grants or revokes operator status for all tokens
     * @param operator The address to modify permissions for
     * @param approved True to grant, false to revoke
     */
    function setApprovalForAll(address operator, bool approved) external {
        require(operator != msg.sender, "Cannot approve self");
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    /**
     * @notice Checks if an operator is approved for all tokens of an owner
     * @param owner The token owner
     * @param operator The operator to check
     * @return True if approved for all
     */
    function isApprovedForAll(address owner, address operator) public view returns (bool) {
        return _operatorApprovals[owner][operator];
    }

    /**
     * @notice Transfers a token from one address to another
     * @param from Current owner
     * @param to New owner
     * @param tokenId The token to transfer
     *
     * @dev Caller must be owner, approved, or operator
     */
    function transferFrom(address from, address to, uint256 tokenId) public {
        if (!_isApprovedOrOwner(msg.sender, tokenId)) revert NotOwnerOrApproved();
        _transfer(from, to, tokenId);
    }

    /**
     * @notice Safe transfer that checks if recipient can handle ERC-721
     * @param from Current owner
     * @param to New owner
     * @param tokenId The token to transfer
     */
    function safeTransferFrom(address from, address to, uint256 tokenId) external {
        safeTransferFrom(from, to, tokenId, "");
    }

    /**
     * @notice Safe transfer with additional data
     * @param from Current owner
     * @param to New owner
     * @param tokenId The token to transfer
     * @param data Additional data to pass to the receiver
     */
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory data) public {
        if (!_isApprovedOrOwner(msg.sender, tokenId)) revert NotOwnerOrApproved();
        _transfer(from, to, tokenId);

        // Check if recipient is a contract and supports ERC721Receiver
        if (to.code.length > 0) {
            try IERC721Receiver(to).onERC721Received(msg.sender, from, tokenId, data) returns (bytes4 retval) {
                if (retval != IERC721Receiver.onERC721Received.selector) {
                    revert NotERC721Receiver();
                }
            } catch {
                revert NotERC721Receiver();
            }
        }
    }

    /**
     * @notice Returns the metadata URI for a given token
     * @param tokenId The token to query
     * @return The URI string
     */
    function tokenURI(uint256 tokenId) external view tokenExists(tokenId) returns (string memory) {
        return _tokenURIs[tokenId];
    }

    // =========================================================================
    // Minting
    // =========================================================================

    /**
     * @notice Mints a new NFT to the caller's address
     * @param uri The metadata URI (typically an IPFS URL)
     * @return tokenId The ID of the newly minted token
     *
     * @dev Anyone can mint. The caller becomes both the owner and creator.
     *      The creator address is stored for royalty distribution on resales.
     */
    function mint(string calldata uri) external returns (uint256 tokenId) {
        if (msg.sender == address(0)) revert MintToZeroAddress();

        tokenId = _nextTokenId++;
        _owners[tokenId] = msg.sender;
        _balances[msg.sender] += 1;
        _tokenURIs[tokenId] = uri;
        creators[tokenId] = msg.sender;
        totalSupply += 1;

        emit Transfer(address(0), msg.sender, tokenId);
        emit ItemMinted(tokenId, msg.sender, uri);
    }

    // =========================================================================
    // Marketplace Functions
    // =========================================================================

    /**
     * @notice Lists an NFT for sale on the marketplace
     * @param tokenId The token to list
     * @param price The sale price in wei
     *
     * @dev The seller must own the token. The marketplace contract must be
     *      approved to transfer the token (via approve or setApprovalForAll).
     */
    function listItem(uint256 tokenId, uint256 price) external tokenExists(tokenId) {
        if (ownerOf(tokenId) != msg.sender) revert NotTokenOwner(tokenId);
        if (listings[tokenId].active) revert AlreadyListed(tokenId);
        if (price == 0) revert PriceMustBeAboveZero();

        listings[tokenId] = Listing({
            seller: msg.sender,
            price: price,
            active: true
        });

        emit ItemListed(tokenId, msg.sender, price);
    }

    /**
     * @notice Purchases a listed NFT
     * @param tokenId The token to buy
     *
     * @dev Distributes payment:
     *      1. Platform fee goes to pendingWithdrawals[contractOwner]
     *      2. Creator royalty goes to pendingWithdrawals[creator]
     *      3. Remainder goes to pendingWithdrawals[seller]
     *
     * Security:
     * - nonReentrant prevents reentrancy during purchase
     * - State is updated before any external interactions
     * - Uses pull payment pattern (funds accumulate in pendingWithdrawals)
     */
    function buyItem(uint256 tokenId)
        external
        payable
        nonReentrant
        tokenExists(tokenId)
    {
        Listing memory listing = listings[tokenId];
        if (!listing.active) revert NotListed(tokenId);
        if (msg.value < listing.price) {
            revert InsufficientPayment(listing.price, msg.value);
        }

        // Calculate fee distribution
        uint256 platformFee = (listing.price * platformFeeBps) / 10000;
        uint256 creatorRoyalty = 0;

        // Only charge royalty on secondary sales (creator != seller)
        address creator = creators[tokenId];
        if (creator != listing.seller) {
            creatorRoyalty = (listing.price * CREATOR_ROYALTY_BPS) / 10000;
        }

        uint256 sellerProceeds = listing.price - platformFee - creatorRoyalty;

        // Effects: Update state BEFORE any external calls
        delete listings[tokenId];

        // Accumulate funds (pull payment pattern)
        pendingWithdrawals[contractOwner] += platformFee;
        if (creatorRoyalty > 0) {
            pendingWithdrawals[creator] += creatorRoyalty;
        }
        pendingWithdrawals[listing.seller] += sellerProceeds;

        // Transfer the NFT to the buyer
        _transfer(listing.seller, msg.sender, tokenId);

        // Refund excess payment
        if (msg.value > listing.price) {
            uint256 refund = msg.value - listing.price;
            (bool success, ) = payable(msg.sender).call{value: refund}("");
            if (!success) revert TransferFailed();
        }

        emit ItemSold(tokenId, listing.seller, msg.sender, listing.price);
    }

    /**
     * @notice Cancels an active listing
     * @param tokenId The token listing to cancel
     * @dev Only the seller can cancel their own listing
     */
    function cancelListing(uint256 tokenId) external {
        Listing memory listing = listings[tokenId];
        if (!listing.active) revert NotListed(tokenId);
        if (listing.seller != msg.sender) revert NotTokenOwner(tokenId);

        delete listings[tokenId];

        emit ListingCanceled(tokenId, msg.sender);
    }

    /**
     * @notice Withdraws accumulated funds (sales proceeds, royalties, fees)
     * @dev Uses the pull payment pattern for security. Each participant
     *      withdraws their own funds rather than having funds pushed to them.
     */
    function withdraw() external nonReentrant {
        uint256 amount = pendingWithdrawals[msg.sender];
        if (amount == 0) revert NoPendingWithdrawals();

        // Effects before interaction
        pendingWithdrawals[msg.sender] = 0;

        (bool success, ) = payable(msg.sender).call{value: amount}("");
        if (!success) revert TransferFailed();

        emit Withdrawal(msg.sender, amount);
    }

    // =========================================================================
    // Admin Functions
    // =========================================================================

    /**
     * @notice Updates the platform fee
     * @param newFeeBps New fee in basis points (max 1000 = 10%)
     */
    function updatePlatformFee(uint256 newFeeBps) external onlyContractOwner {
        if (newFeeBps > 1000) revert InvalidFee();
        platformFeeBps = newFeeBps;
        emit PlatformFeeUpdated(newFeeBps);
    }

    // =========================================================================
    // View Functions
    // =========================================================================

    /**
     * @notice Returns full listing details
     * @param tokenId The token to query
     * @return seller The listing seller
     * @return price The listing price
     * @return active Whether the listing is active
     */
    function getListing(uint256 tokenId)
        external
        view
        returns (address seller, uint256 price, bool active)
    {
        Listing memory l = listings[tokenId];
        return (l.seller, l.price, l.active);
    }

    /**
     * @notice Checks ERC-165 interface support
     * @param interfaceId The interface identifier to check
     * @return True if the interface is supported
     */
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return
            interfaceId == 0x80ac58cd || // ERC-721
            interfaceId == 0x01ffc9a7;   // ERC-165
    }

    // =========================================================================
    // Internal Functions
    // =========================================================================

    /**
     * @dev Internal transfer logic
     */
    function _transfer(address from, address to, uint256 tokenId) internal {
        if (to == address(0)) revert TransferToZeroAddress();
        require(ownerOf(tokenId) == from, "Transfer from incorrect owner");

        // Clear approvals
        delete _tokenApprovals[tokenId];

        // Cancel any active listing
        if (listings[tokenId].active) {
            delete listings[tokenId];
        }

        _balances[from] -= 1;
        _balances[to] += 1;
        _owners[tokenId] = to;

        emit Transfer(from, to, tokenId);
    }

    /**
     * @dev Checks if an address is owner or approved for a token
     */
    function _isApprovedOrOwner(address spender, uint256 tokenId) internal view returns (bool) {
        address tokenOwner = ownerOf(tokenId);
        return (
            spender == tokenOwner ||
            getApproved(tokenId) == spender ||
            isApprovedForAll(tokenOwner, spender)
        );
    }
}

// =========================================================================
// ERC-721 Receiver Interface
// =========================================================================

/**
 * @title IERC721Receiver
 * @notice Interface for contracts that want to receive ERC-721 tokens via safeTransferFrom
 */
interface IERC721Receiver {
    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) external returns (bytes4);
}
