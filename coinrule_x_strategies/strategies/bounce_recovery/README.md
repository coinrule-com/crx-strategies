# Bounce Recovery

## Overview

**Bounce Recovery** focuses on identifying temporary price overextensions and entering positions when the market shows signs of stabilizing or reversing.

Unlike aggressive dip-buying strategies, **Bounce Recovery** incorporates volatility and trend context to avoid entering against strong momentum.

## Market Conditions

_Best suited for:_

- Range-bound markets
- Shallow pullbacks within broader trends
- Short-term oversold conditions

_Avoid during:_

- Strong directional breakdowns
- High-impact news events
- Panic-driven selloffs

## Core Logic

The strategy detects overextended price movements using:

- Momentum exhaustion signals
- Volatility thresholds
- Short-term trend stabilization

Entries occur only after confirmation that selling pressure is weakening, reducing the risk of catching a “falling knife”.

## Risk Profile

- **Style**: Mean reversion
- **Trade frequency**: Medium
- **Drawdowns**: Possible during strong directional moves
- **Risk handling**: Managed by Coinrule X execution layer

## Execution & Risk Management

**This strategy generates entry signals only**.

Position management (exits, stop-loss, take-profit, trailing, breakeven) is handled by Coinrule X’s execution layer, which applies a standardized and configurable risk framework across all strategies.

For details on execution, exits, and risk controls, see:
→ [Execution & Risk Management](../../../README.md#execution--risk-management)

## When NOT to use

- During strong bearish trends
- During sudden volatility spikes
- When momentum remains dominant

## Summary

**Bounce Recovery** is designed for pullbacks — and Coinrule X's risk engine ensures disciplined exits.
Risk control is core to the overall **Bounce Recovery** setup.

## Contributors

- [Ethical Daddy](https://github.com/ethical-daddy)

## Disclaimer

Strategies provided on Coinrule X are open-source and intended for systematic trading experimentation.
They do not constitute financial or investment advice.
Trading involves risk, and users are fully responsible for their configuration and capital allocation.
