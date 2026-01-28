# ₿ Bitcoin Fee Simulator

Ever sent a Bitcoin transaction and wondered why it's taking forever? Or why you had to pay $20 in fees during peak times? This tool shows you exactly what's happening behind the scenes.

Miners are basically playing Tetris with transactions, trying to fit the most profitable ones into each 1MB block. This simulator lets you see that process in action.

## Why I built this

I got tired of my transactions getting stuck in the mempool. After digging into how Bitcoin actually works, I realized miners don't care about your transaction amount - they only care about **fee rate** (satoshis per byte). 

Pay 1 sat/vB? You're waiting hours.  
Pay 50 sat/vB? Next block, baby.

So I built this to visualize the whole thing. Now I can see exactly where my transaction stands in the queue.

## Setup

```bash
pip install -r requirements.txt
```

That's it. Just installs Rich (for the pretty terminal UI) and Click (for CLI stuff).

## How to use it

**Live mode** - pulls real data from mempool.space:
```bash
python fee_sim.py
```

**Offline mode** - use the sample JSON I included:
```bash
python fee_sim.py mempool_sample.json
```

**Custom block size** - wanna see what 2MB blocks would look like?
```bash
python fee_sim.py --block-size 2000000
```

## How it works

The algorithm is dead simple (that's why it's so effective):

1. Grab all pending transactions
2. Sort them by fee rate (highest first)
3. Pack them into a 1MB block until it's full
4. Everything else waits

This is literally what miners do. It's called a "greedy algorithm" - always pick the most profitable option available.

## Tech stuff

- Python 3 (because it's easy and fast for this kind of thing)
- Uses Timsort for O(n log n) sorting
- Fetches live data from mempool.space API
- Has a fallback that generates fake data if the API is down
- Rich library makes the terminal output look nice

---

Built this to learn more about Bitcoin's fee market. Feel free to use it however you want.
