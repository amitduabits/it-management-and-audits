"""
Balance Checker Module
======================

Checks ETH and ERC-20 token balances for Ethereum addresses on the Sepolia
testnet. Provides both single-address and batch balance checking, as well
as ERC-20 token balance queries.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
==============================================
This module queries the Sepolia testnet. Balances shown are for testnet
tokens with NO real value. Never use this tool to check or manage
real cryptocurrency balances.

ERC-20 Token Standard
---------------------
ERC-20 is the most common Ethereum token standard. Key functions:
- balanceOf(address) -> uint256: Returns token balance
- transfer(address, uint256): Transfers tokens
- approve(address, uint256): Approves spending allowance
- decimals() -> uint8: Returns token decimal precision
- symbol() -> string: Returns token ticker symbol
- name() -> string: Returns token full name
"""

import os
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any, List, Optional

import requests

from .utils import (
    wei_to_ether,
    is_valid_address,
    to_checksum_address,
    truncate_hash,
    SEPOLIA_CHAIN_ID,
    ERC20_BALANCE_ABI,
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

# Well-known Sepolia testnet tokens (address -> symbol)
KNOWN_SEPOLIA_TOKENS = {
    "0x779877A7B0D9E8603169DdbD7836e478b4624789": {
        "symbol": "LINK",
        "name": "Chainlink Token",
        "decimals": 18,
    },
    "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238": {
        "symbol": "USDC",
        "name": "USD Coin",
        "decimals": 6,
    },
    "0x7169D38820dfd117C3FA1f22a697dBA58d90BA06": {
        "symbol": "DAI",
        "name": "Dai Stablecoin",
        "decimals": 18,
    },
    "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14": {
        "symbol": "WETH",
        "name": "Wrapped Ether",
        "decimals": 18,
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ETHBalance:
    """
    ETH balance information for an address.

    Attributes
    ----------
    address : str
        The Ethereum address.
    balance_wei : int
        Balance in wei.
    """
    address: str
    balance_wei: int

    @property
    def balance_ether(self) -> Decimal:
        """Balance in ether."""
        return wei_to_ether(self.balance_wei)

    @property
    def balance_formatted(self) -> str:
        """Human-readable balance string."""
        ether = self.balance_ether
        return f"{ether:.6f} ETH"

    def to_dict(self) -> Dict[str, str]:
        """Convert to display-friendly dictionary."""
        return {
            "Address": self.address,
            "Balance (ETH)": f"{self.balance_ether:.6f}",
            "Balance (Wei)": f"{self.balance_wei:,}",
        }


@dataclass
class TokenBalance:
    """
    ERC-20 token balance information.

    Attributes
    ----------
    address : str
        The holder's Ethereum address.
    token_address : str
        The ERC-20 token contract address.
    token_symbol : str
        The token's ticker symbol.
    token_name : str
        The token's full name.
    decimals : int
        The token's decimal precision.
    raw_balance : int
        The raw balance (before decimal adjustment).
    """
    address: str
    token_address: str
    token_symbol: str
    token_name: str
    decimals: int
    raw_balance: int

    @property
    def formatted_balance(self) -> Decimal:
        """Balance adjusted for token decimals."""
        if self.decimals == 0:
            return Decimal(self.raw_balance)
        return Decimal(self.raw_balance) / Decimal(10**self.decimals)

    @property
    def balance_string(self) -> str:
        """Human-readable balance string."""
        return f"{self.formatted_balance:.{min(self.decimals, 8)}f} {self.token_symbol}"

    def to_dict(self) -> Dict[str, str]:
        """Convert to display-friendly dictionary."""
        return {
            "Token": f"{self.token_name} ({self.token_symbol})",
            "Contract": self.token_address,
            "Balance": self.balance_string,
            "Raw Balance": f"{self.raw_balance:,}",
            "Decimals": str(self.decimals),
        }


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
    """Make a rate-limited request to the Etherscan API."""
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
# ETH Balance
# ---------------------------------------------------------------------------

def get_eth_balance(
    address: str,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> ETHBalance:
    """
    Fetch the ETH balance for a single address.

    Parameters
    ----------
    address : str
        The Ethereum address to check.
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    ETHBalance
        The balance information.

    Raises
    ------
    ValueError
        If the address is invalid.
    """
    if not is_valid_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")

    data = _etherscan_request({
        "module": "account",
        "action": "balance",
        "address": address,
        "tag": "latest",
    }, chain_id)

    balance_wei = int(data.get("result", "0"))

    return ETHBalance(
        address=to_checksum_address(address),
        balance_wei=balance_wei,
    )


def get_multi_eth_balance(
    addresses: List[str],
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> List[ETHBalance]:
    """
    Fetch ETH balances for multiple addresses in a single API call.

    Parameters
    ----------
    addresses : list of str
        The Ethereum addresses to check (max 20).
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    list of ETHBalance
        Balance information for each address.

    Raises
    ------
    ValueError
        If any address is invalid or more than 20 addresses given.
    """
    if len(addresses) > 20:
        raise ValueError(
            "Etherscan multi-balance API supports at most 20 addresses per call."
        )

    for addr in addresses:
        if not is_valid_address(addr):
            raise ValueError(f"Invalid Ethereum address: {addr}")

    address_str = ",".join(addresses)

    data = _etherscan_request({
        "module": "account",
        "action": "balancemulti",
        "address": address_str,
        "tag": "latest",
    }, chain_id)

    results = data.get("result", [])
    balances = []

    for item in results:
        balances.append(
            ETHBalance(
                address=to_checksum_address(item.get("account", "")),
                balance_wei=int(item.get("balance", "0")),
            )
        )

    return balances


# ---------------------------------------------------------------------------
# ERC-20 Token Balance
# ---------------------------------------------------------------------------

def get_token_balance(
    address: str,
    token_address: str,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> TokenBalance:
    """
    Fetch the balance of a specific ERC-20 token for an address.

    Parameters
    ----------
    address : str
        The holder's Ethereum address.
    token_address : str
        The ERC-20 token contract address.
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    TokenBalance
        The token balance information.
    """
    if not is_valid_address(address):
        raise ValueError(f"Invalid holder address: {address}")
    if not is_valid_address(token_address):
        raise ValueError(f"Invalid token contract address: {token_address}")

    # Fetch raw token balance
    data = _etherscan_request({
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": token_address,
        "address": address,
        "tag": "latest",
    }, chain_id)

    raw_balance = int(data.get("result", "0"))

    # Try to get token info from known tokens
    token_info = KNOWN_SEPOLIA_TOKENS.get(
        to_checksum_address(token_address),
        None,
    )

    if token_info:
        symbol = token_info["symbol"]
        name = token_info["name"]
        decimals = token_info["decimals"]
    else:
        # Fallback: try to fetch from Etherscan
        symbol, name, decimals = _fetch_token_info(token_address, chain_id)

    return TokenBalance(
        address=to_checksum_address(address),
        token_address=to_checksum_address(token_address),
        token_symbol=symbol,
        token_name=name,
        decimals=decimals,
        raw_balance=raw_balance,
    )


def _fetch_token_info(
    token_address: str,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> tuple:
    """
    Attempt to fetch token metadata (symbol, name, decimals) from Etherscan.

    Parameters
    ----------
    token_address : str
        The token contract address.
    chain_id : int
        The chain ID.

    Returns
    -------
    tuple of (str, str, int)
        (symbol, name, decimals) with fallback defaults.
    """
    symbol = "UNKNOWN"
    name = "Unknown Token"
    decimals = 18  # Default assumption

    try:
        # Use the ABI-encoded function calls via Etherscan proxy
        # symbol() = 0x95d89b41
        data = _etherscan_request({
            "module": "proxy",
            "action": "eth_call",
            "to": token_address,
            "data": "0x95d89b41",
            "tag": "latest",
        }, chain_id)

        result = data.get("result", "0x")
        if result and result != "0x" and len(result) > 2:
            # Decode ABI-encoded string (simplified)
            try:
                hex_data = result[2:]
                if len(hex_data) >= 128:
                    # Skip offset (32 bytes) and length (32 bytes)
                    str_len = int(hex_data[64:128], 16)
                    str_hex = hex_data[128 : 128 + str_len * 2]
                    symbol = bytes.fromhex(str_hex).decode("utf-8").strip("\x00")
            except Exception:
                pass

        # name() = 0x06fdde03
        data = _etherscan_request({
            "module": "proxy",
            "action": "eth_call",
            "to": token_address,
            "data": "0x06fdde03",
            "tag": "latest",
        }, chain_id)

        result = data.get("result", "0x")
        if result and result != "0x" and len(result) > 2:
            try:
                hex_data = result[2:]
                if len(hex_data) >= 128:
                    str_len = int(hex_data[64:128], 16)
                    str_hex = hex_data[128 : 128 + str_len * 2]
                    name = bytes.fromhex(str_hex).decode("utf-8").strip("\x00")
            except Exception:
                pass

        # decimals() = 0x313ce567
        data = _etherscan_request({
            "module": "proxy",
            "action": "eth_call",
            "to": token_address,
            "data": "0x313ce567",
            "tag": "latest",
        }, chain_id)

        result = data.get("result", "0x")
        if result and result != "0x" and len(result) > 2:
            try:
                decimals = int(result, 16)
            except Exception:
                pass

    except Exception:
        pass  # Use defaults

    return symbol, name, decimals


def check_known_token_balances(
    address: str,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> List[TokenBalance]:
    """
    Check balances for all known Sepolia testnet tokens.

    Parameters
    ----------
    address : str
        The holder's Ethereum address.
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    list of TokenBalance
        Balances for all known tokens (including zero balances).
    """
    if not is_valid_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")

    balances = []
    for token_addr, info in KNOWN_SEPOLIA_TOKENS.items():
        try:
            balance = get_token_balance(address, token_addr, chain_id)
            balances.append(balance)
        except Exception as e:
            # Include zero balance on error
            balances.append(
                TokenBalance(
                    address=to_checksum_address(address),
                    token_address=token_addr,
                    token_symbol=info["symbol"],
                    token_name=info["name"],
                    decimals=info["decimals"],
                    raw_balance=0,
                )
            )

    return balances


# ---------------------------------------------------------------------------
# ERC-20 Token Transfer Events
# ---------------------------------------------------------------------------

def get_token_transfers(
    address: str,
    token_address: Optional[str] = None,
    start_block: int = 0,
    end_block: int = 99999999,
    page: int = 1,
    offset: int = 20,
    sort: str = "desc",
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> List[Dict[str, Any]]:
    """
    Fetch ERC-20 token transfer events for an address.

    Parameters
    ----------
    address : str
        The Ethereum address.
    token_address : str, optional
        Filter to a specific token contract address.
    start_block : int
        Starting block number.
    end_block : int
        Ending block number.
    page : int
        Page number.
    offset : int
        Results per page.
    sort : str
        Sort order: 'asc' or 'desc'.
    chain_id : int
        The chain ID.

    Returns
    -------
    list of dict
        Token transfer events.
    """
    if not is_valid_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")

    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": str(start_block),
        "endblock": str(end_block),
        "page": str(page),
        "offset": str(offset),
        "sort": sort,
    }

    if token_address:
        if not is_valid_address(token_address):
            raise ValueError(f"Invalid token address: {token_address}")
        params["contractaddress"] = token_address

    data = _etherscan_request(params, chain_id)
    result = data.get("result", [])

    if isinstance(result, str):
        return []

    transfers = []
    for tx in result:
        decimals = int(tx.get("tokenDecimal", "18"))
        raw_value = int(tx.get("value", "0"))

        transfers.append({
            "hash": tx.get("hash", ""),
            "block_number": int(tx.get("blockNumber", "0")),
            "timestamp": int(tx.get("timeStamp", "0")),
            "from": tx.get("from", ""),
            "to": tx.get("to", ""),
            "token_symbol": tx.get("tokenSymbol", "UNKNOWN"),
            "token_name": tx.get("tokenName", "Unknown"),
            "token_address": tx.get("contractAddress", ""),
            "raw_value": raw_value,
            "formatted_value": str(
                Decimal(raw_value) / Decimal(10**decimals) if decimals > 0
                else Decimal(raw_value)
            ),
            "decimals": decimals,
            "gas_used": int(tx.get("gasUsed", "0")),
        })

    return transfers


# ---------------------------------------------------------------------------
# Complete Balance Report
# ---------------------------------------------------------------------------

def generate_balance_report(
    address: str,
    include_tokens: bool = True,
    chain_id: int = SEPOLIA_CHAIN_ID,
) -> Dict[str, Any]:
    """
    Generate a comprehensive balance report for an address.

    Includes ETH balance and optionally all known ERC-20 token balances.

    Parameters
    ----------
    address : str
        The Ethereum address.
    include_tokens : bool
        If True, also check known ERC-20 token balances.
    chain_id : int
        The chain ID (default: Sepolia).

    Returns
    -------
    dict
        Complete balance report.
    """
    if not is_valid_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")

    report = {
        "address": to_checksum_address(address),
        "network": "Sepolia Testnet" if chain_id == SEPOLIA_CHAIN_ID else f"Chain {chain_id}",
        "eth_balance": None,
        "token_balances": [],
        "warning": (
            "TESTNET ONLY: These balances represent testnet tokens with NO "
            "real monetary value. This report is for educational purposes only."
        ),
    }

    # ETH balance
    try:
        eth_bal = get_eth_balance(address, chain_id)
        report["eth_balance"] = eth_bal.to_dict()
    except Exception as e:
        report["eth_balance"] = {"error": str(e)}

    # Token balances
    if include_tokens:
        try:
            token_bals = check_known_token_balances(address, chain_id)
            report["token_balances"] = [
                tb.to_dict() for tb in token_bals
            ]
        except Exception as e:
            report["token_balances"] = [{"error": str(e)}]

    return report


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------

def format_balance_report(report: Dict[str, Any]) -> str:
    """
    Format a balance report as a readable string.

    Parameters
    ----------
    report : dict
        The balance report from generate_balance_report.

    Returns
    -------
    str
        Formatted report string.
    """
    lines = []
    lines.append("=" * 72)
    lines.append(f"  Balance Report: {report['address']}")
    lines.append(f"  Network: {report['network']}")
    lines.append("=" * 72)
    lines.append("")

    # Warning
    lines.append(f"  [!] {report['warning']}")
    lines.append("")

    # ETH balance
    eth = report.get("eth_balance")
    if eth and "error" not in eth:
        lines.append("  --- ETH Balance ---")
        for key, value in eth.items():
            lines.append(f"    {key}: {value}")
        lines.append("")

    # Token balances
    tokens = report.get("token_balances", [])
    if tokens:
        lines.append("  --- ERC-20 Token Balances ---")
        for token in tokens:
            if "error" in token:
                lines.append(f"    Error: {token['error']}")
            else:
                lines.append(f"    {token.get('Token', 'Unknown')}: {token.get('Balance', '0')}")
        lines.append("")

    lines.append("=" * 72)
    return "\n".join(lines)
