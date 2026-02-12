"""
Command-Line Interface
======================

Provides a Click-based CLI for all Crypto Wallet Explorer features.
All commands operate exclusively on the Sepolia testnet.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
==============================================
NEVER use generated wallets for real cryptocurrency.
NEVER enter real mnemonics or private keys into this tool.
All operations target the Sepolia testnet only.

Usage
-----
Run commands with:
    python -m src.cli <command> [options]

Available Commands:
    generate-wallet    Generate a new HD wallet (BIP-39/32/44)
    show-derivation    Visualize the key derivation process
    build-tx           Build and sign a testnet transaction
    explore-tx         Fetch and display transaction details
    explore-block      Fetch and display block information
    check-balance      Check ETH and token balances
"""

import os
import sys
import json
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Load environment variables from .env file
load_dotenv()

console = Console()


# ---------------------------------------------------------------------------
# Security Warning
# ---------------------------------------------------------------------------

SECURITY_BANNER = """
+----------------------------------------------------------------------+
|   CRYPTO WALLET EXPLORER -- EDUCATIONAL / TESTNET USE ONLY           |
|                                                                      |
|   - NEVER use generated wallets for real cryptocurrency              |
|   - NEVER enter real mnemonics or private keys                       |
|   - All operations target Sepolia testnet ONLY                       |
|   - Generated keys are INSECURE and should be treated as PUBLIC      |
|   - Use hardware wallets or audited software for real funds           |
+----------------------------------------------------------------------+
"""


def print_banner():
    """Print the security banner."""
    console.print(
        Panel(
            SECURITY_BANNER.strip(),
            title="[bold red]SECURITY WARNING[/bold red]",
            border_style="red",
            box=box.DOUBLE,
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="1.0.0", prog_name="Crypto Wallet Explorer")
def cli():
    """
    Crypto Wallet Explorer -- Educational blockchain toolkit.

    A professional blockchain education tool for understanding cryptocurrency
    wallets, key derivation, transaction construction, and blockchain
    exploration on the Sepolia testnet.

    WARNING: EDUCATIONAL / TESTNET USE ONLY. Never use generated wallets
    or keys for real cryptocurrency.
    """
    pass


# ---------------------------------------------------------------------------
# generate-wallet
# ---------------------------------------------------------------------------

@cli.command("generate-wallet")
@click.option(
    "--strength",
    type=click.Choice(["128", "160", "192", "224", "256"]),
    default="128",
    help="Entropy bits: 128=12 words, 160=15, 192=18, 224=21, 256=24 words.",
)
@click.option(
    "--passphrase",
    default="",
    help="Optional BIP-39 passphrase (the '25th word').",
)
@click.option(
    "--path",
    default="m/44'/60'/0'/0/0",
    help="BIP-44 derivation path.",
)
@click.option(
    "--count",
    default=1,
    type=int,
    help="Number of addresses to derive (1-20).",
)
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="Output wallet data as JSON.",
)
def generate_wallet_cmd(strength, passphrase, path, count, json_output):
    """
    Generate a new HD wallet with BIP-39 mnemonic.

    Creates a new wallet by generating a random mnemonic phrase, deriving
    the seed, master key, and child keys according to BIP-32/44, and
    computing one or more Ethereum addresses.

    WARNING: NEVER use the generated wallet for real cryptocurrency.
    These keys are for educational/testnet use ONLY.
    """
    from .wallet_generator import generate_wallet, derive_multiple_addresses

    print_banner()

    strength_int = int(strength)

    console.print("[bold cyan]Generating new wallet...[/bold cyan]\n")

    wallet = generate_wallet(
        strength=strength_int,
        passphrase=passphrase,
        derivation_path=path,
    )

    if json_output:
        output = {
            "warning": "EDUCATIONAL/TESTNET ONLY - Never use for real funds",
            "mnemonic": wallet.mnemonic,
            "passphrase": passphrase if passphrase else "(none)",
            "derivation_path": path,
            "ethereum_address": wallet.ethereum_address,
            "private_key": wallet.final_private_key_hex,
        }

        if count > 1:
            addresses = derive_multiple_addresses(
                wallet.mnemonic, passphrase, min(count, 20)
            )
            output["derived_addresses"] = [
                {"path": p, "address": a, "private_key": k}
                for p, a, k in addresses
            ]

        click.echo(json.dumps(output, indent=2))
        return

    # Rich display
    # Mnemonic
    words = wallet.mnemonic.split()
    mnemonic_table = Table(
        title="BIP-39 Mnemonic Phrase",
        box=box.ROUNDED,
        title_style="bold cyan",
        show_lines=True,
    )
    cols = 4
    for i in range(cols):
        mnemonic_table.add_column(f"Col {i+1}", justify="center")

    row = []
    for i, word in enumerate(words):
        row.append(f"[green]{i+1}.[/green] {word}")
        if len(row) == cols:
            mnemonic_table.add_row(*row)
            row = []
    if row:
        while len(row) < cols:
            row.append("")
        mnemonic_table.add_row(*row)

    console.print(mnemonic_table)
    console.print()

    # Wallet details
    detail_table = Table(box=box.ROUNDED, show_header=False, show_lines=True)
    detail_table.add_column("Field", style="bold")
    detail_table.add_column("Value", style="yellow")

    detail_table.add_row("Word Count", str(wallet.word_count))
    detail_table.add_row("Passphrase", passphrase if passphrase else "(none)")
    detail_table.add_row("Derivation Path", path)
    detail_table.add_row("Ethereum Address", f"[bold green]{wallet.ethereum_address}[/bold green]")
    detail_table.add_row("Private Key", wallet.final_private_key_hex)

    console.print(detail_table)
    console.print()

    # Multiple addresses
    if count > 1:
        addresses = derive_multiple_addresses(
            wallet.mnemonic, passphrase, min(count, 20)
        )
        addr_table = Table(
            title=f"Derived Addresses (first {len(addresses)})",
            box=box.ROUNDED,
            title_style="bold cyan",
        )
        addr_table.add_column("Path", style="cyan")
        addr_table.add_column("Address", style="green")

        for p, a, _ in addresses:
            addr_table.add_row(p, a)

        console.print(addr_table)
        console.print()

    # Final warning
    console.print(
        Panel(
            "[bold red]NEVER use this wallet for real cryptocurrency. "
            "TESTNET ONLY.[/bold red]",
            border_style="red",
        )
    )


# ---------------------------------------------------------------------------
# show-derivation
# ---------------------------------------------------------------------------

@cli.command("show-derivation")
@click.option(
    "--strength",
    type=click.Choice(["128", "256"]),
    default="128",
    help="Mnemonic strength: 128=12 words, 256=24 words.",
)
@click.option(
    "--passphrase",
    default="",
    help="Optional BIP-39 passphrase.",
)
@click.option(
    "--mnemonic",
    default=None,
    help="Use an existing mnemonic phrase (for exploration only).",
)
def show_derivation_cmd(strength, passphrase, mnemonic):
    """
    Visualize the complete key derivation process.

    Shows every step from mnemonic generation through seed derivation,
    master key creation, child key derivation, and Ethereum address
    computation with rich terminal formatting.

    WARNING: If providing a mnemonic, use ONLY test mnemonics.
    NEVER enter a real mnemonic phrase into this tool.
    """
    from .wallet_generator import generate_wallet, restore_wallet
    from .key_visualizer import visualize_full_derivation

    print_banner()

    if mnemonic:
        console.print(
            "[bold red]WARNING: Never enter a real mnemonic into this tool. "
            "Only use test mnemonics.[/bold red]\n"
        )
        wallet = restore_wallet(mnemonic, passphrase)
    else:
        wallet = generate_wallet(strength=int(strength), passphrase=passphrase)

    visualize_full_derivation(wallet=wallet)


# ---------------------------------------------------------------------------
# build-tx
# ---------------------------------------------------------------------------

@cli.command("build-tx")
@click.option("--to", "to_address", required=True, help="Recipient address.")
@click.option(
    "--value",
    type=float,
    default=0.001,
    help="Amount in ETH to send (default: 0.001).",
)
@click.option(
    "--private-key",
    default=None,
    help="Sender's private key (hex). If not given, a test wallet is generated.",
)
@click.option(
    "--gas-limit",
    type=int,
    default=21000,
    help="Gas limit (default: 21000 for simple transfer).",
)
@click.option(
    "--max-fee",
    type=float,
    default=50.0,
    help="Max fee per gas in gwei (default: 50).",
)
@click.option(
    "--priority-fee",
    type=float,
    default=2.0,
    help="Max priority fee in gwei (default: 2).",
)
@click.option(
    "--broadcast",
    is_flag=True,
    default=False,
    help="Actually broadcast the transaction to Sepolia.",
)
@click.option(
    "--data",
    default="0x",
    help="Transaction data (hex) for contract calls.",
)
def build_tx_cmd(to_address, value, private_key, gas_limit, max_fee,
                 priority_fee, broadcast, data):
    """
    Build and sign a testnet Ethereum transaction.

    Constructs an EIP-1559 transaction for the Sepolia testnet, signs it
    with the provided (or generated) private key, and optionally broadcasts
    it to the network.

    WARNING: SEPOLIA TESTNET ONLY. This tool refuses to sign mainnet
    transactions. Use only testnet ETH from faucets.
    """
    from .wallet_generator import generate_wallet
    from .transaction_builder import (
        TransactionRequest,
        build_transaction,
        sign_transaction,
        broadcast_transaction,
        analyze_transaction,
    )
    from .utils import is_valid_address

    print_banner()

    if not is_valid_address(to_address):
        console.print(f"[red]Error: Invalid recipient address: {to_address}[/red]")
        sys.exit(1)

    # Get or generate private key
    if private_key:
        from eth_account import Account
        account = Account.from_key(private_key)
        from_address = account.address
        console.print(f"[yellow]Using provided private key.[/yellow]")
        console.print(
            "[bold red]WARNING: Never use a real private key in this tool.[/bold red]\n"
        )
    else:
        console.print("[dim]No private key provided. Generating a test wallet...[/dim]\n")
        wallet = generate_wallet()
        private_key = wallet.final_private_key_hex
        from_address = wallet.ethereum_address
        console.print(f"Generated test address: [green]{from_address}[/green]")
        console.print(
            "[yellow]This address has no testnet ETH. "
            "Get some from a Sepolia faucet first.[/yellow]\n"
        )

    # Build transaction
    request = TransactionRequest(
        to=to_address,
        value_ether=value,
        gas_limit=gas_limit,
        max_fee_per_gas_gwei=max_fee,
        max_priority_fee_gwei=priority_fee,
        data=data,
    )

    console.print("[bold cyan]Building transaction...[/bold cyan]\n")

    tx_dict = build_transaction(request, from_address)

    # Analyze
    analysis = analyze_transaction(tx_dict)
    analysis_table = Table(
        title="Transaction Analysis",
        box=box.ROUNDED,
        show_lines=True,
    )
    analysis_table.add_column("Field", style="bold")
    analysis_table.add_column("Value", style="yellow")
    for key, val in analysis.items():
        analysis_table.add_row(key, str(val))
    console.print(analysis_table)
    console.print()

    # Sign
    console.print("[bold cyan]Signing transaction...[/bold cyan]\n")
    signed = sign_transaction(tx_dict, private_key)

    signed_table = Table(
        title="Signed Transaction",
        box=box.ROUNDED,
        show_lines=True,
    )
    signed_table.add_column("Field", style="bold")
    signed_table.add_column("Value", style="yellow")
    signed_table.add_row("Transaction Hash", signed.transaction_hash)
    signed_table.add_row("From", signed.sender)
    signed_table.add_row("To", signed.to)
    signed_table.add_row("Nonce", str(signed.nonce))
    signed_table.add_row("v", str(signed.v))
    signed_table.add_row("r", signed.r)
    signed_table.add_row("s", signed.s)
    console.print(signed_table)
    console.print()

    # Raw TX display
    console.print("[bold]Raw Signed Transaction (RLP-encoded):[/bold]")
    console.print(f"[dim]{signed.raw_transaction[:80]}...[/dim]\n")

    # Broadcast
    if broadcast:
        console.print("[bold cyan]Broadcasting to Sepolia testnet...[/bold cyan]\n")
        try:
            tx_hash = broadcast_transaction(signed.raw_transaction)
            console.print(f"[bold green]Transaction broadcast successfully![/bold green]")
            console.print(f"TX Hash: [green]{tx_hash}[/green]")
            console.print(
                f"View on Etherscan: https://sepolia.etherscan.io/tx/0x{tx_hash}\n"
            )
        except Exception as e:
            console.print(f"[red]Broadcast failed: {e}[/red]")
            console.print(
                "[yellow]Make sure your address has Sepolia testnet ETH.[/yellow]\n"
            )
    else:
        console.print(
            "[dim]Transaction was NOT broadcast. Use --broadcast to send it.[/dim]\n"
        )

    console.print(
        Panel(
            "[bold red]REMINDER: SEPOLIA TESTNET ONLY. "
            "Never use this for real transactions.[/bold red]",
            border_style="red",
        )
    )


# ---------------------------------------------------------------------------
# explore-tx
# ---------------------------------------------------------------------------

@cli.command("explore-tx")
@click.option(
    "--tx-hash",
    required=True,
    help="Transaction hash to explore (0x-prefixed).",
)
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="Output as JSON.",
)
def explore_tx_cmd(tx_hash, json_output):
    """
    Fetch and display details for a specific transaction.

    Queries the Sepolia Etherscan API for transaction data including
    status, gas usage, value, input data, and more.

    Requires ETHERSCAN_API_KEY environment variable.
    """
    from .transaction_explorer import (
        get_transaction_details,
        format_transaction_for_display,
        decode_input_data,
    )

    print_banner()

    console.print(f"[bold cyan]Fetching transaction: {tx_hash}[/bold cyan]\n")

    try:
        tx = get_transaction_details(tx_hash)

        if json_output:
            click.echo(json.dumps(tx.to_dict(), indent=2, default=str))
        else:
            # Rich display
            detail_table = Table(
                title="Transaction Details",
                box=box.ROUNDED,
                show_lines=True,
            )
            detail_table.add_column("Field", style="bold", min_width=20)
            detail_table.add_column("Value", style="yellow")

            for key, val in tx.to_dict().items():
                detail_table.add_row(key, str(val))

            console.print(detail_table)
            console.print()

            # Decode input data
            if tx.input_data and tx.input_data != "0x":
                decoded = decode_input_data(tx.input_data)
                decode_table = Table(
                    title="Input Data Decode",
                    box=box.ROUNDED,
                    show_lines=True,
                )
                decode_table.add_column("Field", style="bold")
                decode_table.add_column("Value", style="cyan")
                for k, v in decoded.items():
                    if k != "raw_data":
                        decode_table.add_row(k, str(v))
                console.print(decode_table)
                console.print()

            console.print(
                f"[dim]View on Etherscan: "
                f"https://sepolia.etherscan.io/tx/{tx_hash}[/dim]\n"
            )

    except EnvironmentError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# explore-block
# ---------------------------------------------------------------------------

@cli.command("explore-block")
@click.option(
    "--block-number",
    type=int,
    default=None,
    help="Block number to explore. Defaults to latest.",
)
@click.option(
    "--latest",
    type=int,
    default=None,
    help="Show N latest blocks (max 10).",
)
@click.option(
    "--show-txs",
    is_flag=True,
    default=False,
    help="Show transactions within the block.",
)
def explore_block_cmd(block_number, latest, show_txs):
    """
    Fetch and display block information from Sepolia testnet.

    Shows block metadata including gas usage, transaction count,
    base fee, and optionally lists all transactions.

    Requires ETHERSCAN_API_KEY environment variable.
    """
    from .block_explorer import (
        get_block_by_number,
        get_latest_block_number,
        get_latest_blocks,
        get_block_transactions,
    )

    print_banner()

    try:
        if latest:
            count = min(latest, 10)
            console.print(f"[bold cyan]Fetching latest {count} blocks...[/bold cyan]\n")
            blocks = get_latest_blocks(count)

            block_table = Table(
                title=f"Latest {count} Blocks (Sepolia)",
                box=box.ROUNDED,
                show_lines=True,
            )
            block_table.add_column("Block", style="cyan", justify="right")
            block_table.add_column("Time", style="dim")
            block_table.add_column("TXs", justify="right")
            block_table.add_column("Gas Used", justify="right")
            block_table.add_column("Gas %", justify="right")
            block_table.add_column("Base Fee", justify="right")

            for b in blocks:
                block_table.add_row(
                    f"{b.number:,}",
                    b.timestamp_readable,
                    str(b.transaction_count),
                    f"{b.gas_used:,}",
                    f"{b.gas_utilization:.1f}%",
                    f"{b.base_fee_gwei} Gwei",
                )

            console.print(block_table)
            console.print()
            return

        # Single block
        if block_number is None:
            block_number = get_latest_block_number()
            console.print(f"[dim]Using latest block: {block_number:,}[/dim]\n")

        console.print(f"[bold cyan]Fetching block #{block_number:,}...[/bold cyan]\n")
        block = get_block_by_number(block_number, include_transactions=show_txs)

        detail_table = Table(
            title=f"Block #{block.number:,}",
            box=box.ROUNDED,
            show_lines=True,
        )
        detail_table.add_column("Field", style="bold", min_width=20)
        detail_table.add_column("Value", style="yellow")

        for key, val in block.to_dict().items():
            detail_table.add_row(key, str(val))

        console.print(detail_table)
        console.print()

        # Show transactions
        if show_txs:
            console.print(f"[bold cyan]Transactions in block #{block_number:,}:[/bold cyan]\n")
            txs = get_block_transactions(block_number)

            if not txs:
                console.print("[dim]No transactions in this block.[/dim]\n")
            else:
                tx_table = Table(
                    title=f"Transactions ({len(txs)})",
                    box=box.ROUNDED,
                )
                tx_table.add_column("#", style="dim", justify="right")
                tx_table.add_column("Hash", style="cyan")
                tx_table.add_column("From", style="dim")
                tx_table.add_column("To", style="dim")
                tx_table.add_column("Value (ETH)", justify="right", style="green")
                tx_table.add_column("Type", style="yellow")

                from .utils import truncate_hash

                for tx in txs[:50]:  # Limit display
                    tx_type = "Contract" if tx.is_contract_interaction else "Transfer"
                    tx_table.add_row(
                        str(tx.transaction_index),
                        truncate_hash(tx.hash),
                        truncate_hash(tx.from_address),
                        truncate_hash(tx.to_address),
                        tx.value_ether,
                        tx_type,
                    )

                console.print(tx_table)
                if len(txs) > 50:
                    console.print(f"[dim]... and {len(txs) - 50} more transactions[/dim]")
                console.print()

    except EnvironmentError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# check-balance
# ---------------------------------------------------------------------------

@cli.command("check-balance")
@click.option(
    "--address",
    required=True,
    help="Ethereum address to check.",
)
@click.option(
    "--tokens",
    is_flag=True,
    default=False,
    help="Also check known ERC-20 token balances.",
)
@click.option(
    "--token-address",
    default=None,
    help="Check balance for a specific ERC-20 token contract.",
)
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="Output as JSON.",
)
def check_balance_cmd(address, tokens, token_address, json_output):
    """
    Check ETH and ERC-20 token balances for an address.

    Queries the Sepolia Etherscan API for the current balance of the
    specified address. Optionally checks known ERC-20 token balances.

    Requires ETHERSCAN_API_KEY environment variable.

    NOTE: Balances shown are TESTNET tokens with NO real value.
    """
    from .balance_checker import (
        get_eth_balance,
        get_token_balance,
        generate_balance_report,
        format_balance_report,
    )

    print_banner()

    if not is_valid_address_check(address):
        console.print(f"[red]Error: Invalid Ethereum address: {address}[/red]")
        sys.exit(1)

    try:
        if token_address:
            # Specific token balance
            console.print(
                f"[bold cyan]Checking token balance...[/bold cyan]\n"
            )
            balance = get_token_balance(address, token_address)

            if json_output:
                click.echo(json.dumps(balance.to_dict(), indent=2, default=str))
            else:
                token_table = Table(
                    title="Token Balance",
                    box=box.ROUNDED,
                    show_lines=True,
                )
                token_table.add_column("Field", style="bold")
                token_table.add_column("Value", style="yellow")
                for k, v in balance.to_dict().items():
                    token_table.add_row(k, str(v))
                console.print(token_table)
                console.print()

        else:
            # Full balance report
            console.print(
                f"[bold cyan]Checking balance for {address}...[/bold cyan]\n"
            )
            report = generate_balance_report(
                address,
                include_tokens=tokens,
            )

            if json_output:
                click.echo(json.dumps(report, indent=2, default=str))
            else:
                # ETH balance
                eth = report.get("eth_balance", {})
                if eth and "error" not in eth:
                    eth_table = Table(
                        title="ETH Balance (Sepolia Testnet)",
                        box=box.ROUNDED,
                        show_lines=True,
                    )
                    eth_table.add_column("Field", style="bold")
                    eth_table.add_column("Value", style="green")
                    for k, v in eth.items():
                        eth_table.add_row(k, str(v))
                    console.print(eth_table)
                    console.print()

                # Token balances
                token_bals = report.get("token_balances", [])
                if token_bals:
                    token_table = Table(
                        title="ERC-20 Token Balances (Sepolia)",
                        box=box.ROUNDED,
                        show_lines=True,
                    )
                    token_table.add_column("Token", style="cyan")
                    token_table.add_column("Balance", style="green")
                    token_table.add_column("Contract", style="dim")

                    for tb in token_bals:
                        if "error" not in tb:
                            token_table.add_row(
                                tb.get("Token", "Unknown"),
                                tb.get("Balance", "0"),
                                tb.get("Contract", ""),
                            )
                    console.print(token_table)
                    console.print()

                console.print(
                    f"[dim]{report.get('warning', '')}[/dim]\n"
                )

    except EnvironmentError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def is_valid_address_check(address: str) -> bool:
    """Quick address validation for CLI use."""
    from .utils import is_valid_address
    return is_valid_address(address)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
