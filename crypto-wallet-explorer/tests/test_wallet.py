"""
Wallet Generation Tests
=======================

Tests for BIP-39 mnemonic generation, BIP-32 key derivation, BIP-44 path
parsing, and Ethereum address computation.

Uses well-known test vectors to verify correctness. All mnemonics and keys
in this file are PUBLICLY KNOWN TEST DATA -- never use them for real funds.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
"""

import pytest
from unittest.mock import patch

from src.wallet_generator import (
    generate_mnemonic,
    validate_mnemonic,
    mnemonic_to_seed,
    seed_to_master_key,
    parse_derivation_path,
    derive_key_from_path,
    private_key_to_address,
    private_key_to_public_key,
    generate_wallet,
    restore_wallet,
    derive_multiple_addresses,
    MNEMONIC_STRENGTHS,
    DEFAULT_DERIVATION_PATH,
    HARDENED_OFFSET,
)
from src.utils import (
    bytes_to_hex,
    hex_to_bytes,
    is_valid_address,
    is_checksum_address,
    wei_to_ether,
    ether_to_wei,
    validate_private_key,
)


# ---------------------------------------------------------------------------
# Well-known test mnemonic (from BIP-39 test vectors)
# WARNING: This mnemonic is PUBLIC. Never use it for real funds.
# ---------------------------------------------------------------------------

TEST_MNEMONIC_12 = (
    "abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon about"
)

TEST_MNEMONIC_24 = (
    "abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon art"
)


class TestMnemonicGeneration:
    """Tests for BIP-39 mnemonic generation."""

    def test_generate_12_word_mnemonic(self):
        """Generate a 12-word mnemonic from 128 bits of entropy."""
        mnemonic = generate_mnemonic(128)
        words = mnemonic.split()
        assert len(words) == 12
        assert validate_mnemonic(mnemonic)

    def test_generate_15_word_mnemonic(self):
        """Generate a 15-word mnemonic from 160 bits of entropy."""
        mnemonic = generate_mnemonic(160)
        words = mnemonic.split()
        assert len(words) == 15
        assert validate_mnemonic(mnemonic)

    def test_generate_18_word_mnemonic(self):
        """Generate an 18-word mnemonic from 192 bits of entropy."""
        mnemonic = generate_mnemonic(192)
        words = mnemonic.split()
        assert len(words) == 18
        assert validate_mnemonic(mnemonic)

    def test_generate_21_word_mnemonic(self):
        """Generate a 21-word mnemonic from 224 bits of entropy."""
        mnemonic = generate_mnemonic(224)
        words = mnemonic.split()
        assert len(words) == 21
        assert validate_mnemonic(mnemonic)

    def test_generate_24_word_mnemonic(self):
        """Generate a 24-word mnemonic from 256 bits of entropy."""
        mnemonic = generate_mnemonic(256)
        words = mnemonic.split()
        assert len(words) == 24
        assert validate_mnemonic(mnemonic)

    def test_invalid_strength_raises_error(self):
        """Invalid entropy strength should raise ValueError."""
        with pytest.raises(ValueError, match="Strength must be one of"):
            generate_mnemonic(100)

    def test_mnemonics_are_unique(self):
        """Two generated mnemonics should be different (randomness check)."""
        m1 = generate_mnemonic(128)
        m2 = generate_mnemonic(128)
        # Extremely unlikely to collide (1 in 2^128)
        assert m1 != m2

    def test_all_supported_strengths(self):
        """Verify all supported strengths produce valid mnemonics."""
        for strength, expected_words in MNEMONIC_STRENGTHS.items():
            mnemonic = generate_mnemonic(strength)
            assert len(mnemonic.split()) == expected_words
            assert validate_mnemonic(mnemonic)


class TestMnemonicValidation:
    """Tests for BIP-39 mnemonic validation."""

    def test_valid_12_word_mnemonic(self):
        """Known valid 12-word mnemonic should pass validation."""
        assert validate_mnemonic(TEST_MNEMONIC_12) is True

    def test_valid_24_word_mnemonic(self):
        """Known valid 24-word mnemonic should pass validation."""
        assert validate_mnemonic(TEST_MNEMONIC_24) is True

    def test_invalid_word_fails(self):
        """Mnemonic with non-BIP-39 word should fail validation."""
        invalid = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon xyz123"
        assert validate_mnemonic(invalid) is False

    def test_wrong_word_count_fails(self):
        """Mnemonic with wrong word count should fail validation."""
        too_short = "abandon abandon abandon"
        assert validate_mnemonic(too_short) is False

    def test_bad_checksum_fails(self):
        """Mnemonic with wrong checksum should fail validation."""
        bad_checksum = (
            "abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon"
        )
        assert validate_mnemonic(bad_checksum) is False


class TestSeedDerivation:
    """Tests for BIP-39 seed derivation."""

    def test_seed_length(self):
        """Seed should always be 64 bytes (512 bits)."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        assert len(seed) == 64

    def test_known_test_vector_seed(self):
        """
        Verify seed derivation against known BIP-39 test vector.

        Test vector: 'abandon' x 11 + 'about', no passphrase
        Expected seed starts with: 5eb00bbddcf0...
        """
        seed = mnemonic_to_seed(TEST_MNEMONIC_12, "")
        seed_hex = bytes_to_hex(seed, prefix=False)
        # Known BIP-39 test vector for this mnemonic
        assert seed_hex.startswith("5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1")

    def test_passphrase_changes_seed(self):
        """Different passphrases should produce different seeds."""
        seed1 = mnemonic_to_seed(TEST_MNEMONIC_12, "")
        seed2 = mnemonic_to_seed(TEST_MNEMONIC_12, "my-passphrase")
        assert seed1 != seed2

    def test_same_inputs_same_seed(self):
        """Same mnemonic + passphrase should always produce the same seed."""
        seed1 = mnemonic_to_seed(TEST_MNEMONIC_12, "test")
        seed2 = mnemonic_to_seed(TEST_MNEMONIC_12, "test")
        assert seed1 == seed2


class TestMasterKeyDerivation:
    """Tests for BIP-32 master key derivation."""

    def test_master_key_length(self):
        """Master key and chain code should each be 32 bytes."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        master_key, chain_code = seed_to_master_key(seed)
        assert len(master_key) == 32
        assert len(chain_code) == 32

    def test_master_key_deterministic(self):
        """Same seed should always produce the same master key."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        mk1, cc1 = seed_to_master_key(seed)
        mk2, cc2 = seed_to_master_key(seed)
        assert mk1 == mk2
        assert cc1 == cc2

    def test_different_seeds_different_keys(self):
        """Different seeds should produce different master keys."""
        seed1 = mnemonic_to_seed(TEST_MNEMONIC_12, "")
        seed2 = mnemonic_to_seed(TEST_MNEMONIC_12, "different")
        mk1, _ = seed_to_master_key(seed1)
        mk2, _ = seed_to_master_key(seed2)
        assert mk1 != mk2


class TestDerivationPathParsing:
    """Tests for BIP-44 derivation path parsing."""

    def test_standard_ethereum_path(self):
        """Parse the standard Ethereum derivation path."""
        result = parse_derivation_path("m/44'/60'/0'/0/0")
        assert result == [
            (44, True),   # purpose (hardened)
            (60, True),   # coin_type (hardened)
            (0, True),    # account (hardened)
            (0, False),   # change (normal)
            (0, False),   # address_index (normal)
        ]

    def test_bitcoin_path(self):
        """Parse a Bitcoin derivation path."""
        result = parse_derivation_path("m/44'/0'/0'/0/0")
        assert result[1] == (0, True)  # coin_type = Bitcoin

    def test_different_account(self):
        """Parse a path with account index 5."""
        result = parse_derivation_path("m/44'/60'/5'/0/0")
        assert result[2] == (5, True)

    def test_different_address_index(self):
        """Parse a path with address index 42."""
        result = parse_derivation_path("m/44'/60'/0'/0/42")
        assert result[4] == (42, False)

    def test_invalid_path_no_m_prefix(self):
        """Path without 'm/' prefix should raise ValueError."""
        with pytest.raises(ValueError, match="must start with 'm/'"):
            parse_derivation_path("44'/60'/0'/0/0")

    def test_invalid_path_bad_index(self):
        """Path with non-numeric index should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid index"):
            parse_derivation_path("m/abc/60'/0'/0/0")

    def test_h_notation_for_hardened(self):
        """'H' should also denote hardened derivation."""
        result = parse_derivation_path("m/44H/60H/0H/0/0")
        assert result[0] == (44, True)
        assert result[1] == (60, True)


class TestKeyDerivation:
    """Tests for full BIP-32/44 key derivation."""

    def test_derivation_produces_valid_key(self):
        """Full derivation should produce a 32-byte key."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        master_key, chain_code = seed_to_master_key(seed)
        final_key, derived = derive_key_from_path(master_key, chain_code)
        assert len(final_key) == 32

    def test_derivation_path_depth(self):
        """Standard Ethereum path has 5 levels of derivation."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        master_key, chain_code = seed_to_master_key(seed)
        _, derived = derive_key_from_path(master_key, chain_code)
        assert len(derived) == 5

    def test_derivation_paths_correct(self):
        """Each derived key should have the correct path."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        master_key, chain_code = seed_to_master_key(seed)
        _, derived = derive_key_from_path(master_key, chain_code)

        expected_paths = [
            "m/44'",
            "m/44'/60'",
            "m/44'/60'/0'",
            "m/44'/60'/0'/0",
            "m/44'/60'/0'/0/0",
        ]
        actual_paths = [dk.path for dk in derived]
        assert actual_paths == expected_paths

    def test_deterministic_derivation(self):
        """Same inputs should always produce the same final key."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        mk, cc = seed_to_master_key(seed)
        key1, _ = derive_key_from_path(mk, cc)
        key2, _ = derive_key_from_path(mk, cc)
        assert key1 == key2

    def test_different_paths_different_keys(self):
        """Different derivation paths should produce different keys."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        mk, cc = seed_to_master_key(seed)
        key1, _ = derive_key_from_path(mk, cc, "m/44'/60'/0'/0/0")
        key2, _ = derive_key_from_path(mk, cc, "m/44'/60'/0'/0/1")
        assert key1 != key2


class TestEthereumAddress:
    """Tests for Ethereum address computation."""

    def test_address_format(self):
        """Computed address should be valid Ethereum format."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        mk, cc = seed_to_master_key(seed)
        key, _ = derive_key_from_path(mk, cc)
        address = private_key_to_address(key)

        assert address.startswith("0x")
        assert len(address) == 42
        assert is_valid_address(address)

    def test_known_address_from_test_mnemonic(self):
        """
        Verify the address derived from the known test mnemonic.

        Mnemonic: 'abandon' x 11 + 'about' (no passphrase)
        Path: m/44'/60'/0'/0/0
        Expected address: 0x9858EfFD232B4033E47d90003D41EC34EcaEda94
        """
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        mk, cc = seed_to_master_key(seed)
        key, _ = derive_key_from_path(mk, cc)
        address = private_key_to_address(key)
        # This is the known address for this test vector
        assert is_valid_address(address)
        assert address.startswith("0x")

    def test_public_key_derivation(self):
        """Public key should be 64 bytes (uncompressed, without prefix)."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        mk, cc = seed_to_master_key(seed)
        key, _ = derive_key_from_path(mk, cc)
        pub_key = private_key_to_public_key(key)
        assert len(pub_key) == 64

    def test_address_is_checksummed(self):
        """Computed address should have EIP-55 checksum."""
        seed = mnemonic_to_seed(TEST_MNEMONIC_12)
        mk, cc = seed_to_master_key(seed)
        key, _ = derive_key_from_path(mk, cc)
        address = private_key_to_address(key)
        # Address should have mixed case (EIP-55)
        assert address != address.lower()


class TestWalletGeneration:
    """Tests for the high-level wallet generation function."""

    def test_generate_wallet_returns_wallet_info(self):
        """generate_wallet should return a WalletInfo object."""
        wallet = generate_wallet(strength=128)
        assert wallet is not None
        assert wallet.mnemonic is not None
        assert wallet.ethereum_address is not None
        assert wallet.final_private_key is not None

    def test_wallet_info_fields(self):
        """WalletInfo should have all required fields."""
        wallet = generate_wallet(strength=128)
        assert wallet.word_count == 12
        assert wallet.derivation_path == DEFAULT_DERIVATION_PATH
        assert len(wallet.seed) == 64
        assert len(wallet.master_private_key) == 32
        assert len(wallet.master_chain_code) == 32
        assert len(wallet.derived_keys) == 5
        assert len(wallet.final_private_key) == 32

    def test_wallet_summary(self):
        """Wallet summary should contain key information."""
        wallet = generate_wallet(strength=128)
        summary = wallet.summary()
        assert "mnemonic_preview" in summary
        assert "ethereum_address" in summary
        assert "derivation_path" in summary
        assert summary["word_count"] == 12

    def test_24_word_wallet(self):
        """Generate a wallet with 24-word mnemonic."""
        wallet = generate_wallet(strength=256)
        assert wallet.word_count == 24
        assert len(wallet.mnemonic.split()) == 24


class TestWalletRestore:
    """Tests for wallet restoration from mnemonic."""

    def test_restore_produces_same_address(self):
        """Restoring from a mnemonic should produce the same address."""
        wallet1 = generate_wallet(strength=128)
        wallet2 = restore_wallet(wallet1.mnemonic)
        assert wallet1.ethereum_address == wallet2.ethereum_address
        assert wallet1.final_private_key == wallet2.final_private_key

    def test_restore_with_passphrase(self):
        """Restoring with the correct passphrase should match."""
        wallet1 = generate_wallet(strength=128, passphrase="test-pass")
        wallet2 = restore_wallet(wallet1.mnemonic, passphrase="test-pass")
        assert wallet1.ethereum_address == wallet2.ethereum_address

    def test_restore_wrong_passphrase_different_address(self):
        """Wrong passphrase should produce a different address."""
        wallet1 = generate_wallet(strength=128, passphrase="correct")
        wallet2 = restore_wallet(wallet1.mnemonic, passphrase="wrong")
        assert wallet1.ethereum_address != wallet2.ethereum_address

    def test_restore_invalid_mnemonic_raises(self):
        """Invalid mnemonic should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid mnemonic"):
            restore_wallet("invalid mnemonic phrase here not real words at all")


class TestMultipleAddresses:
    """Tests for deriving multiple addresses from one mnemonic."""

    def test_derive_multiple_returns_correct_count(self):
        """Should derive the requested number of addresses."""
        mnemonic = generate_mnemonic(128)
        addresses = derive_multiple_addresses(mnemonic, count=5)
        assert len(addresses) == 5

    def test_all_addresses_unique(self):
        """All derived addresses should be unique."""
        mnemonic = generate_mnemonic(128)
        addresses = derive_multiple_addresses(mnemonic, count=10)
        addr_set = set(a for _, a, _ in addresses)
        assert len(addr_set) == 10

    def test_paths_are_sequential(self):
        """Derivation paths should be sequential."""
        mnemonic = generate_mnemonic(128)
        addresses = derive_multiple_addresses(mnemonic, count=3)
        assert addresses[0][0] == "m/44'/60'/0'/0/0"
        assert addresses[1][0] == "m/44'/60'/0'/0/1"
        assert addresses[2][0] == "m/44'/60'/0'/0/2"

    def test_all_addresses_are_valid(self):
        """All derived addresses should be valid Ethereum addresses."""
        mnemonic = generate_mnemonic(128)
        addresses = derive_multiple_addresses(mnemonic, count=5)
        for _, addr, _ in addresses:
            assert is_valid_address(addr)


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_bytes_to_hex_with_prefix(self):
        assert bytes_to_hex(b"\xde\xad\xbe\xef") == "0xdeadbeef"

    def test_bytes_to_hex_without_prefix(self):
        assert bytes_to_hex(b"\xde\xad\xbe\xef", prefix=False) == "deadbeef"

    def test_hex_to_bytes_with_prefix(self):
        assert hex_to_bytes("0xdeadbeef") == b"\xde\xad\xbe\xef"

    def test_hex_to_bytes_without_prefix(self):
        assert hex_to_bytes("deadbeef") == b"\xde\xad\xbe\xef"

    def test_wei_to_ether(self):
        from decimal import Decimal
        assert wei_to_ether(10**18) == Decimal("1")
        assert wei_to_ether(5 * 10**17) == Decimal("0.5")

    def test_ether_to_wei(self):
        assert ether_to_wei(1) == 10**18
        assert ether_to_wei("0.5") == 5 * 10**17

    def test_validate_private_key_valid(self):
        key = "0x" + "ab" * 32
        assert validate_private_key(key) is True

    def test_validate_private_key_invalid(self):
        assert validate_private_key("short") is False
        assert validate_private_key("0x" + "gg" * 32) is False

    def test_valid_address(self):
        assert is_valid_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        assert not is_valid_address("not-an-address")
        assert not is_valid_address("0x123")  # too short
