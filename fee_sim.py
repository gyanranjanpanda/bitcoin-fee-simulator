#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bitcoin Fee Simulator
Author: Gyan Ranjan Panda
Created: Jan 2026

This thing basically shows how miners pick transactions. They're greedy bastards
(in a good way lol) - they just want the highest fee per byte. That's it.

I built this to understand why my own BTC transactions were getting stuck sometimes.
Turns out if you're cheap with fees, you wait. Simple as that.
"""

import json
import random
import requests
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

# Block size is 1MB in vbytes (technically 4M weight units but whatever)
MAX_BLOCK_VSIZE = 1000000
MEMPOOL_API = "https://mempool.space/api/mempool/recent"

console = Console()

class MempoolSimulator:
    """Does the heavy lifting - simulates what miners actually do"""
    
    def __init__(self, block_limit=MAX_BLOCK_VSIZE):
        self.block_limit = block_limit
        self.mempool = []  # all pending txs
        self.packed_block = []  # winners
        self.left_behind = []  # losers (sad)

    def fetch_live_mempool(self):
        """Hit the mempool.space API and grab real tx data"""
        console.print("[bold blue]🔗 Connecting to the Bitcoin network (via mempool.space)...[/bold blue]")
        try:
            r = requests.get(MEMPOOL_API, timeout=10)  # 10s should be enough
            r.raise_for_status()
            raw_txs = r.json()
            
            # Convert API format to what we need
            # They give us: txid, fee (sats), vsize (bytes), value
            # We calculate: rate = fee/vsize (this is what miners care about)
            self.mempool = []
            for tx in raw_txs:
                self.mempool.append({
                    "txid": tx["txid"],
                    "fee": tx["fee"],
                    "vsize": tx["vsize"],
                    "rate": tx["fee"] / tx["vsize"]  # the magic number
                })
            
            console.print(f"[green]✅ Found {len(self.mempool)} real transactions in the wild.[/green]")
        
        except Exception as e:
            # API down? No internet? Whatever, we'll fake it
            console.print(f"[red]❌ API Fetch failed: {e}[/red]")
            console.print("[yellow]⚠️  Falling back to fake data so you can still play around[/yellow]")
            self._generate_synthetic_data()

    def load_local_json(self, path):
        """Load mempool from a JSON file (useful for testing)"""
        console.print(f"[blue]📂 Reading local mempool snapshot: {path}[/blue]")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Make sure the JSON has the fields we need
            valid_txs = []
            for tx in data:
                if "txid" in tx and "fee" in tx and "vsize" in tx:
                    tx["rate"] = tx["fee"] / tx["vsize"]
                    valid_txs.append(tx)
            
            self.mempool = valid_txs
            console.print(f"[green]✅ Loaded {len(self.mempool)} transactions from disk.[/green]")
        except Exception as e:
            console.print(f"[red]💥 Error reading file: {e}[/red]")

    def _generate_synthetic_data(self):
        """Make up some fake transactions when API is down"""
        # Generate ~250 random txs that look kinda real
        for i in range(250):
            vsize = random.randint(140, 800)  # most txs are between 140-800 bytes
            fee_rate = random.uniform(1.0, 150.0)  # sat/vB can vary wildly
            
            self.mempool.append({
                "txid": f"fake_{random.getrandbits(64):x}",
                "fee": int(vsize * fee_rate),
                "vsize": vsize,
                "rate": fee_rate
            })

    def run_simulation(self):
        """
        Here's where the magic happens - the greedy algorithm
        
        Miners do this:
        1. Sort all txs by fee rate (highest first)
        2. Shove them in the block until it's full
        3. Profit
        """
        # Sort by rate - highest payers go first (duh)
        sorted_mempool = sorted(self.mempool, key=lambda x: x["rate"], reverse=True)
        
        current_weight = 0
        total_fees = 0

        # Pack the block greedily
        for tx in sorted_mempool:
            if current_weight + tx["vsize"] <= self.block_limit:
                # It fits! Add it
                self.packed_block.append(tx)
                current_weight += tx["vsize"]
                total_fees += tx["fee"]
            else:
                # Sorry, no room for you
                self.left_behind.append(tx)

        return {
            "fees": total_fees,
            "vsize": current_weight,
            "avg_rate": total_fees / current_weight if current_weight > 0 else 0
        }

def get_conf_label(index, total_packed):
    """Rough estimate of when a tx will confirm"""
    if index < total_packed:
        return "[bold green]Next Block (High)[/bold green]"
    elif index < total_packed * 3:
        return "[bold yellow]~30-60 min (Medium)[/bold yellow]"  # maybe 2-3 blocks
    else:
        return "[bold red]Hours/Days (Low)[/bold red]"  # good luck lol

@click.command()
@click.argument('mempool_file', required=False, type=click.Path(exists=True))
@click.option('--block-size', default=MAX_BLOCK_VSIZE, help='Max block size in vBytes')
def cli(mempool_file, block_size):
    """
    Bitcoin Fee Simulator
    
    Shows you how miners pack blocks. Spoiler: they're greedy (in a good way).
    """
    console.print(Panel.fit("₿ BITCOIN FEE SIMULATOR", style="bold white on blue", padding=(1, 5)))
    
    sim = MempoolSimulator(block_limit=block_size)
    
    # Load data from wherever
    if mempool_file:
        sim.load_local_json(mempool_file)
    else:
        sim.fetch_live_mempool()

    if not sim.mempool:
        console.print("[red]No data to simulate. Try connecting to the internet or provide a JSON file.[/red]")
        return

    # Run the simulation with a fancy progress bar (because why not)
    with Progress() as progress:
        progress.add_task("[cyan]🔨 Mining block...", total=None)
        stats = sim.run_simulation()

    # --- Show the results ---
    results_table = Table(title="\n💎 Top Candidates for Next Block", header_style="bold magenta")
    results_table.add_column("Rank", justify="right")
    results_table.add_column("TXID (truncated)", style="dim")
    results_table.add_column("Rate (sat/vB)", style="bold cyan")
    results_table.add_column("VSize", justify="right")
    results_table.add_column("Priority", justify="center")

    # Show top 12 (nobody wants to see all 1000 lol)
    for i, tx in enumerate(sim.packed_block[:12]):
        results_table.add_row(
            str(i+1),
            f"{tx['txid'][:16]}...",
            f"{tx['rate']:.1f}",
            f"{tx['vsize']} vB",
            get_conf_label(i, len(sim.packed_block))
        )
    
    console.print(results_table)

    # Summary stats
    summary_text = (
        f"💰 [bold]Total Fees:[/bold] {stats['fees']:,} sats\n"
        f"📊 [bold]Average Rate:[/bold] {stats['avg_rate']:.2f} sat/vB\n"
        f"📦 [bold]Block Fill:[/bold] {stats['vsize']:,} / {block_size:,} vB "
        f"({(stats['vsize']/block_size)*100:.2f}%)\n"
        f"📈 [bold]TXs Included:[/bold] {len(sim.packed_block)}\n"
        f"⏳ [bold]TXs Queued (Mempool):[/bold] {len(sim.left_behind)}"
    )
    console.print(Panel(summary_text, title="Simulation Stats", border_style="green", expand=False))

    # Little easter egg - show the first rejected tx
    if sim.left_behind:
        cheapest = sim.left_behind[0]
        console.print(f"\n[italic gray]Note: First TX rejected had a rate of {cheapest['rate']:.1f} sat/vB.[/italic gray]")

if __name__ == "__main__":
    cli()
