# ₿ Bitcoin Fee Simulator

Ever wondered how your transaction actually gets picked by a miner? This tool is a peek behind the curtain. It simulates the "Greedy Algorithm" miners use to fill 1MB blocks with the most profitable transactions.

## 🚀 Why this matters
To a miner, every byte in a block is prime real estate. They don't care about the *value* of your transaction; they only care about the **fee rate (sat/vB)**. This simulator helps you visualize:
- Why "low fee" transactions get stuck for days.
- How a sudden burst of high-fee activity pushes others out.
- The literal packing of a Bitcoin block.

## 🛠️ Setup
```bash
# Install the cool UI libraries (Rich & Click)
pip install -r requirements.txt
```

## 🕹️ How to Use
**Live Mode** (Needs internet):
Fetches the latest real transactions from `mempool.space`.
```bash
python fee_sim.py
```

**Offline Mode**:
Use the provided sample or your own snapshot.
```bash
python fee_sim.py mempool_sample.json
```

**Custom Block Size**:
Want to see what happens if blocks were 2MB?
```bash
python fee_sim.py --block-size 2000000
```

## 🧠 Developer Notes
- **Sorting**: We use Python's Timsort (very efficient) to mimic the miner's sorting priority.
- **Safety**: Includes a synthetic data generator so the tool works even when the API is down or you're on a plane ✈️.
- **Refactoring**: Coded with love for the Summer of Bitcoin (SoB).
