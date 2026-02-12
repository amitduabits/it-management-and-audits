"""
Key Derivation Visualizer
=========================

Provides rich terminal visualizations of the HD wallet key derivation process,
showing the complete path from mnemonic to Ethereum address with intermediate
steps displayed in an educational, easy-to-follow format.

Uses the ``rich`` library for formatted terminal output including tables,
trees, panels, and colored text.

WARNING: EDUCATIONAL USE ONLY -- TESTNET ONLY.
==============================================
NEVER use any wallet, mnemonic, or private key displayed by this module
to store real cryptocurrency. All displayed keys are INSECURE.
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.columns import Columns
from rich.layout import Layout
from rich.rule import Rule
from rich import box

from .wallet_generator import (
    WalletInfo,
    generate_wallet,
    private_key_to_public_key,
)
from .utils import bytes_to_hex, truncate_hash


# ---------------------------------------------------------------------------
# Console instance
# ---------------------------------------------------------------------------

console = Console()


# ---------------------------------------------------------------------------
# Security Banner
# ---------------------------------------------------------------------------

def display_security_banner():
    """Display a prominent security warning banner."""
    warning_text = Text()
    warning_text.append("SECURITY WARNING\n\n", style="bold red")
    warning_text.append(
        "All keys and addresses shown below are for EDUCATIONAL / TESTNET "
        "purposes ONLY.\n\n",
        style="red",
    )
    warning_text.append(
        "NEVER use these keys to store, send, or receive real cryptocurrency.\n",
        style="bold yellow",
    )
    warning_text.append(
        "NEVER enter a real mnemonic phrase into this tool.\n",
        style="bold yellow",
    )
    warning_text.append(
        "All generated material should be treated as PUBLICLY COMPROMISED.",
        style="red",
    )

    console.print(
        Panel(
            warning_text,
            title="[bold red]WARNING[/bold red]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Mnemonic Display
# ---------------------------------------------------------------------------

def display_mnemonic(wallet: WalletInfo):
    """
    Display the mnemonic phrase in a numbered grid layout.

    Parameters
    ----------
    wallet : WalletInfo
        The wallet containing the mnemonic to display.
    """
    words = wallet.mnemonic.split()

    table = Table(
        title="BIP-39 Mnemonic Phrase",
        box=box.ROUNDED,
        title_style="bold cyan",
        header_style="bold white",
        show_lines=True,
    )

    # Create columns (4 columns for 12 words, 6 for 24)
    cols_count = 4 if len(words) <= 16 else 6
    for i in range(cols_count):
        table.add_column(f"#{i+1}", justify="center", style="cyan")

    # Fill rows
    rows = []
    current_row = []
    for i, word in enumerate(words):
        current_row.append(f"[bold green]{i+1}.[/bold green] {word}")
        if len(current_row) == cols_count:
            rows.append(current_row)
            current_row = []
    if current_row:
        while len(current_row) < cols_count:
            current_row.append("")
        rows.append(current_row)

    for row in rows:
        table.add_row(*row)

    console.print(
        Panel(
            table,
            subtitle=f"[dim]{len(words)} words | {len(words) * 11 - len(words) // 3} bits of entropy[/dim]",
            border_style="cyan",
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Seed Display
# ---------------------------------------------------------------------------

def display_seed(wallet: WalletInfo):
    """
    Display the derived seed with explanation.

    Parameters
    ----------
    wallet : WalletInfo
        The wallet containing the seed to display.
    """
    seed_hex = wallet.seed_hex
    passphrase_display = (
        f'"{wallet.passphrase}"' if wallet.passphrase else "(none)"
    )

    info_text = Text()
    info_text.append("Derivation Method: ", style="bold")
    info_text.append("PBKDF2-HMAC-SHA512\n", style="green")
    info_text.append("Iterations: ", style="bold")
    info_text.append("2048\n", style="green")
    info_text.append("Salt: ", style="bold")
    info_text.append(f'"mnemonic" + passphrase\n', style="green")
    info_text.append("Passphrase: ", style="bold")
    info_text.append(f"{passphrase_display}\n", style="green")
    info_text.append("Output Length: ", style="bold")
    info_text.append("512 bits (64 bytes)\n\n", style="green")
    info_text.append("Seed (hex):\n", style="bold")
    # Display seed in 32-char lines for readability
    for i in range(0, len(seed_hex) - 2, 32):
        chunk = seed_hex[2:][i : i + 32]
        info_text.append(f"  {chunk}\n", style="yellow")

    console.print(
        Panel(
            info_text,
            title="[bold magenta]Binary Seed (BIP-39)[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED,
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Master Key Display
# ---------------------------------------------------------------------------

def display_master_key(wallet: WalletInfo):
    """
    Display the master private key and chain code.

    Parameters
    ----------
    wallet : WalletInfo
        The wallet containing the master key to display.
    """
    info_text = Text()
    info_text.append("Derivation: ", style="bold")
    info_text.append('HMAC-SHA512(key="Bitcoin seed", data=seed)\n\n', style="green")
    info_text.append("Master Private Key (first 256 bits):\n", style="bold")
    info_text.append(f"  {wallet.master_private_key_hex}\n\n", style="yellow")
    info_text.append("Master Chain Code (last 256 bits):\n", style="bold")
    info_text.append(
        f"  {bytes_to_hex(wallet.master_chain_code)}\n\n", style="yellow"
    )
    info_text.append("Path: ", style="bold")
    info_text.append("m (root)\n", style="cyan")
    info_text.append("Depth: ", style="bold")
    info_text.append("0", style="cyan")

    console.print(
        Panel(
            info_text,
            title="[bold blue]Master Key (BIP-32)[/bold blue]",
            border_style="blue",
            box=box.ROUNDED,
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Derivation Path Tree
# ---------------------------------------------------------------------------

def display_derivation_tree(wallet: WalletInfo):
    """
    Display the full derivation path as a rich tree structure.

    Shows each level of the BIP-44 path with the derived key and chain code
    at that level.

    Parameters
    ----------
    wallet : WalletInfo
        The wallet with derived keys to display.
    """
    tree = Tree(
        "[bold white]m[/bold white] [dim](master)[/dim]",
        guide_style="blue",
    )

    # Path meaning lookup
    path_meanings = {
        "m/44'": "purpose = BIP-44 (multi-account HD wallets)",
        "m/44'/60'": "coin_type = 60 (Ethereum)",
        "m/44'/60'/0'": "account = 0 (first account)",
        "m/44'/60'/0'/0": "change = 0 (external / receiving chain)",
        "m/44'/60'/0'/0/0": "address_index = 0 (first address)",
    }

    current_branch = tree
    for dk in wallet.derived_keys:
        hardened_marker = " [red](hardened)[/red]" if dk.is_hardened else ""
        meaning = path_meanings.get(dk.path, "")
        meaning_str = f" [dim]-- {meaning}[/dim]" if meaning else ""

        key_preview = truncate_hash(dk.private_key_hex, 8, 8)

        label = (
            f"[bold cyan]{dk.path}[/bold cyan]{hardened_marker}{meaning_str}\n"
            f"  [dim]Key:[/dim] [yellow]{key_preview}[/yellow]  "
            f"[dim]Depth:[/dim] {dk.depth}  "
            f"[dim]Index:[/dim] {dk.index}"
        )
        current_branch = current_branch.add(label)

    console.print(
        Panel(
            tree,
            title="[bold green]Derivation Path Tree (BIP-44)[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Ethereum Address Display
# ---------------------------------------------------------------------------

def display_ethereum_address(wallet: WalletInfo):
    """
    Display the final Ethereum address with derivation details.

    Parameters
    ----------
    wallet : WalletInfo
        The wallet containing the final address.
    """
    public_key = private_key_to_public_key(wallet.final_private_key)

    info_text = Text()
    info_text.append("Final Private Key:\n", style="bold")
    info_text.append(f"  {wallet.final_private_key_hex}\n\n", style="yellow")
    info_text.append("Public Key (uncompressed, 64 bytes):\n", style="bold")
    pub_hex = bytes_to_hex(public_key)
    info_text.append(f"  {pub_hex[:34]}...\n", style="yellow")
    info_text.append(f"  ...{pub_hex[-34:]}\n\n", style="yellow")
    info_text.append("Address Derivation:\n", style="bold")
    info_text.append("  public_key -> Keccak-256 -> last 20 bytes -> EIP-55 checksum\n\n", style="dim")
    info_text.append("Ethereum Address:\n", style="bold")
    info_text.append(f"  {wallet.ethereum_address}\n\n", style="bold green")
    info_text.append("Derivation Path: ", style="bold")
    info_text.append(wallet.derivation_path, style="cyan")

    console.print(
        Panel(
            info_text,
            title="[bold green]Ethereum Address[/bold green]",
            border_style="green",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Flow Diagram
# ---------------------------------------------------------------------------

def display_flow_diagram():
    """
    Display an ASCII flow diagram showing the complete derivation process.
    """
    diagram = """
[bold cyan]Complete Key Derivation Flow[/bold cyan]

[bold white]  Entropy (128-256 bits of randomness)[/bold white]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]BIP-39 encoding[/dim]
[bold green]  Mnemonic Phrase (12-24 words)[/bold green]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]PBKDF2-HMAC-SHA512 (2048 rounds, salt="mnemonic"+passphrase)[/dim]
[bold yellow]  Binary Seed (512 bits)[/bold yellow]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]HMAC-SHA512 (key="Bitcoin seed")[/dim]
  [bold blue]+---------------------------+[/bold blue]
  [bold blue]| Master Private Key (256b) |[/bold blue]
  [bold blue]| Master Chain Code  (256b) |[/bold blue]
  [bold blue]+---------------------------+[/bold blue]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]BIP-32 child key derivation (hardened)[/dim]
  [bold magenta]m/44'[/bold magenta]   [dim]purpose = BIP-44[/dim]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]BIP-32 child key derivation (hardened)[/dim]
  [bold magenta]m/44'/60'[/bold magenta]   [dim]coin_type = Ethereum[/dim]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]BIP-32 child key derivation (hardened)[/dim]
  [bold magenta]m/44'/60'/0'[/bold magenta]   [dim]account = 0[/dim]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]BIP-32 child key derivation (normal)[/dim]
  [bold magenta]m/44'/60'/0'/0[/bold magenta]   [dim]external chain[/dim]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]BIP-32 child key derivation (normal)[/dim]
  [bold magenta]m/44'/60'/0'/0/0[/bold magenta]   [dim]address index 0[/dim]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]secp256k1 elliptic curve multiplication[/dim]
[bold yellow]  Public Key (512 bits / 64 bytes)[/bold yellow]
              [dim]|[/dim]
              [dim]v[/dim]  [dim]Keccak-256 hash, take last 20 bytes[/dim]
[bold green]  Ethereum Address (160 bits / 20 bytes / 0x...)[/bold green]
    """

    console.print(
        Panel(
            diagram,
            border_style="white",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Summary Table
# ---------------------------------------------------------------------------

def display_summary_table(wallet: WalletInfo):
    """
    Display a compact summary table of all derivation stages.

    Parameters
    ----------
    wallet : WalletInfo
        The wallet to summarize.
    """
    table = Table(
        title="Derivation Summary",
        box=box.ROUNDED,
        title_style="bold white",
        header_style="bold cyan",
        show_lines=True,
    )

    table.add_column("Stage", style="bold", min_width=20)
    table.add_column("Value", style="yellow", min_width=50)
    table.add_column("Size", justify="right", style="dim")

    words = wallet.mnemonic.split()
    mnemonic_preview = f"{words[0]} {words[1]} ... {words[-2]} {words[-1]}"

    table.add_row(
        "Mnemonic",
        mnemonic_preview,
        f"{len(words)} words",
    )
    table.add_row(
        "Seed",
        truncate_hash(wallet.seed_hex, 16, 16),
        "512 bits",
    )
    table.add_row(
        "Master Key",
        truncate_hash(wallet.master_private_key_hex, 16, 16),
        "256 bits",
    )
    table.add_row(
        "Chain Code",
        truncate_hash(bytes_to_hex(wallet.master_chain_code), 16, 16),
        "256 bits",
    )

    for dk in wallet.derived_keys:
        table.add_row(
            f"Key at {dk.path}",
            truncate_hash(dk.private_key_hex, 12, 12),
            "256 bits",
        )

    table.add_row(
        "[bold green]Ethereum Address[/bold green]",
        f"[bold green]{wallet.ethereum_address}[/bold green]",
        "160 bits",
    )

    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Full Visualization
# ---------------------------------------------------------------------------

def visualize_full_derivation(
    wallet: Optional[WalletInfo] = None,
    strength: int = 128,
    passphrase: str = "",
    show_flow: bool = True,
):
    """
    Run the complete derivation visualization.

    Generates a wallet (if not provided) and displays every stage of the
    key derivation process with rich formatting.

    Parameters
    ----------
    wallet : WalletInfo, optional
        Pre-generated wallet to visualize. If None, a new wallet is generated.
    strength : int
        Mnemonic strength if generating a new wallet.
    passphrase : str
        Passphrase if generating a new wallet.
    show_flow : bool
        If True, show the flow diagram before the detailed steps.
    """
    console.print(Rule("[bold white]Crypto Wallet Explorer -- Key Derivation Visualizer[/bold white]"))
    console.print()

    # Security warning
    display_security_banner()

    # Generate wallet if needed
    if wallet is None:
        console.print("[dim]Generating new wallet...[/dim]\n")
        wallet = generate_wallet(strength=strength, passphrase=passphrase)

    # Flow diagram
    if show_flow:
        display_flow_diagram()

    # Step-by-step display
    console.print(Rule("[bold]Step 1: Mnemonic Generation (BIP-39)[/bold]"))
    console.print()
    display_mnemonic(wallet)

    console.print(Rule("[bold]Step 2: Seed Derivation (BIP-39)[/bold]"))
    console.print()
    display_seed(wallet)

    console.print(Rule("[bold]Step 3: Master Key Derivation (BIP-32)[/bold]"))
    console.print()
    display_master_key(wallet)

    console.print(Rule("[bold]Step 4: Child Key Derivation (BIP-44)[/bold]"))
    console.print()
    display_derivation_tree(wallet)

    console.print(Rule("[bold]Step 5: Ethereum Address Computation[/bold]"))
    console.print()
    display_ethereum_address(wallet)

    # Summary
    console.print(Rule("[bold]Summary[/bold]"))
    console.print()
    display_summary_table(wallet)

    # Final warning
    console.print(
        Panel(
            "[bold red]REMINDER: These keys are for EDUCATIONAL / TESTNET use ONLY. "
            "NEVER use them for real cryptocurrency.[/bold red]",
            border_style="red",
            box=box.HEAVY,
        )
    )

    return wallet
