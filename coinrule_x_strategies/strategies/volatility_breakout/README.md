# Volatility Breakout (VBO) Strategy

## Overview

**Volatility Breakout (VBO)** is a systematic strategy designed to capture high-quality volatility expansions in perpetual futures markets. It profits from "regime shifts" where the market transitions from a low-volatility compression phase into specific directional momentum.

It avoids "falling knives" and choppy markets by strictly requiring:

1.  **Compression**: Prior volatility must be low.
2.  **Breakout**: Price must break a significant recent range (Donchian Channel).
3.  **Expansion**: Volatility must be visibly expanding.
4.  **Trend Alignment**: Trades are only taken in the direction of the dominant trend.

**Risk Profile**: Moderate/High (Trend Following).
**Best Market Condition**: Explosive moves after consolidation.
**Worst Market Condition**: Range-bound chop with fake breakouts.

---

## Logic & Indicators

### Indicators Used

| Indicator | Period | Purpose |
|Dist |---|---|
| **Donchian Channels** | 20 | Identifies key support/resistance levels for breakout triggers. |
| **Bollinger Bands** | 20, 2.0 | Measures volatility compression and expansion via Bandwidth. |
| **EMA** | 50 | Determines the major trend direction (Filter). |
| **ADX** | 14 | Measures trend strength (Filter). |

### Signal Generation Steps

#### 1. Compression Phase (The Setup)

The strategy first looks for a "squeeze".

- **Condition**: `Bandwidth` < `(Average Bandwidth over last 50 candles) * 0.8`.
- This ensures we are entering from a quiet period, giving the move potential energy.

#### 2. Volatility Expansion (The Trigger Context)

- **Condition**: `Current Bandwidth` > `Previous Bandwidth`.
- Volatility must be waking up. We don't trade dead markets.

#### 3. Breakout Trigger (The Entry)

- **Long**: `Close` > `Previous 20-period Donchian Upper`.
- **Short**: `Close` < `Previous 20-period Donchian Lower`.
- This confirms price is engaging new highs/lows.

#### 4. Trend Filters (The Protection)

- **Trend Align**: Price must be > EMA 50 (for Long) or < EMA 50 (for Short).
- **Trend Strength**: ADX must be > 20 (avoiding completely trendless chop).

---

## Configuration

| Parameter              | Default | Description                                                   |
| ---------------------- | ------- | ------------------------------------------------------------- |
| `donchian_period`      | 20      | Lookback for breakout channel.                                |
| `bb_period`            | 20      | Bollinger Band period for volatility.                         |
| `ema_period`           | 50      | Trend filter lookback.                                        |
| `adx_threshold`        | 20      | Minimum trend strength required.                              |
| `compression_lookback` | 50      | Baseline lookback for average volatility.                     |
| `compression_factor`   | 0.8     | Threshold for identifying "low" volatility (relative to avg). |

## When It Does NOT Trade

- **High Volatility**: If the market is already wild (Bandwidth > Average), it waits.
- **Counter-Trend**: It will never short above the EMA or long below it.
- **Weak Trends**: If ADX < 20, it stays flat.

---

## Execution & Risk Management

**This strategy generates entry signals only**.

Position management (exits, stop-loss, take-profit, trailing, breakeven) is handled by Coinrule X’s execution layer, which applies a standardized and configurable risk framework across all strategies.

For details on execution, exits, and risk controls, see:
→ [Execution & Risk Management](../../../README.md#execution--risk-management)

## Contributors

- [Ethical Daddy](https://github.com/ethical-daddy)

## Disclaimer

Strategies provided on Coinrule X are open-source and intended for systematic trading experimentation.
They do not constitute financial or investment advice.
Trading involves risk, and users are fully responsible for their configuration and capital allocation.
