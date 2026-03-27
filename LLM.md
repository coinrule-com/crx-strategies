# Coinrule X Strategies - LLM Strategy Generation Guide

This document provides comprehensive information about available indicators in the Coinrule X strategy library for use in AI-generated trading strategies.

## Overview

This guide explains how to generate new trading strategies using the Coinrule X framework, as well as how to utilize the available prebuilt indicators. It also outlines recommended practices and common design patterns if you want to create a custom strategy.

### Core Principles

- **Stateless**: Strategies should not reference specific coins or tokens (for example, avoid statements like "buy BTC").
- **Entry-only or Entry-Exit**: You can create strategies that define conditions for opening positions (long or short) only, or include both entry and exit conditions.
- **Coin-agnostic**: Strategies should be applicable to any trading pair and any type of market (such as crypto spot, perpetuals, stocks, or commodities).
- **Timeframe-parameterized**: Strategy timeframes are configurable at runtime. You can also use multiple timeframes within a single strategy by requesting multiple instances of the same indicator type.

### Position Context

The `evaluate()` method receives an optional `position` parameter — the current position state persisted by the execution engine. **Use this instead of instance variables** to track whether a position is open.

```python
from coinrule_x_strategies.core import PositionContext

# position is None when no open position exists
# When a position exists:
#   position.side        → "LONG" or "SHORT"
#   position.entry_price → average entry price
#   position.quantity    → total position size
#   position.legs        → number of legs (1 = single entry, >1 = DCA)
#   position.pnl_pct     → unrealized P&L % at current price (or None)
```

**Why not instance variables?** Strategy objects live in the runner's memory. If the runner restarts, all instance state (like `self._entered = True`) is lost, but the actual position still exists on the exchange. The `position` parameter comes from persistent storage and survives restarts.

### Signal Types

Strategies return signals using the `SignalSide` enum:

```python
from coinrule_x_strategies.core import SignalSide

class SignalSide(Enum):
    OPEN_LONG = "OPEN_LONG"      # Enter a long position
    OPEN_SHORT = "OPEN_SHORT"    # Enter a short position
    CLOSE_LONG = "CLOSE_LONG"    # Exit a long position (entry & exit strategies only)
    CLOSE_SHORT = "CLOSE_SHORT"  # Exit a short position (entry & exit strategies only)
    WAIT = "WAIT"                # No action - wait for conditions
```

Signals are returned as a `Signal` object:

```python
from coinrule_x_strategies.core import Signal

Signal(
    side=SignalSide.OPEN_LONG,       # Required: the signal type
    confidence=0.85,                  # Optional: confidence score 0.0-1.0 (default: 1.0)
    reason="Strong bullish trend",    # Optional: human-readable explanation
    metadata={"rsi": 45, "adx": 30}   # Optional: additional data for logging/analysis
)
```

### Strategy Types

Strategies operate in one of two modes, determined by the `entry_only` flag in the registry:

#### Entry-Only Strategies (`entry_only: true`)

- Return only `OPEN_LONG`, `OPEN_SHORT`, or `WAIT` signals
- **Do NOT return `CLOSE_LONG` or `CLOSE_SHORT`** - exits are fully managed by the Coinrule X risk engine
- Risk management (stop-loss, take-profit, trailing, breakeven) is **mandatory and enforced**
- Best for: trend-following, momentum, breakout strategies

#### Entry & Exit Strategies (`entry_only: false`)

- Can return all signal types including `CLOSE_LONG` and `CLOSE_SHORT`
- Strategy controls when to close positions via exit signals
- Risk management is **optional** (disabled by default, users can enable as a safety layer)
- Best for: mean-reversion, arbitrage, strategies with custom exit logic

**IMPORTANT**: When generating a strategy, always clarify which mode is intended. Entry-only strategies must NOT return `CLOSE_LONG` or `CLOSE_SHORT` signals.

## Architecture

Strategies are organized into individual folders under `coinrule_x_strategies/strategies/`. Each strategy folder contains:

- `strategy.py` - Strategy implementation (entry signals, and optionally exit signals)
- `registry.yaml` - Strategy-specific metadata and configuration
- `README.md` - Documentation describing logic, use cases, and risk profile

### Registry Configuration

Each strategy requires a `registry.yaml` file with the following structure:

```yaml
name: my_strategy # Unique strategy identifier
version: 1.0.0 # Semantic version
entry_only:
  true # true = entry signals only (OPEN_LONG/OPEN_SHORT/WAIT)
  # false = entry & exit signals (all SignalSide values)
category: trend # Strategy category: trend, momentum, mean_reversion, breakout, volatility
settings:
  market_mode: "single" # "single" (default) or "multi" for multi-timeframe
  market_aliases: [] # Required if market_mode is "multi", e.g., ["ltf", "htf"]
```

**IMPORTANT**: The `entry_only` field is mandatory and determines:

- Which `SignalSide` values are valid returns from `evaluate()`
- Whether risk management is mandatory (entry-only) or optional (entry & exit)

## Required Imports

Every strategy must include these core imports:

```python
from typing import List, Dict, Any, Optional
from coinrule_x_strategies.core import Strategy, Signal, SignalSide, PositionContext
from coinrule_x_indicators.core import Indicator
```

For multi-timeframe strategies, also import `Tuple`:

```python
from typing import List, Dict, Any, Tuple
```

## Available Indicators

For all available prebuilt indicators, please refer to:

- https://raw.githubusercontent.com/coinrule-com/crx-indicators/refs/tags/main/LLM.md - _raw file for LLMs_
- https://github.com/coinrule-com/crx-indicators/blob/main/LLM.md - _version for humans_

## Strategy Writing Guidelines

### 1. Strategy Structure

A strategy must:

- Inherit from the `Strategy` base class
- Implement `indicators()` method to define required indicators
- Implement `evaluate()` method to return a `Signal` based on indicator values and position context
- Be stateless (no coin/token references, no specific candle timeframes, no instance variables for tracking position state)
- Handle insufficient data gracefully (return `WAIT` signal)

**Example Strategy Template:**

```python
from typing import List, Dict, Any, Optional
from coinrule_x_strategies.core import Strategy, Signal, SignalSide, PositionContext
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators import SMA, RSI, Candle, VolumeSMA

class MyStrategy(Strategy):
    """
    A trend-following strategy with volume confirmation.
    ENTRY LOGIC ONLY - exits managed by risk engine.
    """

    def __init__(self,
                 sma_fast_period: int = 20,
                 sma_slow_period: int = 50,
                 rsi_period: int = 14,
                 volume_period: int = 20):
        super().__init__(
            sma_fast_period=sma_fast_period,
            sma_slow_period=sma_slow_period,
            rsi_period=rsi_period,
            volume_period=volume_period
        )

    def indicators(self) -> Dict[str, Indicator]:
        """Define indicators used by this strategy."""
        return {
            "sma_fast": SMA(period=self.config['sma_fast_period']),
            "sma_slow": SMA(period=self.config['sma_slow_period']),
            "rsi": RSI(period=self.config['rsi_period']),
            "volume": Candle(field="volume"),
            "volume_sma": VolumeSMA(period=self.config['volume_period']),
        }

    def evaluate(self, indicators: Dict[str, List[Any]], position: Optional[PositionContext] = None) -> Signal:
        """Evaluate indicators and return a trading signal."""
        # Always check for sufficient data first
        if len(indicators["sma_slow"]) < self.config['sma_slow_period']:
            return Signal(side=SignalSide.WAIT, reason="Insufficient data")

        # Get latest values
        sma_fast = indicators["sma_fast"][-1]
        sma_slow = indicators["sma_slow"][-1]
        rsi = indicators["rsi"][-1]
        volume = indicators["volume"][-1]
        volume_sma = indicators["volume_sma"][-1]

        # Check for volume confirmation
        has_volume = volume > volume_sma

        # Long entry conditions
        if sma_fast > sma_slow and rsi < 70 and has_volume:
            return Signal(
                side=SignalSide.OPEN_LONG,
                reason=f"Bullish crossover with volume (RSI: {rsi:.2f})",
                metadata={"rsi": rsi, "sma_fast": sma_fast, "sma_slow": sma_slow}
            )

        # Short entry conditions
        if sma_fast < sma_slow and rsi > 30 and has_volume:
            return Signal(
                side=SignalSide.OPEN_SHORT,
                reason=f"Bearish crossover with volume (RSI: {rsi:.2f})",
                metadata={"rsi": rsi, "sma_fast": sma_fast, "sma_slow": sma_slow}
            )

        return Signal(side=SignalSide.WAIT, reason="No entry conditions met")
```

### 2. Common Strategy Patterns

These patterns show the condition logic within `evaluate()`. Assume `indicators` is the dict passed to evaluate.

#### Trend Following

```python
# Moving average crossover with trend strength
sma_fast = indicators["sma_fast"][-1]
sma_slow = indicators["sma_slow"][-1]
adx = indicators["adx"][-1]

# Entry when fast MA crosses above slow MA with strong trend
if sma_fast > sma_slow and adx["adx"] > 25:
    return Signal(side=SignalSide.OPEN_LONG, reason="Bullish trend crossover")
```

#### Mean Reversion

```python
# RSI oversold bounce
rsi = indicators["rsi"][-1]
sma_200 = indicators["sma_200"][-1]
close = indicators["close"][-1]

# Entry when RSI oversold but above long-term MA
if rsi < 30 and close > sma_200:
    return Signal(side=SignalSide.OPEN_LONG, reason="Oversold bounce")
```

#### Breakout

```python
# Donchian channel breakout with volume
donchian = indicators["donchian"][-1]
close = indicators["close"][-1]
volume = indicators["volume"][-1]
volume_sma = indicators["volume_sma"][-1]

# Entry on upper channel breakout with high volume
if close > donchian["upper"] and volume > volume_sma * 1.5:
    return Signal(side=SignalSide.OPEN_LONG, reason="Breakout with volume")
```

#### Volatility

```python
# Bollinger Band squeeze breakout
bb = indicators["bb"][-1]
close = indicators["close"][-1]

# Entry when bands compressed then price breaks out
if bb["bandwidth"] < 0.1 and close > bb["upper"]:
    return Signal(side=SignalSide.OPEN_LONG, reason="Squeeze breakout")
```

### 3. Multi-Timeframe Considerations

**Do NOT hardcode timeframes.** Use parameterized periods that scale:

```python
# GOOD: Relative periods that work on any timeframe
fast_ma = SMA(period=20)   # Works on 1h, 4h, 1d, etc.
slow_ma = SMA(period=50)

# BAD: Don't reference specific timeframes
# "Use 1-hour candles for fast MA"  ❌
```

See the [Multi-Timeframe Strategies](#multi-timeframe-strategies) section for details on using multiple timeframes or markets.

### 4. Indicator Value Access

In the `evaluate()` method, indicator values are accessed from the `indicators` dictionary:

```python
def evaluate(self, indicators: Dict[str, List[Any]]) -> Signal:
    # Latest value
    current_rsi = indicators["rsi"][-1]

    # Previous value (one bar back)
    prev_rsi = indicators["rsi"][-2]

    # Historical value (n bars back)
    older_rsi = indicators["rsi"][-5]
```

**Single-value indicators** (SMA, EMA, RSI, ATR, Price, Candle fields) return scalar values:

```python
rsi = indicators["rsi"][-1]           # float: 45.5
sma = indicators["sma_200"][-1]       # float: 1850.25
close = indicators["close"][-1]       # float: 1875.00
```

**Multi-value indicators** (BollingerBands, DonchianChannels, ADX) return dictionaries:

```python
bb = indicators["bb"][-1]
# bb = {"upper": 1900.0, "middle": 1850.0, "lower": 1800.0, "bandwidth": 0.054}
upper_band = bb["upper"]

adx_data = indicators["adx"][-1]
# adx_data = {"adx": 28.5, "plus_di": 25.0, "minus_di": 18.0}
adx_value = adx_data["adx"]

donchian = indicators["donchian"][-1]
# donchian = {"upper": 1920.0, "middle": 1860.0, "lower": 1800.0}
```

### 5. Comparison Operators

Available for building conditions:

- `>` greater than
- `<` less than
- `>=` greater than or equal
- `<=` less than or equal
- `==` equal
- `!=` not equal

Combine with boolean operators:

- `and` - all conditions must be true
- `or` - at least one condition must be true
- `not` - negation

---

## Best Practices

### Strategy Design

1. **Keep it simple**: Start with 2-3 indicators, add complexity only if needed
2. **Avoid overfitting**: Don't create overly specific conditions with many parameters
3. **Volume confirmation**: Add volume checks to validate price moves
4. **Trend filters**: Use long-term MAs or ADX to filter for trending markets
5. **Combine indicator types**: Mix trend + momentum + volatility for robust signals
6. **Test assumptions**: Ensure conditions make logical sense (e.g., RSI < 30 = oversold)
7. **Document your logic**: Add comments explaining why each condition matters

### Code Quality Requirements

1. **Type Hinting**: All methods must be fully type-hinted

   ```python
   def indicators(self) -> Dict[str, Indicator]:  # ✅
   def evaluate(self, indicators: Dict[str, List[Any]], position: Optional[PositionContext] = None) -> Signal:  # ✅
   ```

2. **Data Validation**: Always check for sufficient data before accessing indicator values

   ```python
   if len(indicators["sma"]) < required_periods:
       return Signal(side=SignalSide.WAIT, reason="Insufficient data")
   ```

3. **Handle Historical Access**: When accessing previous values (e.g., `indicators["bb"][-2]`), ensure the list is long enough

4. **Use Vectorized Operations**: When possible, use numpy/pandas operations for performance

### Signal Guidelines

1. **Single Signal per Evaluation**: The `evaluate()` method must return exactly one `Signal`
2. **Always Return a Signal**: Never raise exceptions; return `SignalSide.WAIT` for uncertain conditions
3. **Provide Meaningful Reasons**: Include context in the `reason` field for debugging and logging
4. **Include Metadata**: Add relevant indicator values to `metadata` for analysis and backtesting
5. **Confidence Scoring**: Use the `confidence` field (0.0-1.0) to indicate signal strength when applicable

### What Strategies Must NOT Do

- **No instance variable state**: Do not use `self._entered`, `self._state`, etc. to track position state — use the `position` parameter instead (it survives runner restarts)
- **No risk management logic**: Do not implement stop-loss, take-profit, or trailing stops (handled by execution layer)
- **No order execution**: Do not place orders or interact with exchanges
- **No external API calls**: Do not fetch external data; use only provided indicators
- **No file I/O**: Do not read/write files
- **No sleep/delays**: Strategies must return immediately

---

## Common Pitfalls to Avoid

❌ **Don't use instance variables to track position state:**

```python
# BAD - Instance state is lost on runner restart
def __init__(self):
    self._entered = False  # ❌ Lost if runner restarts

def evaluate(self, indicators, position=None):
    if not self._entered:  # ❌ Will re-buy after restart
        self._entered = True
        return Signal(side=SignalSide.OPEN_LONG)
```

```python
# GOOD - Use the position parameter (persisted)
def evaluate(self, indicators, position=None):
    if position is None:
        return Signal(side=SignalSide.OPEN_LONG, reason="No position — enter")
    if position.side == "LONG":
        return Signal(side=SignalSide.CLOSE_LONG, reason="Already in — exit")
    return Signal(side=SignalSide.WAIT)
```

❌ **Don't reference specific assets:**

```python
# BAD
if ticker == "BTC" and rsi < 30:
    return Signal(side=SignalSide.OPEN_LONG)
```

❌ **Don't hardcode timeframes:**

```python
# BAD
# "This strategy works on 1-hour charts only"
```

❌ **Don't use future data (look-ahead bias):**

```python
# BAD - Using future candle data
if indicators["close"][i+1] > indicators["close"][i]:  # ❌
```

❌ **Don't return CLOSE signals in entry-only strategies:**

```python
# BAD - entry_only: true strategy should NOT return exit signals
return Signal(side=SignalSide.CLOSE_LONG)  # ❌ for entry-only strategies
```

❌ **Don't implement risk management logic:**

```python
# BAD - Risk management is handled by the execution layer
if price < entry_price * 0.95:  # ❌ Don't implement stop-loss
    return Signal(side=SignalSide.CLOSE_LONG)
```

❌ **Don't skip data validation:**

```python
# BAD - May crash if not enough data
def evaluate(self, indicators):
    rsi = indicators["rsi"][-1]  # ❌ Could fail if list is empty
```

✅ **Do write generic, reusable conditions:**

```python
# GOOD
def evaluate(self, indicators: Dict[str, List[Any]]) -> Signal:
    if len(indicators["rsi"]) < self.config['rsi_period']:
        return Signal(side=SignalSide.WAIT, reason="Insufficient data")

    rsi = indicators["rsi"][-1]
    sma_200 = indicators["sma_200"][-1]
    close = indicators["close"][-1]

    if rsi < 30 and close > sma_200:
        return Signal(
            side=SignalSide.OPEN_LONG,
            reason=f"Oversold bounce (RSI: {rsi:.2f})",
            metadata={"rsi": rsi, "sma_200": sma_200}
        )

    return Signal(side=SignalSide.WAIT, reason="No conditions met")
```

> **Dependency Management:**
> Only use imports that are present in the existing code examples or provided library. **Do not install/import any new dependencies or external packages** beyond those shown above or documented as part of the Coinrule X strategy library.

---

## Example: Complete Strategy

```python
from typing import List, Dict, Any, Optional
from coinrule_x_strategies.core import Strategy, Signal, SignalSide, PositionContext
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators import EMA, ADX, BollingerBands, DonchianChannels, Candle

class VolatilityBreakoutStrategy(Strategy):
    """
    Entry Strategy: Volatility compression followed by breakout with trend confirmation.

    ENTRY LOGIC ONLY - exits managed by risk engine.

    Logic:
    1. Bollinger Bands are compressed (low volatility)
    2. Bollinger Bandwidth starts expanding (volatility increasing)
    3. Price breaks out of Donchian Channel
    4. Trend strength confirmed by ADX > 20
    5. Price is on the correct side of EMA 50
    """

    def __init__(self,
                 bb_period: int = 20,
                 bb_std_dev: float = 2.0,
                 donchian_period: int = 20,
                 ema_period: int = 50,
                 adx_period: int = 14,
                 adx_threshold: float = 20.0,
                 bandwidth_threshold: float = 0.15):
        super().__init__(
            bb_period=bb_period,
            bb_std_dev=bb_std_dev,
            donchian_period=donchian_period,
            ema_period=ema_period,
            adx_period=adx_period,
            adx_threshold=adx_threshold,
            bandwidth_threshold=bandwidth_threshold
        )
        self.adx_threshold = adx_threshold
        self.bandwidth_threshold = bandwidth_threshold

    def indicators(self) -> Dict[str, Indicator]:
        return {
            "close": Candle(field="close"),
            "bb": BollingerBands(
                period=self.config['bb_period'],
                std_dev=self.config['bb_std_dev']
            ),
            "donchian": DonchianChannels(period=self.config['donchian_period']),
            "ema": EMA(period=self.config['ema_period']),
            "adx": ADX(period=self.config['adx_period']),
        }

    def evaluate(self, indicators: Dict[str, List[Any]], position: Optional[PositionContext] = None) -> Signal:
        # Minimum data check
        min_periods = max(
            self.config['bb_period'],
            self.config['donchian_period'],
            self.config['ema_period'],
            self.config['adx_period']
        )
        if len(indicators["close"]) < min_periods + 1:
            return Signal(side=SignalSide.WAIT, reason="Insufficient data")

        # Get current and previous values
        close = indicators["close"][-1]
        bb_current = indicators["bb"][-1]
        bb_prev = indicators["bb"][-2]
        donchian = indicators["donchian"][-1]
        ema = indicators["ema"][-1]
        adx_data = indicators["adx"][-1]

        current_bandwidth = bb_current['bandwidth']
        prev_bandwidth = bb_prev['bandwidth']
        adx_val = adx_data['adx']

        # Check for volatility compression and expansion
        was_compressed = prev_bandwidth < self.bandwidth_threshold
        is_expanding = current_bandwidth > prev_bandwidth
        has_trend_strength = adx_val > self.adx_threshold

        # Bullish conditions
        if (was_compressed and is_expanding and has_trend_strength and
            close > donchian['upper'] and close > ema):
            return Signal(
                side=SignalSide.OPEN_LONG,
                confidence=min(adx_val / 50.0, 1.0),
                reason=f"Volatility breakout bullish (ADX: {adx_val:.2f})",
                metadata={
                    "bandwidth": current_bandwidth,
                    "adx": adx_val,
                    "close": close,
                    "donchian_upper": donchian['upper']
                }
            )

        # Bearish conditions
        if (was_compressed and is_expanding and has_trend_strength and
            close < donchian['lower'] and close < ema):
            return Signal(
                side=SignalSide.OPEN_SHORT,
                confidence=min(adx_val / 50.0, 1.0),
                reason=f"Volatility breakout bearish (ADX: {adx_val:.2f})",
                metadata={
                    "bandwidth": current_bandwidth,
                    "adx": adx_val,
                    "close": close,
                    "donchian_lower": donchian['lower']
                }
            )

        return Signal(
            side=SignalSide.WAIT,
            reason="No breakout conditions met",
            metadata={"bandwidth": current_bandwidth, "adx": adx_val}
        )
```

---

## Example: Entry & Exit Strategy

For strategies with custom exit logic (`entry_only: false`):

```python
from typing import List, Dict, Any, Optional
from coinrule_x_strategies.core import Strategy, Signal, SignalSide, PositionContext
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators import RSI, SMA, Candle

class MeanReversionStrategy(Strategy):
    """
    Mean reversion strategy with custom exit logic.

    ENTRY & EXIT STRATEGY - manages its own exits.

    Entry: Buy oversold (RSI < 30) above long-term trend
    Exit: Close when RSI normalizes (RSI > 50) or overbought (RSI > 70)
    """

    def __init__(self,
                 rsi_period: int = 14,
                 sma_period: int = 200,
                 oversold_threshold: float = 30.0,
                 exit_threshold: float = 50.0,
                 overbought_threshold: float = 70.0):
        super().__init__(
            rsi_period=rsi_period,
            sma_period=sma_period,
            oversold_threshold=oversold_threshold,
            exit_threshold=exit_threshold,
            overbought_threshold=overbought_threshold
        )

    def indicators(self) -> Dict[str, Indicator]:
        return {
            "close": Candle(field="close"),
            "rsi": RSI(period=self.config['rsi_period']),
            "sma": SMA(period=self.config['sma_period']),
        }

    def evaluate(self, indicators: Dict[str, List[Any]], position: Optional[PositionContext] = None) -> Signal:
        if len(indicators["sma"]) < self.config['sma_period']:
            return Signal(side=SignalSide.WAIT, reason="Insufficient data")

        close = indicators["close"][-1]
        rsi = indicators["rsi"][-1]
        sma = indicators["sma"][-1]

        # Exit conditions — only check when we have an open position
        if position is not None and position.side == "LONG":
            if rsi > self.config['overbought_threshold']:
                return Signal(
                    side=SignalSide.CLOSE_LONG,
                    reason=f"RSI overbought ({rsi:.2f})",
                    metadata={"rsi": rsi}
                )

            if rsi > self.config['exit_threshold']:
                return Signal(
                    side=SignalSide.CLOSE_LONG,
                    reason=f"RSI normalized ({rsi:.2f})",
                    metadata={"rsi": rsi}
                )

        # Entry conditions — only when no position is open
        if position is None and rsi < self.config['oversold_threshold'] and close > sma:
            return Signal(
                side=SignalSide.OPEN_LONG,
                reason=f"Oversold bounce opportunity (RSI: {rsi:.2f})",
                metadata={"rsi": rsi, "sma": sma, "close": close}
            )

        return Signal(side=SignalSide.WAIT, reason="No conditions met")
```

**Registry for Entry & Exit Strategy:**

```yaml
name: mean_reversion
version: 1.0.0
entry_only: false # Allows CLOSE_LONG and CLOSE_SHORT signals
category: mean_reversion
```

---

## Multi-Timeframe Strategies

Strategies can use indicators across multiple timeframes by binding them to market aliases.

### Configuration

In the strategy's `registry.yaml`:

```yaml
settings:
  market_mode: "multi" # Enable multi-timeframe
  market_aliases: ["ltf", "htf"] # Define timeframe labels
```

### Indicator Binding Syntax

For single-timeframe strategies (default):

```python
def indicators(self) -> Dict[str, Indicator]:
    return {
        "rsi": RSI(14),
        "ema": EMA(50),
    }
```

For multi-timeframe strategies, use tuple syntax `(Indicator, market_alias)`:

```python
def indicators(self) -> Dict[str, Tuple[Indicator, str]]:
    return {
        # Lower timeframe indicators
        "rsi_ltf": (RSI(14), "ltf"),
        "ema_ltf": (EMA(50), "ltf"),
        "bb_ltf": (BollingerBands(20, 2.0), "ltf"),
        "candle": (Candle(), "ltf"),

        # Higher timeframe indicators
        "rsi_htf": (RSI(14), "htf"),
        "ema_htf": (EMA(200), "htf"),
        "adx_htf": (ADX(14), "htf"),
    }
```

### How It Works

1. The runner subscribes to candle streams for each market alias (e.g., 5m for `ltf`, 1h for `htf`)
2. Candles are fed to indicators based on their market binding
3. In `evaluate()`, each indicator's history contains values from its bound timeframe

### Use Cases

- **Trend confirmation**: Use higher timeframe for trend direction, lower for entry timing
- **Multi-timeframe divergence**: Compare RSI across timeframes
- **Volatility filtering**: Check higher timeframe ADX before entering on lower timeframe signals

### Multi-Market Strategies

The same `market_mode: "multi"` mechanism can be used for **multi-market** strategies, where indicators are computed on different assets (e.g., BTC and ETH) rather than different timeframes.

**Registry Configuration:**

```yaml
name: cross_market_momentum
version: 1.0.0
entry_only: true
category: momentum
settings:
  market_mode: "multi"
  market_aliases: ["primary", "secondary"] # e.g., BTC and ETH
```

**Strategy Example:**

```python
from typing import List, Dict, Any, Tuple
from coinrule_x_strategies.core import Strategy, Signal, SignalSide, PositionContext
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators import RSI, EMA, Candle

class CrossMarketMomentumStrategy(Strategy):
    """
    Multi-market strategy that compares momentum between two assets.

    ENTRY LOGIC ONLY - exits managed by risk engine.

    Logic: Enter long on secondary asset when both primary and secondary
    show bullish momentum alignment (e.g., buy ETH when both BTC and ETH
    have RSI > 50 and price above EMA).
    """

    def __init__(self, rsi_period: int = 14, ema_period: int = 50):
        super().__init__(rsi_period=rsi_period, ema_period=ema_period)

    def indicators(self) -> Dict[str, Tuple[Indicator, str]]:
        return {
            # Primary market indicators (e.g., BTC)
            "rsi_primary": (RSI(self.config['rsi_period']), "primary"),
            "ema_primary": (EMA(self.config['ema_period']), "primary"),
            "close_primary": (Candle(field="close"), "primary"),

            # Secondary market indicators (e.g., ETH)
            "rsi_secondary": (RSI(self.config['rsi_period']), "secondary"),
            "ema_secondary": (EMA(self.config['ema_period']), "secondary"),
            "close_secondary": (Candle(field="close"), "secondary"),
        }

    def evaluate(self, indicators: Dict[str, List[Any]], position: Optional[PositionContext] = None) -> Signal:
        if len(indicators["ema_primary"]) < self.config['ema_period']:
            return Signal(side=SignalSide.WAIT, reason="Insufficient data")

        # Primary market values
        rsi_primary = indicators["rsi_primary"][-1]
        ema_primary = indicators["ema_primary"][-1]
        close_primary = indicators["close_primary"][-1]

        # Secondary market values
        rsi_secondary = indicators["rsi_secondary"][-1]
        ema_secondary = indicators["ema_secondary"][-1]
        close_secondary = indicators["close_secondary"][-1]

        # Check momentum alignment across both markets
        primary_bullish = rsi_primary > 50 and close_primary > ema_primary
        secondary_bullish = rsi_secondary > 50 and close_secondary > ema_secondary

        if primary_bullish and secondary_bullish:
            return Signal(
                side=SignalSide.OPEN_LONG,
                reason=f"Cross-market bullish alignment",
                metadata={
                    "rsi_primary": rsi_primary,
                    "rsi_secondary": rsi_secondary
                }
            )

        primary_bearish = rsi_primary < 50 and close_primary < ema_primary
        secondary_bearish = rsi_secondary < 50 and close_secondary < ema_secondary

        if primary_bearish and secondary_bearish:
            return Signal(
                side=SignalSide.OPEN_SHORT,
                reason=f"Cross-market bearish alignment",
                metadata={
                    "rsi_primary": rsi_primary,
                    "rsi_secondary": rsi_secondary
                }
            )

        return Signal(side=SignalSide.WAIT, reason="No cross-market alignment")
```

**Note**: The strategy remains coin-agnostic. The actual assets (BTC, ETH, etc.) are configured at runtime by the execution layer, not hardcoded in the strategy.

---

## Questions?

If you need an indicator that doesn't exist:

1. Check if you can combine existing indicators to achieve the same goal
2. If not, create a custom `CandleIndicator` based on [Coinrule X Indicator Library](https://github.com/coinrule-com/crx-indicators)
3. Ensure your custom indicator follows the same patterns as built-in indicators
