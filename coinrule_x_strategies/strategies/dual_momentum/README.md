# Dual Momentum Strategy

## Overview

A multi-timeframe momentum strategy that combines higher timeframe trend analysis with lower timeframe entry/exit precision. This strategy manages its own position exits based on momentum divergence and extreme RSI conditions.

## Strategy Type

**Entry & Exit Strategy** (`entry_only: false`)

This strategy generates both entry signals (`OPEN_LONG`, `OPEN_SHORT`) and exit signals (`CLOSE_LONG`, `CLOSE_SHORT`). Risk management settings are optional and can be used as a safety layer.

## Core Logic

### Multi-Timeframe Approach

The strategy uses two timeframes with different roles:

- **Higher Timeframe (HTF)**: Determines trend direction and strength
  - Provides directional bias (bullish/bearish)
  - Filters out low-probability setups via ADX
  - Triggers exits when trend weakens

- **Lower Timeframe (LTF)**: Provides entry timing and exit signals
  - Confirms momentum in the same direction as HTF
  - Detects overbought/oversold conditions for exits
  - Provides precise entry timing with RSI momentum

### Entry Conditions

**Long Entry:**

1. HTF must show strong bullish trend:
   - Price above HTF EMA
   - RSI above momentum threshold (default: 50)
   - ADX above threshold (default: 25)
   - +DI > -DI (directional movement)

2. LTF must confirm with bullish momentum:
   - Price above LTF EMA
   - RSI above momentum threshold
   - RSI not yet overbought (< 70)
   - RSI turning up (momentum acceleration)

**Short Entry:**

1. HTF must show strong bearish trend:
   - Price below HTF EMA
   - RSI below momentum threshold (default: 50)
   - ADX above threshold (default: 25)
   - -DI > +DI (directional movement)

2. LTF must confirm with bearish momentum:
   - Price below LTF EMA
   - RSI below momentum threshold
   - RSI not yet oversold (> 30)
   - RSI turning down (momentum acceleration)

### Exit Conditions

**Exit Long:**

- LTF RSI becomes overbought (> 70)

**Exit Short:**

- LTF RSI becomes oversold (< 30)

**Note on HTF Reversals:**
When HTF conditions reverse (e.g., turn bearish while in a long position), the strategy will generate an opposite entry signal (OPEN_SHORT). The execution layer handles closing the existing position before opening the new one. This design keeps the strategy stateless and avoids ambiguity between exit signals and reversal signals.

## Indicators Used

### Lower Timeframe (LTF):

- **Candle (close)**: Current price for trend position
- **EMA**: Fast-moving average for trend direction
- **RSI**: Momentum oscillator for entry timing and exit signals

### Higher Timeframe (HTF):

- **Candle (close)**: Current price for trend position
- **EMA**: Slower-moving average for primary trend direction
- **RSI**: Momentum oscillator for momentum divergence detection
- **ADX**: Trend strength filter (with +DI/-DI for directional bias)

## Parameters

| Parameter                | Default | Description                                     |
| ------------------------ | ------- | ----------------------------------------------- |
| `ema_period_ltf`         | 20      | Lower timeframe EMA period for entry timing     |
| `ema_period_htf`         | 50      | Higher timeframe EMA period for trend direction |
| `rsi_period`             | 14      | RSI period for both timeframes                  |
| `adx_period`             | 14      | ADX period for higher timeframe trend strength  |
| `adx_threshold`          | 25.0    | Minimum ADX value to consider trend strong      |
| `rsi_overbought`         | 70.0    | RSI level that triggers long exit               |
| `rsi_oversold`           | 30.0    | RSI level that triggers short exit              |
| `rsi_momentum_threshold` | 50.0    | RSI level defining bullish vs bearish momentum  |

## Use Cases

### Ideal Market Conditions

- **Trending markets**: Strong directional moves on HTF
- **Volatile markets**: Clear momentum swings on LTF
- **Clean trends**: Price respecting EMAs on both timeframes

### Best Timeframe Combinations

- **5m / 1h**: Day trading with hourly trend filter
- **15m / 4h**: Swing trading with 4-hour trend filter
- **1h / 1d**: Position trading with daily trend filter

## Advantages

1. **Reduced False Signals**: HTF filter eliminates noise from LTF
2. **Better Entry Timing**: LTF provides precise entry points within HTF trend
3. **Early Exit Detection**: LTF momentum extremes signal exits before major reversals
4. **Momentum Confirmation**: Both timeframes must agree for entries
5. **Trend Strength Filter**: ADX ensures only strong trends are traded

## Limitations

1. **Lag on Trend Changes**: Multi-timeframe confirmation causes delayed entries
2. **Chop Sensitivity**: Can exit prematurely in ranging markets with high LTF volatility
3. **Parameter Sensitivity**: Requires optimization for specific timeframe combinations
4. **Missed Moves**: Strong HTF moves may not get LTF confirmation
5. **Whipsaw Risk**: Frequent exits if LTF RSI oscillates around extreme levels

## Risk Considerations

- **Exit Discipline**: Strategy exits are not guaranteed to prevent losses
- **Trend Reversals**: HTF EMA cross may lag actual trend change
- **Momentum Divergence**: LTF/HTF disagreement can cause premature exits
- **Optional Risk Management**: Consider enabling stop-loss as safety layer

## Configuration Example

```yaml
markets:
  - alias: "ltf"
    venue: "hyperliquid"
    symbol: "BTC"
    asset_type: "perp"
    interval: "5m"

  - alias: "htf"
    venue: "hyperliquid"
    symbol: "BTC"
    asset_type: "perp"
    interval: "1h"

strategy:
  id: "dual_momentum"
  version: "0.1.0"
  arguments:
    ema_period_ltf: 20
    ema_period_htf: 50
    rsi_period: 14
    adx_period: 14
    adx_threshold: 25.0
    rsi_overbought: 70.0
    rsi_oversold: 30.0
    rsi_momentum_threshold: 50.0
```

## Performance Notes

- **Win Rate**: Typically 45-55% (trend-following characteristics)
- **Risk/Reward**: Targets 2:1+ due to riding trends
- **Best Performance**: Strong trending markets with clear momentum
- **Worst Performance**: Choppy, range-bound markets with weak trends

## Version History

### 0.1.0 (Current)

- Initial release
- Multi-timeframe momentum alignment
- Entry and exit signal generation
- ADX trend strength filter
- RSI momentum divergence detection

## Disclaimer

Strategies provided on Coinrule X are open-source and intended for systematic trading experimentation.
They do not constitute financial or investment advice.
Trading involves risk, and users are fully responsible for their configuration and capital allocation.
