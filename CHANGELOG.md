# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-03-27

### Added

- **PositionContext**: New dataclass passed to `Strategy.evaluate()` providing current position state (side, entry_price, quantity, legs, pnl_pct). Sourced from the execution engine via persistent storage — survives runner restarts.
- **Updated `evaluate()` signature**: `evaluate(self, indicators, position=None)` — strategies receive position context directly instead of tracking state in instance variables (which breaks on restart).

## [1.0.0] - 2026-01-06

### Added

- **Initial Release**: Core strategy framework with `Strategy`, `Signal`, and `SignalSide`.
- **Registry System**: `registry.yaml` support for strategy discovery.
- **Strategies**:
  - Trend Rider
  - Bounce Recovery
  - Volatility Breakout
- **Validation**: Added `coinrule_x-validate-strategies` CLI tool for registry validation.
- **CI/CD**: GitHub Actions workflow for validation, testing, and automated PyPI release.
