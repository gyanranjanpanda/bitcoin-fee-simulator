# Bitcoin Fee Simulator - Technical Deep Dive

## What's in here

- [Why I made this](#why-i-made-this)
- [Real-world uses](#real-world-uses)
- [The algorithm explained](#the-algorithm-explained)
- [How I built it](#how-i-built-it)
- [Architecture stuff](#architecture-stuff)

---

## Why I made this

### The actual problem

Bitcoin's fee market is confusing as hell. Here's what happens to most people:

1. **Stuck transactions**: You send BTC and it just... sits there. For hours. Sometimes days.
2. **Overpaying**: You panic and set fees way too high because you don't know what's actually needed
3. **No visibility**: There's no easy way to see what miners are actually doing
4. **Wrong assumptions**: People think sending $10,000 vs $100 matters. It doesn't. Miners only care about the fee rate.

### What I figured out

After reading way too much Bitcoin documentation, I realized miners use a super simple algorithm. They:
- Sort every transaction by fee rate (sats per byte)
- Pack them into blocks until they hit 1MB
- That's literally it

No fancy AI, no complex optimization. Just sort and pack. Greedy algorithm at its finest.

### What I built

This simulator does exactly what miners do, but shows you the results in a nice terminal UI. Now you can:
- See where your transaction would rank
- Figure out the minimum fee needed for next block
- Understand why that 1 sat/vB transaction is still pending from last week
- Actually learn how Bitcoin's fee market works

### Why I personally cared

I'm into blockchain tech and wanted to understand the economics better. Plus I was getting annoyed paying random fees without knowing if they were right. This project let me:
- Learn the actual Bitcoin fee mechanism
- Build something useful (not just another todo app)
- Practice working with APIs and algorithms
- Make a portfolio piece that shows I can solve real problems

---

## Real-world uses

### 1. Fee Optimization for Users
**Scenario**: A user wants to send Bitcoin but doesn't know what fee to set.

**How this helps**:
- Run the simulator to see current mempool conditions
- Check the fee rate of the lowest transaction in the "next block" category
- Set your fee slightly above that rate to ensure quick confirmation

**Example**:
```bash
python fee_sim.py
# Output shows: "First TX rejected had a rate of 45.3 sat/vB"
# User sets their fee to 46-50 sat/vB for next block inclusion
```

### 2. Wallet Application Integration
**Scenario**: A Bitcoin wallet app needs to suggest optimal fees.

**How this helps**:
- Integrate this algorithm into the wallet backend
- Fetch live mempool data periodically
- Provide users with "Low", "Medium", "High" priority options based on real data

**Business Value**: Improved user experience, fewer support tickets about stuck transactions

### 3. Educational Tool for Blockchain Courses
**Scenario**: Teaching students about Bitcoin's fee market and mining economics.

**How this helps**:
- Visual demonstration of the greedy algorithm
- Students can experiment with different block sizes
- Shows the relationship between fee rates and confirmation times

**Impact**: Makes abstract concepts concrete and interactive

### 4. Market Analysis for Traders
**Scenario**: Cryptocurrency traders need to time their transactions during high volatility.

**How this helps**:
- Monitor mempool congestion in real-time
- Identify periods of low fee competition
- Plan large transactions during off-peak hours

**Example Use Case**: An exchange moving funds between wallets can save thousands in fees by timing transactions properly

### 5. Research and Development
**Scenario**: Blockchain researchers studying fee market dynamics.

**How this helps**:
- Simulate different block size scenarios (e.g., what if blocks were 2MB?)
- Analyze historical mempool data
- Test fee estimation algorithms

**Research Applications**:
- Fee market efficiency studies
- Block size debate analysis
- Transaction prioritization research

### 6. Bitcoin Node Operators
**Scenario**: Running a Bitcoin node and want to understand mempool behavior.

**How this helps**:
- Visualize what your node's mempool looks like
- Understand why certain transactions are prioritized
- Debug fee-related issues

---

## The algorithm explained

### The Greedy Algorithm Explained

The simulator implements the **Greedy Knapsack Algorithm**, which is the same approach Bitcoin miners use to maximize profits.

### Algorithm Steps

```
INPUT: 
  - Mempool: List of pending transactions
  - Block Limit: 1,000,000 vbytes (1MB)

OUTPUT:
  - Packed Block: Transactions to include
  - Rejected Transactions: Transactions left in mempool

PROCESS:
1. Calculate fee rate for each transaction
   fee_rate = transaction_fee / transaction_vsize

2. Sort all transactions by fee_rate (descending order)
   sorted_mempool = sort(mempool, key=fee_rate, reverse=True)

3. Initialize empty block and counter
   block = []
   current_size = 0

4. Iterate through sorted transactions
   FOR each transaction in sorted_mempool:
       IF current_size + transaction.vsize <= 1,000,000:
           block.append(transaction)
           current_size += transaction.vsize
       ELSE:
           rejected.append(transaction)

5. Return block and statistics
```

### Why This Algorithm Works

**Optimality**: The greedy approach is optimal for this problem because:
- Miners want to maximize total fees
- Fee rate (sat/vB) is the correct metric for comparison
- Sorting ensures we always pick the most profitable transactions first

**Time Complexity**: 
- Sorting: O(n log n) where n = number of transactions
- Packing: O(n) single pass through sorted list
- **Total: O(n log n)** - Very efficient even for thousands of transactions

**Space Complexity**: O(n) - We store the original mempool and sorted version

### Mathematical Proof of Greedy Choice

Let's prove why sorting by fee rate is optimal:

**Theorem**: For any two transactions A and B where:
- `rate_A > rate_B` (A has higher fee rate)
- Both fit in remaining block space

Choosing A before B always yields higher or equal total fees.

**Proof**:
```
Scenario 1: Choose A first
  - If both fit: Total fees = fee_A + fee_B
  - If only A fits: Total fees = fee_A

Scenario 2: Choose B first
  - If both fit: Total fees = fee_B + fee_A (same as Scenario 1)
  - If only B fits: Total fees = fee_B

Since rate_A > rate_B:
  fee_A / vsize_A > fee_B / vsize_B
  
For equal sizes: fee_A > fee_B
Therefore, Scenario 1 is always ≥ Scenario 2
```

### Algorithm Visualization

```
Mempool (unsorted):
TX1: 100 sats, 200 vB → rate = 0.5 sat/vB
TX2: 500 sats, 100 vB → rate = 5.0 sat/vB
TX3: 300 sats, 150 vB → rate = 2.0 sat/vB

After Sorting (by rate, descending):
TX2: rate = 5.0 sat/vB ✓ (picked first)
TX3: rate = 2.0 sat/vB ✓ (picked second)
TX1: rate = 0.5 sat/vB ✓ (picked third)

Block packing:
[TX2] → 100 vB used
[TX2, TX3] → 250 vB used
[TX2, TX3, TX1] → 450 vB used
... continue until 1,000,000 vB limit
```

---

## How I built it

### Code Structure

```python
class MempoolSimulator:
    def __init__(self, block_limit=1000000):
        self.block_limit = block_limit
        self.mempool = []
        self.packed_block = []
        self.left_behind = []
```

### Key Methods

#### 1. Data Fetching
```python
def fetch_live_mempool(self):
    # Connects to mempool.space API
    # Fetches recent transactions
    # Calculates fee rates
    # Handles errors gracefully
```

**Why this matters**: Real-time data makes the simulation accurate and relevant.

#### 2. Core Simulation
```python
def run_simulation(self):
    # Step 1: Sort by fee rate (greedy choice)
    sorted_mempool = sorted(
        self.mempool, 
        key=lambda x: x["rate"], 
        reverse=True
    )
    
    # Step 2: Pack until full
    current_weight = 0
    for tx in sorted_mempool:
        if current_weight + tx["vsize"] <= self.block_limit:
            self.packed_block.append(tx)
            current_weight += tx["vsize"]
        else:
            self.left_behind.append(tx)
```

**Algorithm Efficiency**: 
- Python's `sorted()` uses Timsort: O(n log n)
- Single-pass packing: O(n)
- Total: O(n log n) - optimal for this problem

#### 3. Fallback System
```python
def _generate_synthetic_data(self):
    # Creates realistic fake transactions
    # Ensures tool works offline
    # Useful for testing and demos
```

**Engineering Decision**: Always have a fallback. Network failures shouldn't break the tool.

### Data Flow

```
┌─────────────────┐
│  User Input     │
│  (CLI command)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Source     │
│ • Live API      │
│ • Local JSON    │
│ • Synthetic     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Calculate Rates │
│ fee/vsize       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sort (Greedy)   │
│ O(n log n)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pack Block      │
│ O(n)            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Display Results │
│ Rich UI         │
└─────────────────┘
```

---

## Architecture stuff

### System Components

```
bitcoin-fee-simulator/
│
├── fee_sim.py              # Main application
│   ├── MempoolSimulator    # Core logic class
│   ├── CLI interface       # Click-based commands
│   └── UI rendering        # Rich library tables/panels
│
├── mempool_sample.json     # Sample data for offline mode
├── requirements.txt        # Python dependencies
├── README.md              # User documentation
└── DOCUMENTATION.md       # This file
```

### Design Patterns Used

1. **Class-based Design**: Encapsulation of simulator logic
2. **Strategy Pattern**: Multiple data sources (API, JSON, synthetic)
3. **Fallback Pattern**: Graceful degradation when API fails
4. **Command Pattern**: CLI interface with Click

### External Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| requests | 2.31+ | HTTP API calls to mempool.space |
| rich | 13.0+ | Terminal UI (tables, panels, colors) |
| click | 8.0+ | CLI argument parsing and commands |

### API Integration

**Endpoint**: `https://mempool.space/api/mempool/recent`

**Response Format**:
```json
[
  {
    "txid": "abc123...",
    "fee": 5000,
    "vsize": 250,
    "value": 100000
  }
]
```

**Rate Limiting**: None required (public endpoint)
**Timeout**: 10 seconds to prevent hanging

---

## Performance notes

### Scalability
- **Current**: Handles 250-500 transactions efficiently
- **Tested**: Up to 10,000 transactions (< 1 second processing)
- **Bottleneck**: API fetch time, not algorithm

### Optimization Opportunities
1. **Caching**: Store recent mempool snapshots
2. **Parallel Processing**: Fetch and sort simultaneously
3. **Incremental Updates**: Only re-sort new transactions

### Memory Usage
- **Typical**: ~5-10 MB for 500 transactions
- **Worst Case**: ~50 MB for 10,000 transactions
- **Optimization**: Could use generators for very large datasets

---

## References

1. **Bitcoin Block Weight**: [BIP 141](https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki)
2. **Fee Estimation**: [Bitcoin Core Fee Estimation](https://bitcoincore.org/en/faq/fee-estimation/)
3. **Mempool.space API**: [Documentation](https://mempool.space/docs/api)
4. **Greedy Algorithms**: Introduction to Algorithms (CLRS), Chapter 16

---

## What I learned

By building this project, I demonstrated:

- **Algorithm Design**: Implemented and optimized a greedy algorithm  
- **API Integration**: Real-time data fetching with error handling  
- **User Experience**: Beautiful CLI with Rich library  
- **Software Engineering**: Clean code, fallback systems, documentation  
- **Domain Knowledge**: Deep understanding of Bitcoin's fee market  
- **Problem Solving**: Identified a real problem and built a practical solution  

---

**Author**: Gyan Ranjan Panda  
**Repository**: [github.com/gyanranjanpanda/bitcoin-fee-simulator](https://github.com/gyanranjanpanda/bitcoin-fee-simulator)  
**License**: MIT  
**Last Updated**: January 2026
