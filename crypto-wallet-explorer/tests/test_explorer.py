"""
Explorer Function Tests
=======================

Tests for the transaction explorer, block explorer, and balance checker
modules. Uses mocked API responses to test without requiring network
access or API keys.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
All test data in this file is synthetic or from public testnets.
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.utils import (
    wei_to_ether,
    wei_to_gwei,
    ether_to_wei,
    gwei_to_wei,
    ether_to_gwei,
    format_wei,
    is_valid_address,
    is_valid_hex,
    truncate_hash,
    bytes_to_hex,
    hex_to_bytes,
    SEPOLIA_CHAIN_ID,
    WEI_PER_ETHER,
    WEI_PER_GWEI,
)

from src.transaction_builder import (
    TransactionRequest,
    build_transaction,
    build_legacy_transaction,
    analyze_transaction,
    estimate_transaction_cost,
    DEFAULT_GAS_LIMIT,
)

from src.transaction_explorer import (
    TransactionDetails,
    AddressTransaction,
    decode_input_data,
    format_transaction_for_display,
)

from src.block_explorer import (
    BlockInfo,
    BlockTransaction,
    get_block_statistics,
    format_block_for_display,
)

from src.balance_checker import (
    ETHBalance,
    TokenBalance,
    format_balance_report,
)


# ---------------------------------------------------------------------------
# Test addresses (not real -- for format testing only)
# ---------------------------------------------------------------------------

VALID_ADDRESS_1 = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
VALID_ADDRESS_2 = "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18"
INVALID_ADDRESS = "0xinvalid"


# ---------------------------------------------------------------------------
# Unit Conversion Tests
# ---------------------------------------------------------------------------

class TestUnitConversions:
    """Tests for wei/gwei/ether conversions."""

    def test_wei_to_ether_one(self):
        """1 ether = 10^18 wei."""
        assert wei_to_ether(10**18) == Decimal("1")

    def test_wei_to_ether_fractional(self):
        """Half an ether."""
        assert wei_to_ether(5 * 10**17) == Decimal("0.5")

    def test_wei_to_ether_zero(self):
        """Zero wei = zero ether."""
        assert wei_to_ether(0) == Decimal("0")

    def test_ether_to_wei_one(self):
        """1 ether -> 10^18 wei."""
        assert ether_to_wei(1) == 10**18

    def test_ether_to_wei_string(self):
        """String input should work."""
        assert ether_to_wei("0.001") == 10**15

    def test_ether_to_wei_decimal(self):
        """Decimal input should work."""
        assert ether_to_wei(Decimal("0.1")) == 10**17

    def test_wei_to_gwei(self):
        """1 gwei = 10^9 wei."""
        assert wei_to_gwei(10**9) == Decimal("1")

    def test_gwei_to_wei(self):
        """1 gwei -> 10^9 wei."""
        assert gwei_to_wei(1) == 10**9

    def test_ether_to_gwei(self):
        """1 ether = 10^9 gwei."""
        assert ether_to_gwei(1) == Decimal("1000000000")

    def test_roundtrip_wei_ether(self):
        """Converting to ether and back should preserve the value."""
        original = 123456789012345678
        assert ether_to_wei(wei_to_ether(original)) == original

    def test_roundtrip_wei_gwei(self):
        """Converting to gwei and back should preserve the value."""
        original = 20000000000
        assert gwei_to_wei(wei_to_gwei(original)) == original


class TestFormatWei:
    """Tests for the format_wei display function."""

    def test_format_wei_as_ether(self):
        result = format_wei(10**18, "ether")
        assert "1" in result
        assert "ETH" in result

    def test_format_wei_as_wei(self):
        result = format_wei(1000, "wei")
        assert "1000" in result
        assert "Wei" in result

    def test_format_invalid_unit(self):
        with pytest.raises(ValueError, match="Unknown unit"):
            format_wei(1000, "invalid")


# ---------------------------------------------------------------------------
# Hex Encoding Tests
# ---------------------------------------------------------------------------

class TestHexEncoding:
    """Tests for hex encoding/decoding utilities."""

    def test_bytes_to_hex_roundtrip(self):
        original = b"\x01\x02\x03\x04\x05"
        assert hex_to_bytes(bytes_to_hex(original)) == original

    def test_is_valid_hex_with_prefix(self):
        assert is_valid_hex("0xdeadbeef") is True

    def test_is_valid_hex_without_prefix(self):
        assert is_valid_hex("deadbeef") is True

    def test_is_valid_hex_invalid(self):
        assert is_valid_hex("not-hex") is False

    def test_is_valid_hex_empty(self):
        assert is_valid_hex("") is False

    def test_truncate_hash(self):
        full = "0x1234567890abcdef1234567890abcdef12345678"
        truncated = truncate_hash(full)
        assert "..." in truncated
        assert truncated.startswith("0x")
        assert len(truncated) < len(full)

    def test_truncate_short_hash(self):
        """Short hashes should not be truncated."""
        short = "0x1234"
        assert truncate_hash(short) == short


# ---------------------------------------------------------------------------
# Address Validation Tests
# ---------------------------------------------------------------------------

class TestAddressValidation:
    """Tests for Ethereum address validation."""

    def test_valid_address(self):
        assert is_valid_address(VALID_ADDRESS_1) is True

    def test_invalid_format(self):
        assert is_valid_address("not-an-address") is False

    def test_missing_prefix(self):
        assert is_valid_address("d8dA6BF26964aF9D7eEd9e03E53415D37aA96045") is False

    def test_too_short(self):
        assert is_valid_address("0x1234") is False

    def test_too_long(self):
        assert is_valid_address("0x" + "a" * 41) is False

    def test_zero_address(self):
        assert is_valid_address("0x" + "0" * 40) is True


# ---------------------------------------------------------------------------
# Transaction Builder Tests
# ---------------------------------------------------------------------------

class TestTransactionRequest:
    """Tests for TransactionRequest data class."""

    def test_default_values(self):
        req = TransactionRequest(to=VALID_ADDRESS_1)
        assert req.value_ether == 0.0
        assert req.gas_limit == DEFAULT_GAS_LIMIT
        assert req.chain_id == SEPOLIA_CHAIN_ID
        assert req.data == "0x"
        assert req.nonce is None

    def test_custom_values(self):
        req = TransactionRequest(
            to=VALID_ADDRESS_1,
            value_ether=0.5,
            gas_limit=50000,
            max_fee_per_gas_gwei=100.0,
            max_priority_fee_gwei=3.0,
        )
        assert req.value_ether == 0.5
        assert req.gas_limit == 50000


class TestBuildTransaction:
    """Tests for transaction building."""

    def test_build_eip1559_transaction(self):
        """Build an EIP-1559 transaction with valid parameters."""
        req = TransactionRequest(
            to=VALID_ADDRESS_1,
            value_ether=0.01,
            nonce=0,
        )
        tx = build_transaction(req, VALID_ADDRESS_2)

        assert tx["type"] == 2  # EIP-1559
        assert tx["chainId"] == SEPOLIA_CHAIN_ID
        assert tx["nonce"] == 0
        assert tx["value"] == ether_to_wei(0.01)
        assert tx["gas"] == DEFAULT_GAS_LIMIT

    def test_build_transaction_rejects_mainnet(self):
        """Building a transaction for mainnet should raise ValueError."""
        req = TransactionRequest(
            to=VALID_ADDRESS_1,
            chain_id=1,  # Mainnet
            nonce=0,
        )
        with pytest.raises(ValueError, match="Sepolia"):
            build_transaction(req, VALID_ADDRESS_2)

    def test_build_transaction_rejects_invalid_to(self):
        """Invalid recipient address should raise ValueError."""
        req = TransactionRequest(to=INVALID_ADDRESS, nonce=0)
        with pytest.raises(ValueError, match="Invalid"):
            build_transaction(req, VALID_ADDRESS_2)

    def test_build_transaction_rejects_invalid_from(self):
        """Invalid sender address should raise ValueError."""
        req = TransactionRequest(to=VALID_ADDRESS_1, nonce=0)
        with pytest.raises(ValueError, match="Invalid"):
            build_transaction(req, INVALID_ADDRESS)

    def test_build_legacy_transaction(self):
        """Build a legacy transaction."""
        req = TransactionRequest(
            to=VALID_ADDRESS_1,
            value_ether=0.01,
            nonce=0,
        )
        tx = build_legacy_transaction(req, VALID_ADDRESS_2)

        assert "gasPrice" in tx
        assert "maxFeePerGas" not in tx
        assert tx["chainId"] == SEPOLIA_CHAIN_ID


class TestAnalyzeTransaction:
    """Tests for transaction analysis."""

    def test_analyze_eip1559_transaction(self):
        tx = {
            "type": 2,
            "chainId": SEPOLIA_CHAIN_ID,
            "to": VALID_ADDRESS_1,
            "value": ether_to_wei(0.1),
            "gas": 21000,
            "maxFeePerGas": gwei_to_wei(50),
            "maxPriorityFeePerGas": gwei_to_wei(2),
            "nonce": 5,
        }
        analysis = analyze_transaction(tx)

        assert "EIP-1559" in analysis["Transaction Type"]
        assert "Sepolia" in analysis["Network"]
        assert "0.1" in analysis["Value"]
        assert "21000" in analysis["Gas Limit"]
        assert "5" == analysis["Nonce"]

    def test_analyze_legacy_transaction(self):
        tx = {
            "type": 0,
            "chainId": SEPOLIA_CHAIN_ID,
            "to": VALID_ADDRESS_1,
            "value": 0,
            "gas": 21000,
            "gasPrice": gwei_to_wei(20),
            "nonce": 0,
        }
        analysis = analyze_transaction(tx)
        assert "Legacy" in analysis["Transaction Type"]

    def test_analyze_contract_interaction(self):
        tx = {
            "chainId": SEPOLIA_CHAIN_ID,
            "to": VALID_ADDRESS_1,
            "value": 0,
            "gas": 100000,
            "maxFeePerGas": gwei_to_wei(50),
            "maxPriorityFeePerGas": gwei_to_wei(2),
            "nonce": 0,
            "data": "0xa9059cbb0000000000000000000000001234",
        }
        analysis = analyze_transaction(tx)
        assert "contract interaction" in analysis["Data"].lower() or "bytes" in analysis["Data"]

    def test_estimate_transaction_cost(self):
        estimate = estimate_transaction_cost(gas_limit=21000, max_fee_per_gas_gwei=50.0)
        assert "gas_limit" in estimate
        assert "max_transaction_cost_ether" in estimate
        assert "note" in estimate


# ---------------------------------------------------------------------------
# Transaction Details Tests
# ---------------------------------------------------------------------------

class TestTransactionDetails:
    """Tests for TransactionDetails data class."""

    def _make_tx_details(self, **kwargs):
        defaults = {
            "hash": "0x" + "ab" * 32,
            "block_number": 1000000,
            "block_hash": "0x" + "cd" * 32,
            "timestamp": 1700000000,
            "from_address": VALID_ADDRESS_1,
            "to_address": VALID_ADDRESS_2,
            "value_wei": ether_to_wei(1),
            "gas_limit": 21000,
            "gas_used": 21000,
            "gas_price_wei": gwei_to_wei(20),
            "nonce": 0,
            "input_data": "0x",
            "status": 1,
            "transaction_index": 0,
            "confirmations": 100,
        }
        defaults.update(kwargs)
        return TransactionDetails(**defaults)

    def test_value_ether(self):
        tx = self._make_tx_details(value_wei=ether_to_wei(2.5))
        assert "2.5" in tx.value_ether

    def test_status_text_success(self):
        tx = self._make_tx_details(status=1)
        assert tx.status_text == "Success"

    def test_status_text_failure(self):
        tx = self._make_tx_details(status=0)
        assert tx.status_text == "Failed"

    def test_transaction_fee(self):
        tx = self._make_tx_details(
            gas_used=21000,
            gas_price_wei=gwei_to_wei(20),
        )
        expected_fee = 21000 * gwei_to_wei(20)
        assert tx.transaction_fee_wei == expected_fee

    def test_is_contract_interaction_false(self):
        tx = self._make_tx_details(input_data="0x")
        assert tx.is_contract_interaction is False

    def test_is_contract_interaction_true(self):
        tx = self._make_tx_details(input_data="0xa9059cbb0000")
        assert tx.is_contract_interaction is True

    def test_timestamp_readable(self):
        tx = self._make_tx_details(timestamp=1700000000)
        assert "2023" in tx.timestamp_readable

    def test_to_dict(self):
        tx = self._make_tx_details()
        d = tx.to_dict()
        assert "Transaction Hash" in d
        assert "Status" in d
        assert "Value" in d
        assert "Gas Used" in d


class TestDecodeInputData:
    """Tests for transaction input data decoding."""

    def test_decode_empty_input(self):
        result = decode_input_data("0x")
        assert result["type"] == "Simple Transfer"

    def test_decode_none_input(self):
        result = decode_input_data(None)
        assert result["type"] == "Simple Transfer"

    def test_decode_erc20_transfer(self):
        # transfer(address,uint256) selector
        data = "0xa9059cbb" + "00" * 64
        result = decode_input_data(data)
        assert result["type"] == "Contract Interaction"
        assert "transfer" in result.get("function_name", "").lower()

    def test_decode_erc20_approve(self):
        data = "0x095ea7b3" + "00" * 64
        result = decode_input_data(data)
        assert "approve" in result.get("function_name", "").lower()

    def test_decode_unknown_selector(self):
        data = "0x12345678" + "00" * 32
        result = decode_input_data(data)
        assert "Unknown" in result.get("function_name", "")


# ---------------------------------------------------------------------------
# Block Explorer Tests
# ---------------------------------------------------------------------------

class TestBlockInfo:
    """Tests for BlockInfo data class."""

    def _make_block(self, **kwargs):
        defaults = {
            "number": 5000000,
            "hash": "0x" + "ab" * 32,
            "parent_hash": "0x" + "cd" * 32,
            "timestamp": 1700000000,
            "miner": VALID_ADDRESS_1,
            "gas_used": 15000000,
            "gas_limit": 30000000,
            "base_fee_per_gas": gwei_to_wei(20),
            "transaction_count": 150,
            "size": 50000,
            "extra_data": "0x",
            "transactions": [],
        }
        defaults.update(kwargs)
        return BlockInfo(**defaults)

    def test_gas_utilization(self):
        block = self._make_block(gas_used=15000000, gas_limit=30000000)
        assert block.gas_utilization == 50.0

    def test_gas_utilization_zero_limit(self):
        block = self._make_block(gas_used=0, gas_limit=0)
        assert block.gas_utilization == 0.0

    def test_base_fee_gwei(self):
        block = self._make_block(base_fee_per_gas=gwei_to_wei(25))
        assert "25" in block.base_fee_gwei

    def test_timestamp_readable(self):
        block = self._make_block(timestamp=1700000000)
        assert "2023" in block.timestamp_readable

    def test_to_dict(self):
        block = self._make_block()
        d = block.to_dict()
        assert "Block Number" in d
        assert "Gas Used" in d
        assert "Transactions" in d

    def test_block_statistics(self):
        block = self._make_block(transaction_count=200, gas_used=20000000)
        stats = get_block_statistics(block)
        assert stats["transaction_count"] == 200
        assert stats["is_empty"] is False

    def test_empty_block_statistics(self):
        block = self._make_block(transaction_count=0, gas_used=0)
        stats = get_block_statistics(block)
        assert stats["is_empty"] is True

    def test_format_block_display(self):
        block = self._make_block()
        formatted = format_block_for_display(block)
        assert "Block #" in formatted
        assert "Gas" in formatted


class TestBlockTransaction:
    """Tests for BlockTransaction data class."""

    def test_simple_transfer(self):
        tx = BlockTransaction(
            hash="0x" + "ab" * 32,
            from_address=VALID_ADDRESS_1,
            to_address=VALID_ADDRESS_2,
            value_wei=ether_to_wei(1),
            gas=21000,
            gas_price_wei=gwei_to_wei(20),
            nonce=0,
            transaction_index=0,
            input_data="0x",
        )
        assert tx.is_contract_interaction is False
        assert "1" in tx.value_ether

    def test_contract_interaction(self):
        tx = BlockTransaction(
            hash="0x" + "ab" * 32,
            from_address=VALID_ADDRESS_1,
            to_address=VALID_ADDRESS_2,
            value_wei=0,
            gas=100000,
            gas_price_wei=gwei_to_wei(20),
            nonce=1,
            transaction_index=5,
            input_data="0xa9059cbb" + "00" * 64,
        )
        assert tx.is_contract_interaction is True


# ---------------------------------------------------------------------------
# Balance Checker Tests
# ---------------------------------------------------------------------------

class TestETHBalance:
    """Tests for ETHBalance data class."""

    def test_balance_ether(self):
        bal = ETHBalance(
            address=VALID_ADDRESS_1,
            balance_wei=ether_to_wei(5),
        )
        assert bal.balance_ether == Decimal("5")

    def test_balance_formatted(self):
        bal = ETHBalance(
            address=VALID_ADDRESS_1,
            balance_wei=ether_to_wei(1.5),
        )
        assert "1.5" in bal.balance_formatted
        assert "ETH" in bal.balance_formatted

    def test_zero_balance(self):
        bal = ETHBalance(
            address=VALID_ADDRESS_1,
            balance_wei=0,
        )
        assert bal.balance_ether == Decimal("0")

    def test_to_dict(self):
        bal = ETHBalance(
            address=VALID_ADDRESS_1,
            balance_wei=ether_to_wei(1),
        )
        d = bal.to_dict()
        assert "Address" in d
        assert "Balance (ETH)" in d
        assert "Balance (Wei)" in d


class TestTokenBalance:
    """Tests for TokenBalance data class."""

    def test_formatted_balance_18_decimals(self):
        bal = TokenBalance(
            address=VALID_ADDRESS_1,
            token_address=VALID_ADDRESS_2,
            token_symbol="TEST",
            token_name="Test Token",
            decimals=18,
            raw_balance=10**18,
        )
        assert bal.formatted_balance == Decimal("1")

    def test_formatted_balance_6_decimals(self):
        bal = TokenBalance(
            address=VALID_ADDRESS_1,
            token_address=VALID_ADDRESS_2,
            token_symbol="USDC",
            token_name="USD Coin",
            decimals=6,
            raw_balance=1000000,
        )
        assert bal.formatted_balance == Decimal("1")

    def test_balance_string(self):
        bal = TokenBalance(
            address=VALID_ADDRESS_1,
            token_address=VALID_ADDRESS_2,
            token_symbol="DAI",
            token_name="Dai Stablecoin",
            decimals=18,
            raw_balance=5 * 10**18,
        )
        assert "5" in bal.balance_string
        assert "DAI" in bal.balance_string

    def test_to_dict(self):
        bal = TokenBalance(
            address=VALID_ADDRESS_1,
            token_address=VALID_ADDRESS_2,
            token_symbol="LINK",
            token_name="Chainlink",
            decimals=18,
            raw_balance=0,
        )
        d = bal.to_dict()
        assert "Token" in d
        assert "Contract" in d
        assert "Balance" in d


class TestBalanceReport:
    """Tests for balance report formatting."""

    def test_format_balance_report(self):
        report = {
            "address": VALID_ADDRESS_1,
            "network": "Sepolia Testnet",
            "eth_balance": {
                "Address": VALID_ADDRESS_1,
                "Balance (ETH)": "1.500000",
                "Balance (Wei)": "1,500,000,000,000,000,000",
            },
            "token_balances": [
                {
                    "Token": "Chainlink (LINK)",
                    "Balance": "100.000000 LINK",
                    "Contract": VALID_ADDRESS_2,
                },
            ],
            "warning": "TESTNET ONLY",
        }
        formatted = format_balance_report(report)
        assert "Balance Report" in formatted
        assert "Sepolia" in formatted
        assert "TESTNET" in formatted
