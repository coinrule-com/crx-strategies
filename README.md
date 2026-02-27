# Coinrule X Strategies

A standard library of **open-source trading strategies** designed for the **Coinrule X execution platform**.

Strategies in this repository act as **signal generators** and are executed using Coinrule X's managed execution and risk engine.

---

## Strategy Architecture

Strategies in this repository are **signal generators** that can operate in two modes:

### Entry-Only Strategies (`entry_only: true`)

- Generate **entry signals only**
- Exits are fully managed by the Coinrule X risk engine
- **Mandatory managed risk management** (stop-loss, take-profit, trailing, breakeven)
- Best for: trend-following, momentum, breakout strategies

### Entry & Exit Strategies (`entry_only: false`)

- Generate both **entry and exit signals**
- Strategy controls when to close positions
- **Optional risk management** (disabled by default, can be enabled per user)
- Best for: mean-reversion, arbitrage, custom exit logic strategies

All position execution is handled by the **Coinrule X execution layer**, ensuring consistent behavior and safety guarantees across all strategies.

This separation allows:

- reproducible and auditable strategy logic
- flexible risk control (managed or strategy-driven)
- safe execution without exposing private keys
- configurable preferences per user

---

## Execution & Risk Management

Coinrule X provides a configurable risk framework that behaves differently based on strategy type:

### For Entry-Only Strategies

Risk management is **mandatory and enforced**:

- mandatory stop-loss on every position
- take-profit via fixed target or trailing stop
- optional breakeven logic with partial position closes
- configurable position sizing per strategy

Exits are triggered exclusively by the risk engine (SL/TP/trailing/breakeven).

### For Entry & Exit Strategies

Risk management is **optional** (disabled by default):

- strategy controls exit timing via exit signals
- users can opt-in to enable risk management as a safety layer
- when enabled, risk engine acts as a backstop (e.g., emergency stop-loss)
- position sizing remains configurable

### Risk Model Options

When risk management is enabled (mandatory for entry-only, optional for entry & exit):

- **Stop-loss**: mandatory, configurable distance
- **Take-profit**: fixed percentage target or trailing stop
- **Trailing stop**: optional activation after a defined profit threshold
- **Breakeven logic**: partial position close, stop moved to entry, trailing enabled for remainder

### Customization

Users can adjust risk parameters per strategy:

- stop-loss distance
- take-profit method and target
- trailing activation threshold
- breakeven behavior
- position sizing

For entry & exit strategies, users can also toggle whether managed risk management is enabled.

---

## Repository Structure

Strategies are organized into individual folders under `coinrule_x_strategies/strategies/`.

The repository uses a scalable registry system with support for sub-registries.

- `coinrule_x_strategies/registry.yaml`
  Main entry point including all registered strategies.

- `coinrule_x_strategies/strategies/<strategy_name>/registry.yaml`
  Strategy-specific metadata and configuration, including the `entry_only` flag.

- `coinrule_x_strategies/strategies/<strategy_name>/strategy.py`
  Strategy implementation (entry signals, and optionally exit signals).

Each strategy folder also includes a dedicated `README.md` describing its logic, use cases, and risk profile.

### Registry Configuration

Each strategy's `registry.yaml` must include the `entry_only` field:

```yaml
name: my_strategy
version: 1.0.0
entry_only: true  # true = entry signals only, managed risk required
                  # false = entry & exit signals, optional risk management
category: trend
# ... other metadata
```

---

## Multi-Timeframe Strategies

Strategies can operate on multiple timeframes simultaneously using the `market_mode` and `market_aliases` settings.

### Registry Configuration

```yaml
name: volatility_breakout
version: 1.0.0
settings:
  market_mode: "multi"           # "single" (default) or "multi"
  market_aliases: ["ltf", "htf"] # Labels for each timeframe
```

### Indicator Binding

For multi-timeframe strategies, indicators must be bound to specific market aliases using a tuple syntax:

```python
# Single-market strategy (default)
def indicators(self) -> Dict[str, Indicator]:
    return {
        "rsi": RSI(14),
        "ema": EMA(50),
    }

# Multi-market strategy
def indicators(self) -> Dict[str, Tuple[Indicator, str]]:
    return {
        # Indicators bound to lower timeframe
        "rsi_ltf": (RSI(14), "ltf"),
        "ema_ltf": (EMA(50), "ltf"),
        "candle": (Candle(), "ltf"),
        # Indicators bound to higher timeframe
        "rsi_htf": (RSI(14), "htf"),
        "ema_htf": (EMA(50), "htf"),
    }
```

The runner will:

1. Subscribe to candle streams for each market alias (e.g., 5m for `ltf`, 1h for `htf`)
2. Feed candles to indicators based on their market binding
3. Provide indicator history to `evaluate()` with values from the correct timeframe

---

## Installation

```bash
pip install crx-strategies
```

## Available Strategies

- **Trend Rider**: A trend-following strategy designed to capitalize on strong directional markets. It enters positions only when multiple trend and momentum indicators align, aiming to stay in trades during sustained moves while avoiding choppy conditions.
- **Bounce Recovery**: A mean-reversion strategy designed to capture controlled pullbacks and oversold conditions. Aim to profit from short-term price rebounds while applying strict risk controls to avoid prolonged drawdowns.
- **Volatility Breakout**: A strategy designed to trade sudden expansions in volatility after periods of compression. Aim to capture fast, directional moves triggered by volatility regime shifts.

## Contributing

Contributions are welcome.

To add a new strategy:

1. Create a new folder under `coinrule_x_strategies/strategies/`.
2. Implement your strategy class by inheriting from `Strategy` base class.
3. Add a `registry.yaml` file with strategy metadata.
4. Validate your registry file using the included script:

   ```bash
   # Using installed CLI
   coinrule_x-validate-strategies coinrule_x_strategies/strategies/<your_strategy>/registry.yaml

   # Or using poetry during development
   poetry run python coinrule_x_strategies/validation.py coinrule_x_strategies/strategies/<your_strategy>/registry.yaml
   ```

5. Register your strategy by adding its sub-registry path to `coinrule_x_strategies/registry.yaml`.

**All strategies should:**

- generate entry signals (and optionally exit signals)
- specify `entry_only: true` or `entry_only: false` in registry
- remain stateless
- avoid embedding execution or position management logic

### Submission Process

1.  **Fork the Repository**: Create a fork of the repository to your own GitHub account.
2.  **Create a Feature Branch**: Create a new branch for your changes (e.g., `feat/add-abc-strategy`).
3.  **Implement & Test**: Apply your changes and ensure all tests pass.
4.  **Create Pull Request**: Submit a pull request to the main repository.

_Note: Version numbers and the official CHANGELOG will be updated by maintainers upon release._

### Development Guidelines

- **Type Hinting**: All methods must be fully type-hinted.
- **Pandas/Numpy**: Use vectorized operations where possible for performance.
- **Zero Dependencies**: Do not add new external dependencies without prior discussion.

## Disclaimer

Strategies provided in this repository are open-source and intended for systematic trading experimentation.
They do not constitute financial or investment advice.
Trading involves risk, and users are fully responsible for their configuration and capital allocation.
