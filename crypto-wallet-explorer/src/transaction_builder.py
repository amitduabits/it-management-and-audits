"""
Transaction Builder Module
==========================

Provides tools for constructing, signing, and analyzing raw Ethereum
transactions on the Sepolia testnet. Demonstrates the anatomy of an
Ethereum transaction including EIP-1559 (Type 2) transactions.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
==============================================
This module is designed EXCLUSIVELY for Sepolia testnet transactions.
NEVER use it with mainnet. NEVER fund generated wallets with real ETH.
All transactions should use only testnet (valueless) ETH obtained
from faucets.

Transaction Types
-----------------
- Legacy (Type 0): Original Ethereum transaction format with gasPrice
- EIP-2930 (Type 1): Access list transactions
- EIP-1559 (Type 2): Modern transactions with maxFeePerGas and
  maxPriorityFeePerGas (base fee + tip model)
"""

import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

from .utils import (
    ether_to_wei,
    wei_to_ether,
    wei_to_gwei,
    gwei_to_wei,
    is_valid_address,
    to_checksum_address,
    bytes_to_hex,
    SEPOLIA_CHAIN_ID,
    print_security_warning,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default Sepolia RPC (override via INFURA_PROJECT_ID env var)
DEFAULT_SEPOLIA_RPC = "https://rpc.sepolia.org"

# Gas limit for a simple ETH transfer
DEFAULT_GAS_LIMIT = 21000

# Default max priority fee (tip) in gwei
DEFAULT_MAX_PRIORITY_FEE_GWEI = 2.0

# Default max fee per gas in gwei
DEFAULT_MAX_FEE_PER_GAS_GWEI = 50.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TransactionRequest:
    """
    Represents an unsigned transaction request.

    Attributes
    ----------
    to : str
        Recipient address (EIP-55 checksum format).
    value_ether : float
        Amount to send in ether.
    gas_limit : int
        Maximum gas units for the transaction.
    max_fee_per_gas_gwei : float
        Maximum total fee per gas unit in gwei (EIP-1559).
    max_priority_fee_gwei : float
        Maximum priority fee (tip) per gas unit in gwei (EIP-1559).
    data : str
        Optional calldata (hex string) for contract interactions.
    nonce : int or None
        Transaction nonce. If None, fetched from the network.
    chain_id : int
        Chain ID (default: Sepolia = 11155111).
    """
    to: str
    value_ether: float = 0.0
    gas_limit: int = DEFAULT_GAS_LIMIT
    max_fee_per_gas_gwei: float = DEFAULT_MAX_FEE_PER_GAS_GWEI
    max_priority_fee_gwei: float = DEFAULT_MAX_PRIORITY_FEE_GWEI
    data: str = "0x"
    nonce: Optional[int] = None
    chain_id: int = SEPOLIA_CHAIN_ID


@dataclass
class SignedTransactionResult:
    """
    Result of signing a transaction.

    Attributes
    ----------
    raw_transaction : str
        The RLP-encoded signed transaction (hex).
    transaction_hash : str
        The transaction hash.
    sender : str
        The sender's address.
    to : str
        The recipient's address.
    value_wei : int
        The value in wei.
    gas_limit : int
        The gas limit.
    max_fee_per_gas_wei : int
        Maximum fee per gas in wei.
    max_priority_fee_wei : int
        Maximum priority fee in wei.
    nonce : int
        The transaction nonce.
    chain_id : int
        The chain ID.
    v : int
        ECDSA recovery parameter.
    r : str
        ECDSA signature r component.
    s : str
        ECDSA signature s component.
    """
    raw_transaction: str
    transaction_hash: str
    sender: str
    to: str
    value_wei: int
    gas_limit: int
    max_fee_per_gas_wei: int
    max_priority_fee_wei: int
    nonce: int
    chain_id: int
    v: int
    r: str
    s: str


# ---------------------------------------------------------------------------
# Web3 Provider
# ---------------------------------------------------------------------------

def get_web3_provider() -> Web3:
    """
    Create a Web3 provider instance connected to Sepolia testnet.

    Uses the INFURA_PROJECT_ID environment variable if available,
    otherwise falls back to the public Sepolia RPC endpoint.

    Returns
    -------
    Web3
        Connected Web3 instance.
    """
    infura_id = os.environ.get("INFURA_PROJECT_ID", "")
    if infura_id:
        rpc_url = f"https://sepolia.infura.io/v3/{infura_id}"
    else:
        rpc_url = DEFAULT_SEPOLIA_RPC

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    return w3


def get_nonce(address: str) -> int:
    """
    Fetch the current transaction nonce for an address from the network.

    Parameters
    ----------
    address : str
        The Ethereum address.

    Returns
    -------
    int
        The current nonce (number of transactions sent from this address).
    """
    w3 = get_web3_provider()
    return w3.eth.get_transaction_count(to_checksum_address(address))


def get_gas_price_estimate() -> Dict[str, int]:
    """
    Fetch current gas price estimates from the network.

    Returns
    -------
    dict
        Dictionary with 'base_fee_wei', 'max_priority_fee_wei', and
        'suggested_max_fee_wei'.
    """
    w3 = get_web3_provider()

    try:
        latest_block = w3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas", gwei_to_wei(20))
    except Exception:
        base_fee = gwei_to_wei(20)

    try:
        max_priority_fee = w3.eth.max_priority_fee
    except Exception:
        max_priority_fee = gwei_to_wei(2)

    # Suggested max fee = 2 * base_fee + max_priority_fee
    suggested_max_fee = 2 * base_fee + max_priority_fee

    return {
        "base_fee_wei": base_fee,
        "max_priority_fee_wei": max_priority_fee,
        "suggested_max_fee_wei": suggested_max_fee,
    }


# ---------------------------------------------------------------------------
# Transaction Construction
# ---------------------------------------------------------------------------

def build_transaction(
    request: TransactionRequest,
    from_address: str,
) -> Dict[str, Any]:
    """
    Build an unsigned EIP-1559 transaction dictionary.

    This constructs the transaction parameters that will be signed by
    the sender's private key. It does NOT sign or broadcast the transaction.

    Parameters
    ----------
    request : TransactionRequest
        The transaction parameters.
    from_address : str
        The sender's address.

    Returns
    -------
    dict
        The unsigned transaction dictionary ready for signing.

    Raises
    ------
    ValueError
        If addresses are invalid or parameters are out of range.
    """
    # Validate addresses
    if not is_valid_address(from_address):
        raise ValueError(f"Invalid sender address: {from_address}")
    if not is_valid_address(request.to):
        raise ValueError(f"Invalid recipient address: {request.to}")

    # Validate chain ID (must be Sepolia for safety)
    if request.chain_id != SEPOLIA_CHAIN_ID:
        raise ValueError(
            f"This tool only supports Sepolia testnet (chain ID {SEPOLIA_CHAIN_ID}). "
            f"Got chain ID {request.chain_id}. NEVER use this tool on mainnet."
        )

    # Convert values
    value_wei = ether_to_wei(request.value_ether)
    max_fee_per_gas_wei = gwei_to_wei(request.max_fee_per_gas_gwei)
    max_priority_fee_wei = gwei_to_wei(request.max_priority_fee_gwei)

    # Get nonce if not specified
    nonce = request.nonce
    if nonce is None:
        try:
            nonce = get_nonce(from_address)
        except Exception:
            nonce = 0  # Fallback for offline mode

    # Build EIP-1559 (Type 2) transaction
    tx = {
        "type": 2,  # EIP-1559
        "chainId": request.chain_id,
        "nonce": nonce,
        "to": to_checksum_address(request.to),
        "value": value_wei,
        "gas": request.gas_limit,
        "maxFeePerGas": max_fee_per_gas_wei,
        "maxPriorityFeePerGas": max_priority_fee_wei,
    }

    # Add calldata if present
    if request.data and request.data != "0x":
        tx["data"] = request.data

    return tx


def build_legacy_transaction(
    request: TransactionRequest,
    from_address: str,
    gas_price_gwei: float = 20.0,
) -> Dict[str, Any]:
    """
    Build an unsigned legacy (Type 0) transaction dictionary.

    Legacy transactions use a single gasPrice field instead of the
    EIP-1559 base fee + tip model.

    Parameters
    ----------
    request : TransactionRequest
        The transaction parameters.
    from_address : str
        The sender's address.
    gas_price_gwei : float
        Gas price in gwei.

    Returns
    -------
    dict
        The unsigned legacy transaction dictionary.
    """
    if not is_valid_address(from_address):
        raise ValueError(f"Invalid sender address: {from_address}")
    if not is_valid_address(request.to):
        raise ValueError(f"Invalid recipient address: {request.to}")
    if request.chain_id != SEPOLIA_CHAIN_ID:
        raise ValueError(
            f"This tool only supports Sepolia testnet. Got chain ID {request.chain_id}."
        )

    value_wei = ether_to_wei(request.value_ether)
    gas_price_wei = gwei_to_wei(gas_price_gwei)

    nonce = request.nonce
    if nonce is None:
        try:
            nonce = get_nonce(from_address)
        except Exception:
            nonce = 0

    tx = {
        "nonce": nonce,
        "to": to_checksum_address(request.to),
        "value": value_wei,
        "gas": request.gas_limit,
        "gasPrice": gas_price_wei,
        "chainId": request.chain_id,
    }

    if request.data and request.data != "0x":
        tx["data"] = request.data

    return tx


# ---------------------------------------------------------------------------
# Transaction Signing
# ---------------------------------------------------------------------------

def sign_transaction(
    tx_dict: Dict[str, Any],
    private_key: str,
) -> SignedTransactionResult:
    """
    Sign a transaction with a private key.

    Uses the eth-account library to ECDSA-sign the transaction. The
    resulting signed transaction can be broadcast to the network.

    Parameters
    ----------
    tx_dict : dict
        The unsigned transaction dictionary (from build_transaction).
    private_key : str
        The sender's private key (hex string, with or without 0x prefix).

    Returns
    -------
    SignedTransactionResult
        The signed transaction with all components.

    .. warning::
        TESTNET ONLY. Never sign transactions for mainnet with this tool.
    """
    print_security_warning()

    # Verify this is a testnet transaction
    chain_id = tx_dict.get("chainId", 0)
    if chain_id == 1:
        raise ValueError(
            "SAFETY CHECK FAILED: Refusing to sign a mainnet (chain ID 1) "
            "transaction. This tool is for TESTNET USE ONLY."
        )

    # Sign the transaction
    signed = Account.sign_transaction(tx_dict, private_key)

    # Extract signature components
    raw_tx_hex = signed.raw_transaction.hex()
    if not raw_tx_hex.startswith("0x"):
        raw_tx_hex = "0x" + raw_tx_hex

    tx_hash = signed.hash.hex()
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash

    return SignedTransactionResult(
        raw_transaction=raw_tx_hex,
        transaction_hash=tx_hash,
        sender=Account.from_key(private_key).address,
        to=tx_dict["to"],
        value_wei=tx_dict["value"],
        gas_limit=tx_dict["gas"],
        max_fee_per_gas_wei=tx_dict.get("maxFeePerGas", tx_dict.get("gasPrice", 0)),
        max_priority_fee_wei=tx_dict.get("maxPriorityFeePerGas", 0),
        nonce=tx_dict["nonce"],
        chain_id=tx_dict.get("chainId", SEPOLIA_CHAIN_ID),
        v=signed.v,
        r=hex(signed.r),
        s=hex(signed.s),
    )


# ---------------------------------------------------------------------------
# Transaction Broadcasting
# ---------------------------------------------------------------------------

def broadcast_transaction(raw_transaction: str) -> str:
    """
    Broadcast a signed transaction to the Sepolia testnet.

    Parameters
    ----------
    raw_transaction : str
        The RLP-encoded signed transaction (hex string).

    Returns
    -------
    str
        The transaction hash.

    Raises
    ------
    ConnectionError
        If the RPC provider is unreachable.
    ValueError
        If the transaction is rejected by the network.

    .. warning::
        TESTNET ONLY. This broadcasts to Sepolia.
    """
    w3 = get_web3_provider()

    if isinstance(raw_transaction, str):
        if raw_transaction.startswith("0x"):
            raw_bytes = bytes.fromhex(raw_transaction[2:])
        else:
            raw_bytes = bytes.fromhex(raw_transaction)
    else:
        raw_bytes = raw_transaction

    tx_hash = w3.eth.send_raw_transaction(raw_bytes)
    return tx_hash.hex()


# ---------------------------------------------------------------------------
# Transaction Analysis
# ---------------------------------------------------------------------------

def analyze_transaction(tx_dict: Dict[str, Any]) -> Dict[str, str]:
    """
    Analyze a transaction dictionary and return a human-readable breakdown.

    Parameters
    ----------
    tx_dict : dict
        The transaction dictionary (signed or unsigned).

    Returns
    -------
    dict
        Human-readable analysis of each transaction field.
    """
    analysis = {}

    # Type
    tx_type = tx_dict.get("type", 0)
    type_names = {0: "Legacy", 1: "EIP-2930 (Access List)", 2: "EIP-1559"}
    analysis["Transaction Type"] = type_names.get(tx_type, f"Unknown ({tx_type})")

    # Chain
    chain_id = tx_dict.get("chainId", "unknown")
    chain_names = {1: "Mainnet", 11155111: "Sepolia", 5: "Goerli (deprecated)"}
    chain_name = chain_names.get(chain_id, f"Chain {chain_id}")
    analysis["Network"] = f"{chain_name} (ID: {chain_id})"

    # Addresses
    analysis["Recipient"] = tx_dict.get("to", "Contract Creation")

    # Value
    value_wei = tx_dict.get("value", 0)
    analysis["Value"] = f"{wei_to_ether(value_wei)} ETH ({value_wei} wei)"

    # Gas
    gas_limit = tx_dict.get("gas", 0)
    analysis["Gas Limit"] = f"{gas_limit} units"

    # Fee structure
    if "maxFeePerGas" in tx_dict:
        max_fee = tx_dict["maxFeePerGas"]
        max_priority = tx_dict.get("maxPriorityFeePerGas", 0)
        analysis["Max Fee Per Gas"] = f"{wei_to_gwei(max_fee)} gwei"
        analysis["Max Priority Fee"] = f"{wei_to_gwei(max_priority)} gwei"
        max_cost = gas_limit * max_fee
        analysis["Max Transaction Cost"] = f"{wei_to_ether(max_cost)} ETH"
    elif "gasPrice" in tx_dict:
        gas_price = tx_dict["gasPrice"]
        analysis["Gas Price"] = f"{wei_to_gwei(gas_price)} gwei"
        max_cost = gas_limit * gas_price
        analysis["Max Transaction Cost"] = f"{wei_to_ether(max_cost)} ETH"

    # Nonce
    analysis["Nonce"] = str(tx_dict.get("nonce", 0))

    # Data
    data = tx_dict.get("data", "0x")
    if data and data != "0x":
        analysis["Data"] = f"{len(data) // 2 - 1} bytes (contract interaction)"
        if len(data) >= 10:
            analysis["Function Selector"] = data[:10]
    else:
        analysis["Data"] = "Empty (simple ETH transfer)"

    return analysis


def estimate_transaction_cost(
    gas_limit: int = DEFAULT_GAS_LIMIT,
    max_fee_per_gas_gwei: float = DEFAULT_MAX_FEE_PER_GAS_GWEI,
) -> Dict[str, str]:
    """
    Estimate the maximum cost of a transaction.

    Parameters
    ----------
    gas_limit : int
        The gas limit.
    max_fee_per_gas_gwei : float
        The maximum fee per gas in gwei.

    Returns
    -------
    dict
        Cost breakdown with maximum possible cost.
    """
    max_fee_wei = gwei_to_wei(max_fee_per_gas_gwei)
    max_cost_wei = gas_limit * max_fee_wei

    return {
        "gas_limit": str(gas_limit),
        "max_fee_per_gas": f"{max_fee_per_gas_gwei} gwei",
        "max_transaction_cost_wei": str(max_cost_wei),
        "max_transaction_cost_ether": str(wei_to_ether(max_cost_wei)),
        "note": "Actual cost may be lower. You only pay base_fee + priority_fee.",
    }
