"""
Transaction Explorer Module
============================

Fetches transaction details from the Etherscan API, decodes transaction
data, and displays comprehensive transaction information. Supports both
individual transaction lookups and address transaction history.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
==============================================
This module queries the Sepolia testnet Etherscan API. Do not use it
to interact with mainnet or to manage real funds.

API Usage
---------
Requires an Etherscan API key (free tier: 5 calls/second).
Set the ETHERSCAN_API_KEY environment variable or pass it directly.
Get a free key at: https://etherscan.io/apis
"""

import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests

from .utils import (
    wei_to_ether,
    wei_to_gwei,
    truncate_hash,
    is_valid_address,
    SEPOLIA_CHAIN_ID,
    print_security_warning,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Etherscan API base URLs
ETHERSCAN_API_URLS = {
    1: "https://api.etherscan.io/api",
    11155111: "https://api-sepolia.etherscan.io/api",
}

# Rate limiting: minimum seconds between API calls
API_RATE_LIMIT_SECONDS = 0.25

# Module-level timestamp for rate limiting
_last_api_call = 0.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TransactionDetails:
    """
    Detailed information about a single Ethereum transaction.
    """
    hash: str
    block_number: int
    block_hash: str
    timestamp: int
    from_address: str
    to_address: str
    value_wei: int
    gas_limit: int
    gas_used: int
    gas_price_wei: int
    nonce: int
    input_data: str
    status: int  # 1 = success, 0 = failure
    transaction_index: int
    confirmations: int

    @property
    def value_ether(self) -> str:
        return str(wei_to_ether(self.value_wei))

    @property
    def gas_price_gwei(self) -> str:
        return str(wei_to_gwei(self.gas_price_wei))

    @property
    def transaction_fee_wei(self) -> int:
        return self.gas_used * self.gas_price_wei

    @property
    def transaction_fee_ether(self) -> str:
        return str(wei_to_ether(self.transaction_fee_wei))

    @property
    def timestamp_readable(self) -> str:
        return datetime.utcfromtimestamp(self.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    @property
    def status_text(self) -> str:
        return "Success" if self.status == 1 else "Failed"

    @property
    def is_contract_interaction(self) -> bool:
        return self.input_data is not None and self.input_data != "0x"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a display-friendly dictionary."""
        return {
            "Transaction Hash": self.hash,
            "Status": self.status_text,
            "Block": self.block_number,
            "Timestamp": self.timestamp_readable,
            "From": self.from_address,
            "To": self.to_address or "Contract Creation",
            "Value": f"{self.value_ether} ETH",
            "Gas Limit": f"{self.gas_limit:,}",
            "Gas Used": f"{self.gas_used:,} ({self.gas_used / self.gas_limit * 100:.1f}%)" if self.gas_limit > 0 else str(self.gas_used),
            "Gas Price": f"{self.gas_price_gwei} Gwei",
            "Transaction Fee": f"{self.transaction_fee_ether} ETH",
            "Nonce": self.nonce,
            "Confirmations": f"{self.confirmations:,}",
            "Input Data": (
                f"{self.input_data[:66]}..." if len(self.input_data) > 66
                else self.input_data
            ),
            "Contract Interaction": "Yes" if self.is_contract_interaction else "No",
        }


@dataclass
class AddressTransaction:
    """A simplified transaction record from address history."""
    hash: str
    block_number: int
    timestamp: int
    from_address: str
    to_address: str
    value_wei: int
    gas_used: int
    gas_price_wei: int
    is_error: bool
    method_id: str

    @property
    def value_ether(self) -> str:
        return str(wei_to_ether(self.value_wei))

    @property
    def timestamp_readable(self) -> str:
        return datetime.utcfromtimestamp(self.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Get the Etherscan API key from environment."""
    key = os.environ.get("ETHERSCAN_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "ETHERSCAN_API_KEY environment variable is not set. "
            "Get a free API key at https://etherscan.io/apis and set it:\n"
            "  export ETHERSCAN_API_KEY=your_key_here"
        )
    return key


def _get_api_url(chain_id: int = SEPOLIA_CHAIN_ID) -> str:
    """Get the Etherscan API URL for a given chain."""
    url = ETHERSCAN_API_URLS.get(chain_id)
    if not url:
        raise ValueError(
            f"Unsupported chain ID: {chain_id}. "
            f"Supported chains: {list(ETHERSCAN_API_URLS.keys())}"
        )
    return url


def _rate_limit():
    """Enforce rate limiting between API calls."""
    global _last_api_call
    now = time.time()
    elapsed = now - _last_api_call
    if elapsed < API_RATE_LIMIT_SECONDS:
        time.sleep(API_RATE_LIMIT_SECONDS - elapsed)
    _last_api_call = time.time()


def _etherscan_request(
    params: Dict[str, str],
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> Dict[str, Any]:
    """
    Make a rate-limited request to the Etherscan API.

    Parameters
    ----------
    params : dict
        Query parameters for the API request.
    chain_id : int
        The chain ID to query.

    Returns
    -------
    dict
        The parsed JSON response.

    Raises
    ------
    requests.HTTPError
        If the HTTP request fails.
    ValueError
        If the API returns an error.
    """
    _rate_limit()

    api_key = _get_api_key()
    api_url = _get_api_url(chain_id)

    params["apikey"] = api_key

    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if data.get("status") == "0" and data.get("message") != "No transactions found":
        error_msg = data.get("result", data.get("message", "Unknown error"))
        raise ValueError(f"Etherscan API error: {error_msg}")

    return data


# ---------------------------------------------------------------------------
# Transaction Lookup
# ---------------------------------------------------------------------------

def get_transaction_details(
    tx_hash: str,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> TransactionDetails:
    """
    Fetch detailed information about a specific transaction.

    Combines data from eth_getTransactionByHash and eth_getTransactionReceipt
    to provide a complete picture of the transaction.

    Parameters
    ----------
    tx_hash : str
        The transaction hash (0x-prefixed hex string).
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    TransactionDetails
        Complete transaction information.

    Raises
    ------
    ValueError
        If the transaction hash is invalid or not found.
    """
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        raise ValueError(
            f"Invalid transaction hash format: {tx_hash}. "
            "Must be a 0x-prefixed 32-byte hex string (66 characters)."
        )

    # Fetch transaction data
    tx_data = _etherscan_request({
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": tx_hash,
    }, chain_id)

    tx = tx_data.get("result")
    if not tx:
        raise ValueError(f"Transaction not found: {tx_hash}")

    # Fetch transaction receipt for status and gas used
    receipt_data = _etherscan_request({
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": tx_hash,
    }, chain_id)

    receipt = receipt_data.get("result", {})

    # Fetch block for timestamp
    block_number_hex = tx.get("blockNumber", "0x0")
    block_data = _etherscan_request({
        "module": "proxy",
        "action": "eth_getBlockByNumber",
        "tag": block_number_hex,
        "boolean": "false",
    }, chain_id)

    block = block_data.get("result", {})
    timestamp = int(block.get("timestamp", "0x0"), 16)

    # Get current block number for confirmations
    current_block_data = _etherscan_request({
        "module": "proxy",
        "action": "eth_blockNumber",
    }, chain_id)

    current_block = int(current_block_data.get("result", "0x0"), 16)
    block_number = int(block_number_hex, 16)
    confirmations = max(0, current_block - block_number)

    return TransactionDetails(
        hash=tx_hash,
        block_number=block_number,
        block_hash=tx.get("blockHash", ""),
        timestamp=timestamp,
        from_address=tx.get("from", ""),
        to_address=tx.get("to", ""),
        value_wei=int(tx.get("value", "0x0"), 16),
        gas_limit=int(tx.get("gas", "0x0"), 16),
        gas_used=int(receipt.get("gasUsed", "0x0"), 16),
        gas_price_wei=int(tx.get("gasPrice", "0x0"), 16),
        nonce=int(tx.get("nonce", "0x0"), 16),
        input_data=tx.get("input", "0x"),
        status=int(receipt.get("status", "0x1"), 16),
        transaction_index=int(tx.get("transactionIndex", "0x0"), 16),
        confirmations=confirmations,
    )


# ---------------------------------------------------------------------------
# Address Transaction History
# ---------------------------------------------------------------------------

def get_address_transactions(
    address: str,
    start_block: int = 0,
    end_block: int = 99999999,
    page: int = 1,
    offset: int = 20,
    sort: str = "desc",
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> List[AddressTransaction]:
    """
    Fetch transaction history for an Ethereum address.

    Parameters
    ----------
    address : str
        The Ethereum address to query.
    start_block : int
        Starting block number for the search range.
    end_block : int
        Ending block number for the search range.
    page : int
        Page number for pagination.
    offset : int
        Number of transactions per page (max 10000).
    sort : str
        Sort order: 'asc' (oldest first) or 'desc' (newest first).
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    list of AddressTransaction
        List of transactions involving the address.
    """
    if not is_valid_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")

    data = _etherscan_request({
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": str(start_block),
        "endblock": str(end_block),
        "page": str(page),
        "offset": str(offset),
        "sort": sort,
    }, chain_id)

    result = data.get("result", [])
    if isinstance(result, str):
        return []  # No transactions found

    transactions = []
    for tx in result:
        transactions.append(
            AddressTransaction(
                hash=tx.get("hash", ""),
                block_number=int(tx.get("blockNumber", "0")),
                timestamp=int(tx.get("timeStamp", "0")),
                from_address=tx.get("from", ""),
                to_address=tx.get("to", ""),
                value_wei=int(tx.get("value", "0")),
                gas_used=int(tx.get("gasUsed", "0")),
                gas_price_wei=int(tx.get("gasPrice", "0")),
                is_error=tx.get("isError", "0") == "1",
                method_id=tx.get("methodId", "0x"),
            )
        )

    return transactions


# ---------------------------------------------------------------------------
# Internal Transaction Lookup
# ---------------------------------------------------------------------------

def get_internal_transactions(
    tx_hash: str,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> List[Dict[str, Any]]:
    """
    Fetch internal transactions (message calls) for a transaction.

    Internal transactions occur when a smart contract calls another
    contract or sends ETH as part of its execution.

    Parameters
    ----------
    tx_hash : str
        The transaction hash.
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    list of dict
        List of internal transaction details.
    """
    data = _etherscan_request({
        "module": "account",
        "action": "txlistinternal",
        "txhash": tx_hash,
    }, chain_id)

    result = data.get("result", [])
    if isinstance(result, str):
        return []

    internal_txs = []
    for itx in result:
        internal_txs.append({
            "from": itx.get("from", ""),
            "to": itx.get("to", ""),
            "value_wei": int(itx.get("value", "0")),
            "value_ether": str(wei_to_ether(int(itx.get("value", "0")))),
            "gas_limit": int(itx.get("gas", "0")),
            "gas_used": int(itx.get("gasUsed", "0")),
            "type": itx.get("type", ""),
            "is_error": itx.get("isError", "0") == "1",
            "error_code": itx.get("errCode", ""),
        })

    return internal_txs


# ---------------------------------------------------------------------------
# Transaction Decoding Helpers
# ---------------------------------------------------------------------------

def decode_input_data(input_data: str) -> Dict[str, str]:
    """
    Decode transaction input data at a basic level.

    Extracts the function selector (first 4 bytes) and parameter data.
    Full ABI decoding requires the contract ABI.

    Parameters
    ----------
    input_data : str
        The transaction input data (hex string).

    Returns
    -------
    dict
        Decoded components of the input data.
    """
    if not input_data or input_data == "0x":
        return {
            "type": "Simple Transfer",
            "description": "No input data -- this is a plain ETH transfer.",
            "function_selector": "N/A",
            "parameters": "N/A",
        }

    result = {
        "type": "Contract Interaction",
        "raw_data": input_data,
        "data_length": f"{(len(input_data) - 2) // 2} bytes",
    }

    if len(input_data) >= 10:
        selector = input_data[:10]
        result["function_selector"] = selector

        # Common function selectors
        known_selectors = {
            "0xa9059cbb": "transfer(address,uint256) -- ERC-20 token transfer",
            "0x23b872dd": "transferFrom(address,address,uint256) -- ERC-20 delegated transfer",
            "0x095ea7b3": "approve(address,uint256) -- ERC-20 approval",
            "0x70a08231": "balanceOf(address) -- ERC-20 balance query",
            "0x18160ddd": "totalSupply() -- ERC-20 total supply query",
            "0x313ce567": "decimals() -- ERC-20 decimals query",
            "0x06fdde03": "name() -- ERC-20 name query",
            "0x95d89b41": "symbol() -- ERC-20 symbol query",
            "0x3593564c": "execute(bytes,bytes[],uint256) -- Uniswap Universal Router",
            "0x7ff36ab5": "swapExactETHForTokens -- Uniswap V2 Router",
            "0x38ed1739": "swapExactTokensForTokens -- Uniswap V2 Router",
        }

        if selector in known_selectors:
            result["function_name"] = known_selectors[selector]
        else:
            result["function_name"] = "Unknown (ABI required for full decode)"

        # Extract parameter data
        param_data = input_data[10:]
        if param_data:
            # Parameters are 32-byte (64 hex char) words
            params = []
            for i in range(0, len(param_data), 64):
                word = param_data[i : i + 64]
                if len(word) == 64:
                    params.append(f"  [{i // 64}] 0x{word}")
            result["parameters"] = "\n".join(params) if params else "None"
            result["parameter_count"] = len(params)

    return result


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------

def format_transaction_for_display(tx: TransactionDetails) -> str:
    """
    Format a TransactionDetails object as a readable string.

    Parameters
    ----------
    tx : TransactionDetails
        The transaction to format.

    Returns
    -------
    str
        Formatted transaction details.
    """
    details = tx.to_dict()
    lines = []
    max_key_len = max(len(k) for k in details.keys())

    lines.append("=" * 72)
    lines.append(f"  Transaction: {tx.hash}")
    lines.append("=" * 72)

    for key, value in details.items():
        lines.append(f"  {key:<{max_key_len + 2}} {value}")

    # Decode input data
    if tx.input_data and tx.input_data != "0x":
        decoded = decode_input_data(tx.input_data)
        lines.append("")
        lines.append("  --- Input Data Decode ---")
        for k, v in decoded.items():
            if k != "raw_data":  # Skip raw data for readability
                lines.append(f"  {k:<{max_key_len + 2}} {v}")

    lines.append("=" * 72)
    return "\n".join(lines)
