# Trend Rider

## Overview

**Follow the Trend** is a systematic trend-following strategy built for markets with clear directional bias.
It combines multiple indicators to confirm trend strength, momentum, and market structure before entering a position.

The strategy is intentionally conservative in ranging or low-volatility environments and performs best during sustained trends.

## Market Conditions

_Best suited for:_

- Strong trending markets
- High momentum phases
- Directional expansions

_Avoid during:_

- Sideways / choppy price action
- Low volatility consolidation
- Unclear market structure

## Core Logic

**Trend Rider** identifies sustained directional moves by combining trend, momentum, and strength confirmation.

The strategy operates in three layers:

1. Trend Direction (EMA Crossover)

   - A fast and slow Exponential Moving Average (EMA) crossover defines the primary market direction.
   - Long positions are considered only when the fast EMA is above the slow EMA, and short positions only when the fast EMA is below the slow EMA.

2. Momentum Confirmation (RSI)

   - Relative Strength Index (RSI) is used to confirm momentum in the direction of the trend.
   - Trades are entered only when RSI supports continuation rather than exhaustion, helping avoid late or overextended entries.

3. Trend Strength Filter (ADX)
   - Average Directional Index (ADX) acts as a trend quality filter.
   - The strategy avoids trades when ADX indicates weak or non-directional market conditions, reducing exposure during choppy or ranging phases.

A position is opened only when all three components align, ensuring that trades are taken in strong, momentum-supported trends rather than random price movement.

### Why This Works

- EMA crossover defines direction, not timing alone
- RSI filters out weak momentum and overbought/oversold traps
- ADX prevents trading in low-quality, sideways markets

This layered confirmation helps Trend Rider stay patient during noise and participate only in meaningful market moves.

## Risk Profile

- **Style**: Trend-following
- **Trade frequency**: Low to medium
- **Drawdowns**: Can occur during trend reversals or range-bound markets
- **Risk handling**: Managed by Coinrule X execution layer

## Execution & Risk Management

**This strategy generates entry signals only**.

Position management (exits, stop-loss, take-profit, trailing, breakeven) is handled by Coinrule X’s execution layer, which applies a standardized and configurable risk framework across all strategies.

For details on execution, exits, and risk controls, see:
→ [Execution & Risk Management](../../../README.md#execution--risk-management)

## When NOT to use

- During range-bound markets
- Around low-liquidity periods
- When volatility is extremely compressed

## Summary

**Follow the Trend** is designed to ride sustained moves — not to predict tops or bottoms.
Patience and discipline are key.

## Contributors

- [Ethical Daddy](https://github.com/ethical-daddy)

## Disclaimer

Strategies provided on Coinrule X are open-source and intended for systematic trading experimentation.
They do not constitute financial or investment advice.
Trading involves risk, and users are fully responsible for their configuration and capital allocation.
