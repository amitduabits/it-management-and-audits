"""
Entry point for running the scanner as a module.
Usage: python -m scanner scan --target http://127.0.0.1:5000
"""

from scanner.cli import cli

if __name__ == '__main__':
    cli()
