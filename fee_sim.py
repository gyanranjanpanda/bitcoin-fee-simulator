"""
Bitcoin Fee Simulator - A tool to visualize how miners prioritize transactions.
Built for the SoB (Summer of Bitcoin) application.

How it works:
Miners are profit-seekers. They want the most 'satoshis per virtual byte' (sat/vB).
This script mimics that 'greedy strategy' to predict which TXs make the cut.
"""

import json
import random
import requests
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

# --- Constants & Config ---
# Standard Block Weight Limit is 4,000,000 weight units (~1,000,000 vbytes)
MAX_BLOCK_VSIZE = 1000000 
DEFAULT_API_URL = "https://mempool.space/api/mempool/recent"

console = Console()

class MempoolSimulator:
    def __init__(self, block_limit=MAX_BLOCK_VSIZE):
        self.block_limit = block_limit
        self.mempool = []
        self.packed_block = []
        self.left_behind = []

    def fetch_live_mempool(self):
        """
        Grabs real-time data from mempool.space. 
        Note: The 'recent' endpoint only gives us a glimpse, but it's great for simulation.
        """
        console.print("[bold blue]🔗 Connecting to the Bitcoin network (via mempool.space)...[/bold blue]")
        try:
            # We use a timeout because nobody likes a hanging CLI
            r = requests.get(DEFAULT_API_URL, timeout=10)
            r.raise_for_status()
            raw_txs = r.json()
            
            # Map the API fields to our internal logic
            # API gives: txid, fee, vsize, value
            self.mempool = [
                {
                    "txid": tx["txid"],
                    "fee": tx["fee"],
                    "vsize": tx["vsize"],
                    "rate": tx["fee"] / tx["vsize"]
                }
                for tx in raw_txs
            ]
            console.print(f"[green]✅ Found {len(self.mempool)} real transactions in the wild.[/green]")
        
        except Exception as e:
            console.print(f"[red]❌ API Fetch failed: {e}[/red]")
            console.print("[yellow]⚠️  Falling back to generated 'shadow' mempool for demo purposes.[/yellow]")
            self._generate_synthetic_data()

    def load_local_json(self, path):
        """Loads a snapshot of the mempool from a local file."""
        console.print(f"[blue]📂 Reading local mempool snapshot: {path}[/blue]")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Basic validation: ensure we have what we need to calculate rates
            valid_txs = []
            for tx in data:
                if all(k in tx for k in ("txid", "fee", "vsize")):
                    tx["rate"] = tx["fee"] / tx["vsize"]
                    valid_txs.append(tx)
            
            self.mempool = valid_txs
            console.print(f"[green]✅ Loaded {len(self.mempool)} transactions from disk.[/green]")
        except Exception as e:
            console.print(f"[red]💥 Error reading file: {e}[/red]")

    def _generate_synthetic_data(self):
        """Creates fake transactions that look somewhat realistic."""
        for i in range(250):
            vs = random.randint(140, 800) # Typical tx size
            fr = random.uniform(1.0, 150.0) # Fee rate variation
            self.mempool.append({
                "txid": f"mock_{random.getrandbits(64):x}",
                "fee": int(vs * fr),
                "vsize": vs,
                "rate": fr
            })

    def run_simulation(self):
        """
        The 'Greedy' approach: 
        1. Sort EVERYTHING by fee rate (desc).
        2. Pick until we hit the 1MB (vsize) limit.
        """
        # Step 1: Sorting - This is what miners do to maximize profit
        sorted_mempool = sorted(self.mempool, key=lambda x: x["rate"], reverse=True)
        
        current_weight = 0
        total_fees = 0

        # Step 2: Packing
        for tx in sorted_mempool:
            if current_weight + tx["vsize"] <= self.block_limit:
                self.packed_block.append(tx)
                current_weight += tx["vsize"]
                total_fees += tx["fee"]
            else:
                self.left_behind.append(tx)

        return {
            "fees": total_fees,
            "vsize": current_weight,
            "avg_rate": total_fees / current_weight if current_weight > 0 else 0
        }

def get_conf_label(index, total_packed):
    """Gives a human-readable estimate of confirmation time."""
    if index < total_packed:
        return "[bold green]Next Block (High)[/bold green]"
    elif index < total_packed * 3:
        return "[bold yellow]~30-60 min (Medium)[/bold yellow]"
    else:
        return "[bold red]Hours/Days (Low)[/bold red]"

@click.command()
@click.argument('mempool_file', required=False, type=click.Path(exists=True))
@click.option('--block-size', default=MAX_BLOCK_VSIZE, help='Max block size in vBytes')
def cli(mempool_file, block_size):
    """
    🔬 Bitcoin Fee Simulator
    
    A mini-engine that simulates how miners pack blocks to maximize profit.
    """
    console.print(Panel.fit("₿ BITCOIN FEE SIMULATOR", style="bold white on blue", padding=(1, 5)))
    
    sim = MempoolSimulator(block_limit=block_size)
    
    if mempool_file:
        sim.load_local_json(mempool_file)
    else:
        sim.fetch_live_mempool()

    if not sim.mempool:
        console.print("[red]No data to simulate. Try connecting to the internet or provide a JSON file.[/red]")
        return

    with Progress() as progress:
        progress.add_task("[cyan]🔨 Mining block...", total=None)
        stats = sim.run_simulation()

    # --- Results UI ---
    results_table = Table(title="\n💎 Top Candidates for Next Block", header_style="bold magenta")
    results_table.add_column("Rank", justify="right")
    results_table.add_column("TXID (truncated)", style="dim")
    results_table.add_column("Rate (sat/vB)", style="bold cyan")
    results_table.add_column("VSize", justify="right")
    results_table.add_column("Priority", justify="center")

    # Show top 12 transactions
    for i, tx in enumerate(sim.packed_block[:12]):
        results_table.add_row(
            str(i+1),
            f"{tx['txid'][:16]}...",
            f"{tx['rate']:.1f}",
            f"{tx['vsize']} vB",
            get_conf_label(i, len(sim.packed_block))
        )
    
    console.print(results_table)

    # Summary Panel
    summary_text = (
        f"💰 [bold]Total Fees:[/bold] {stats['fees']:,} sats\n"
        f"📊 [bold]Average Rate:[/bold] {stats['avg_rate']:.2f} sat/vB\n"
        f"📦 [bold]Block Fill:[/bold] {stats['vsize']:,} / {block_size:,} vB "
        f"({(stats['vsize']/block_size)*100:.2f}%)\n"
        f"📈 [bold]TXs Included:[/bold] {len(sim.packed_block)}\n"
        f"⏳ [bold]TXs Queued (Mempool):[/bold] {len(sim.left_behind)}"
    )
    console.print(Panel(summary_text, title="Simulation Stats", border_style="green", expand=False))

    if sim.left_behind:
        cheapest = sim.left_behind[0]
        console.print(f"\n[italic gray]Note: First TX rejected had a rate of {cheapest['rate']:.1f} sat/vB.[/italic gray]")

if __name__ == "__main__":
    cli()
