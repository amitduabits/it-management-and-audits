"""
Block Explorer Module
=====================

Fetches block-level data from the Ethereum blockchain via the Etherscan API.
Provides tools to inspect individual blocks, list transactions within blocks,
and track the latest blocks on the Sepolia testnet.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
==============================================
This module queries the Sepolia testnet. It is designed for learning about
blockchain data structures and should not be used for production purposes
or mainnet interaction.

Block Structure
---------------
An Ethereum block contains:
- Block header (parent hash, state root, timestamp, gas limit, etc.)
- List of transactions
- Uncle/ommer block headers (PoW era; no longer relevant post-Merge)
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
    SEPOLIA_CHAIN_ID,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ETHERSCAN_API_URLS = {
    1: "https://api.etherscan.io/api",
    11155111: "https://api-sepolia.etherscan.io/api",
}

API_RATE_LIMIT_SECONDS = 0.25
_last_api_call = 0.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BlockInfo:
    """
    Information about a single Ethereum block.

    Attributes
    ----------
    number : int
        The block number (height).
    hash : str
        The block hash.
    parent_hash : str
        The hash of the parent block.
    timestamp : int
        Unix timestamp when the block was produced.
    miner : str
        The address of the block proposer / miner.
    gas_used : int
        Total gas consumed by all transactions in the block.
    gas_limit : int
        Maximum gas allowed in the block.
    base_fee_per_gas : int
        The EIP-1559 base fee per gas for this block (in wei).
    transaction_count : int
        Number of transactions in the block.
    size : int
        Block size in bytes.
    extra_data : str
        Arbitrary data included by the block producer.
    transactions : list
        List of transaction hashes or full transaction objects.
    """
    number: int
    hash: str
    parent_hash: str
    timestamp: int
    miner: str
    gas_used: int
    gas_limit: int
    base_fee_per_gas: int
    transaction_count: int
    size: int
    extra_data: str
    transactions: List[str] = field(default_factory=list)

    @property
    def timestamp_readable(self) -> str:
        """Human-readable timestamp."""
        return datetime.utcfromtimestamp(self.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    @property
    def gas_utilization(self) -> float:
        """Gas utilization as a percentage."""
        if self.gas_limit == 0:
            return 0.0
        return (self.gas_used / self.gas_limit) * 100

    @property
    def base_fee_gwei(self) -> str:
        """Base fee per gas in gwei."""
        return str(wei_to_gwei(self.base_fee_per_gas))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a display-friendly dictionary."""
        return {
            "Block Number": f"{self.number:,}",
            "Block Hash": self.hash,
            "Parent Hash": self.parent_hash,
            "Timestamp": self.timestamp_readable,
            "Block Producer": self.miner,
            "Transactions": f"{self.transaction_count:,}",
            "Gas Used": f"{self.gas_used:,}",
            "Gas Limit": f"{self.gas_limit:,}",
            "Gas Utilization": f"{self.gas_utilization:.1f}%",
            "Base Fee": f"{self.base_fee_gwei} Gwei",
            "Size": f"{self.size:,} bytes",
            "Extra Data": self.extra_data,
        }


@dataclass
class BlockTransaction:
    """A transaction as it appears within a block."""
    hash: str
    from_address: str
    to_address: str
    value_wei: int
    gas: int
    gas_price_wei: int
    nonce: int
    transaction_index: int
    input_data: str

    @property
    def value_ether(self) -> str:
        return str(wei_to_ether(self.value_wei))

    @property
    def is_contract_interaction(self) -> bool:
        return self.input_data is not None and self.input_data != "0x"


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Get the Etherscan API key from environment."""
    key = os.environ.get("ETHERSCAN_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "ETHERSCAN_API_KEY environment variable is not set. "
            "Get a free API key at https://etherscan.io/apis"
        )
    return key


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
        Query parameters.
    chain_id : int
        The chain ID.

    Returns
    -------
    dict
        Parsed JSON response.
    """
    _rate_limit()
    api_key = _get_api_key()
    api_url = ETHERSCAN_API_URLS.get(chain_id)
    if not api_url:
        raise ValueError(f"Unsupported chain ID: {chain_id}")

    params["apikey"] = api_key
    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Block Queries
# ---------------------------------------------------------------------------

def get_latest_block_number(chain_id: int = SEPOLIA_CHAIN_ID) -> int:
    """
    Fetch the latest block number from the network.

    Parameters
    ----------
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    int
        The latest block number.
    """
    data = _etherscan_request({
        "module": "proxy",
        "action": "eth_blockNumber",
    }, chain_id)

    return int(data.get("result", "0x0"), 16)


def get_block_by_number(
    block_number: int,
    include_transactions: bool = True,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> BlockInfo:
    """
    Fetch a block by its number.

    Parameters
    ----------
    block_number : int
        The block number to fetch.
    include_transactions : bool
        If True, include full transaction objects. If False, only hashes.
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    BlockInfo
        The block information.

    Raises
    ------
    ValueError
        If the block is not found.
    """
    block_hex = hex(block_number)

    data = _etherscan_request({
        "module": "proxy",
        "action": "eth_getBlockByNumber",
        "tag": block_hex,
        "boolean": "true" if include_transactions else "false",
    }, chain_id)

    block = data.get("result")
    if not block:
        raise ValueError(f"Block not found: {block_number}")

    transactions = block.get("transactions", [])
    if include_transactions and transactions and isinstance(transactions[0], dict):
        tx_hashes = [tx.get("hash", "") for tx in transactions]
    else:
        tx_hashes = transactions if isinstance(transactions, list) else []

    return BlockInfo(
        number=int(block.get("number", "0x0"), 16),
        hash=block.get("hash", ""),
        parent_hash=block.get("parentHash", ""),
        timestamp=int(block.get("timestamp", "0x0"), 16),
        miner=block.get("miner", ""),
        gas_used=int(block.get("gasUsed", "0x0"), 16),
        gas_limit=int(block.get("gasLimit", "0x0"), 16),
        base_fee_per_gas=int(block.get("baseFeePerGas", "0x0"), 16),
        transaction_count=len(transactions),
        size=int(block.get("size", "0x0"), 16),
        extra_data=block.get("extraData", ""),
        transactions=tx_hashes,
    )


def get_block_transactions(
    block_number: int,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> List[BlockTransaction]:
    """
    Fetch all transactions within a specific block.

    Parameters
    ----------
    block_number : int
        The block number.
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    list of BlockTransaction
        All transactions in the block.
    """
    block_hex = hex(block_number)

    data = _etherscan_request({
        "module": "proxy",
        "action": "eth_getBlockByNumber",
        "tag": block_hex,
        "boolean": "true",
    }, chain_id)

    block = data.get("result")
    if not block:
        raise ValueError(f"Block not found: {block_number}")

    transactions = []
    for tx in block.get("transactions", []):
        if isinstance(tx, dict):
            transactions.append(
                BlockTransaction(
                    hash=tx.get("hash", ""),
                    from_address=tx.get("from", ""),
                    to_address=tx.get("to", "") or "Contract Creation",
                    value_wei=int(tx.get("value", "0x0"), 16),
                    gas=int(tx.get("gas", "0x0"), 16),
                    gas_price_wei=int(tx.get("gasPrice", "0x0"), 16),
                    nonce=int(tx.get("nonce", "0x0"), 16),
                    transaction_index=int(
                        tx.get("transactionIndex", "0x0"), 16
                    ),
                    input_data=tx.get("input", "0x"),
                )
            )

    return transactions


def get_latest_blocks(
    count: int = 5,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> List[BlockInfo]:
    """
    Fetch the most recent blocks.

    Parameters
    ----------
    count : int
        Number of recent blocks to fetch (max 20).
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    list of BlockInfo
        The most recent blocks, newest first.
    """
    count = min(count, 20)  # Safety limit
    latest = get_latest_block_number(chain_id)

    blocks = []
    for i in range(count):
        block_num = latest - i
        if block_num < 0:
            break
        try:
            block = get_block_by_number(
                block_num,
                include_transactions=False,
                chain_id=chain_id,
            )
            blocks.append(block)
        except Exception as e:
            # Log and continue on individual block failures
            print(f"  Warning: Could not fetch block {block_num}: {e}")
            continue

    return blocks


# ---------------------------------------------------------------------------
# Block Statistics
# ---------------------------------------------------------------------------

def get_block_statistics(block: BlockInfo) -> Dict[str, Any]:
    """
    Compute statistics for a block.

    Parameters
    ----------
    block : BlockInfo
        The block to analyze.

    Returns
    -------
    dict
        Statistical summary of the block.
    """
    return {
        "block_number": block.number,
        "transaction_count": block.transaction_count,
        "gas_utilization_percent": round(block.gas_utilization, 2),
        "base_fee_gwei": block.base_fee_gwei,
        "timestamp": block.timestamp_readable,
        "size_bytes": block.size,
        "is_empty": block.transaction_count == 0,
    }


def get_block_range_summary(
    start_block: int,
    end_block: int,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> Dict[str, Any]:
    """
    Compute a summary over a range of blocks.

    Parameters
    ----------
    start_block : int
        Starting block number (inclusive).
    end_block : int
        Ending block number (inclusive).
    chain_id : int
        The chain ID.

    Returns
    -------
    dict
        Summary statistics over the block range.
    """
    block_count = end_block - start_block + 1
    if block_count > 50:
        raise ValueError("Block range too large. Maximum 50 blocks.")

    total_txs = 0
    total_gas_used = 0
    total_gas_limit = 0
    base_fees = []
    block_times = []

    prev_timestamp = None

    for num in range(start_block, end_block + 1):
        try:
            block = get_block_by_number(num, include_transactions=False, chain_id=chain_id)
            total_txs += block.transaction_count
            total_gas_used += block.gas_used
            total_gas_limit += block.gas_limit
            base_fees.append(block.base_fee_per_gas)

            if prev_timestamp is not None:
                block_times.append(block.timestamp - prev_timestamp)
            prev_timestamp = block.timestamp

        except Exception:
            continue

    avg_gas_util = (total_gas_used / total_gas_limit * 100) if total_gas_limit > 0 else 0
    avg_base_fee = sum(base_fees) / len(base_fees) if base_fees else 0
    avg_block_time = sum(block_times) / len(block_times) if block_times else 0

    return {
        "block_range": f"{start_block} - {end_block}",
        "blocks_analyzed": block_count,
        "total_transactions": total_txs,
        "avg_transactions_per_block": round(total_txs / block_count, 1),
        "avg_gas_utilization_percent": round(avg_gas_util, 2),
        "avg_base_fee_gwei": str(wei_to_gwei(int(avg_base_fee))),
        "avg_block_time_seconds": round(avg_block_time, 2),
    }


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------

def format_block_for_display(block: BlockInfo) -> str:
    """
    Format a BlockInfo object as a readable string.

    Parameters
    ----------
    block : BlockInfo
        The block to format.

    Returns
    -------
    str
        Formatted block details.
    """
    details = block.to_dict()
    lines = []
    max_key_len = max(len(k) for k in details.keys())

    lines.append("=" * 72)
    lines.append(f"  Block #{block.number:,}")
    lines.append("=" * 72)

    for key, value in details.items():
        lines.append(f"  {key:<{max_key_len + 2}} {value}")

    if block.transactions:
        lines.append("")
        lines.append(f"  --- Transactions ({len(block.transactions)}) ---")
        for i, tx_hash in enumerate(block.transactions[:10]):
            lines.append(f"  [{i}] {tx_hash}")
        if len(block.transactions) > 10:
            lines.append(f"  ... and {len(block.transactions) - 10} more")

    lines.append("=" * 72)
    return "\n".join(lines)
