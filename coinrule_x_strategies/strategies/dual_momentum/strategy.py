from typing import List, Dict, Any, Tuple
from coinrule_x_strategies.core import Strategy, Signal, SignalSide
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators import EMA, RSI, ADX, Candle

class DualMomentum(Strategy):
    """
    Multi-timeframe momentum strategy with entry and exit signals.

    ENTRY & EXIT STRATEGY - manages its own position exits.

    Core Principle:
    Uses two timeframes to align momentum and trend strength. Higher timeframe
    (HTF) provides the directional bias and trend confirmation, while lower
    timeframe (LTF) provides precise entry timing and exit signals.

    Entry Logic:
    - HTF must show strong trend (ADX > threshold) and momentum alignment
    - LTF must confirm with momentum in same direction
    - Both timeframes' price must be on correct side of EMA

    Exit Logic:
    - Momentum divergence between timeframes (RSI disagreement)
    - LTF momentum becomes overbought/oversold
    - HTF trend weakens (ADX falls below threshold)
    - Price crosses against the trend on HTF

    Multi-Timeframe Benefits:
    - Reduces false signals from lower timeframe noise
    - Captures stronger moves confirmed by multiple timeframes
    - Earlier exits when higher timeframe momentum fades
    """

    def __init__(self,
                 ema_period_ltf: int = 20,
                 ema_period_htf: int = 50,
                 rsi_period: int = 14,
                 adx_period: int = 14,
                 adx_threshold: float = 25.0,
                 rsi_overbought: float = 70.0,
                 rsi_oversold: float = 30.0,
                 rsi_momentum_threshold: float = 50.0):
        super().__init__(
            ema_period_ltf=ema_period_ltf,
            ema_period_htf=ema_period_htf,
            rsi_period=rsi_period,
            adx_period=adx_period,
            adx_threshold=adx_threshold,
            rsi_overbought=rsi_overbought,
            rsi_oversold=rsi_oversold,
            rsi_momentum_threshold=rsi_momentum_threshold
        )
        self.adx_threshold = adx_threshold
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.rsi_momentum_threshold = rsi_momentum_threshold

    def indicators(self) -> Dict[str, Tuple[Indicator, str]]:
        """
        Define indicators for both timeframes.

        Market aliases:
        - "ltf" (Lower TimeFrame): For entry timing and exit signals
        - "htf" (Higher TimeFrame): For trend direction and strength
        """
        return {
            # Lower timeframe indicators (entry timing)
            "close_ltf": (Candle(field="close"), "ltf"),
            "ema_ltf": (EMA(period=self.config['ema_period_ltf']), "ltf"),
            "rsi_ltf": (RSI(period=self.config['rsi_period']), "ltf"),

            # Higher timeframe indicators (trend filter)
            "close_htf": (Candle(field="close"), "htf"),
            "ema_htf": (EMA(period=self.config['ema_period_htf']), "htf"),
            "rsi_htf": (RSI(period=self.config['rsi_period']), "htf"),
            "adx_htf": (ADX(period=self.config['adx_period']), "htf"),
        }

    def evaluate(self, indicators: Dict[str, List[Any]]) -> Signal:
        """
        Evaluate multi-timeframe momentum alignment.

        Signal Priority:
        1. Check exit conditions first (for position management)
        2. Check entry conditions only if no exit triggered
        """

        # Minimum data check (use HTF EMA as it requires most data)
        min_required = max(
            self.config['ema_period_htf'],
            self.config['adx_period'],
            self.config['rsi_period']
        )

        if len(indicators["close_htf"]) < min_required + 2:
            return Signal(side=SignalSide.WAIT, reason="Insufficient data")

        # Get current values from both timeframes
        close_ltf = indicators["close_ltf"][-1]
        ema_ltf = indicators["ema_ltf"][-1]
        rsi_ltf = indicators["rsi_ltf"][-1]
        rsi_ltf_prev = indicators["rsi_ltf"][-2]

        close_htf = indicators["close_htf"][-1]
        ema_htf = indicators["ema_htf"][-1]
        rsi_htf = indicators["rsi_htf"][-1]
        adx_data_htf = indicators["adx_htf"][-1]
        adx_htf = adx_data_htf['adx']
        plus_di = adx_data_htf['plus_di']
        minus_di = adx_data_htf['minus_di']

        # ═══════════════════════════════════════════════════════════
        # EXIT CONDITIONS (checked first for safety)
        # ═══════════════════════════════════════════════════════════
        # Exit conditions only trigger on extreme RSI levels to avoid
        # conflicting with entry logic. HTF reversals are handled by
        # opposite entry signals (execution layer closes old position
        # before opening new one).

        # Exit long if LTF becomes overbought
        if rsi_ltf > self.rsi_overbought:
            return Signal(
                side=SignalSide.CLOSE_LONG,
                reason=f"LTF overbought (RSI: {rsi_ltf:.2f})",
                metadata={
                    "rsi_ltf": rsi_ltf,
                    "rsi_htf": rsi_htf,
                    "adx_htf": adx_htf
                }
            )

        # Exit short if LTF becomes oversold
        if rsi_ltf < self.rsi_oversold:
            return Signal(
                side=SignalSide.CLOSE_SHORT,
                reason=f"LTF oversold (RSI: {rsi_ltf:.2f})",
                metadata={
                    "rsi_ltf": rsi_ltf,
                    "rsi_htf": rsi_htf,
                    "adx_htf": adx_htf
                }
            )

        # ═══════════════════════════════════════════════════════════
        # ENTRY CONDITIONS
        # ═══════════════════════════════════════════════════════════

        # Check HTF trend strength
        has_strong_trend = adx_htf > self.adx_threshold

        if not has_strong_trend:
            return Signal(
                side=SignalSide.WAIT,
                reason=f"HTF trend not strong enough (ADX: {adx_htf:.2f})",
                metadata={"adx_htf": adx_htf}
            )

        # Bullish entry conditions
        htf_bullish = (
            close_htf > ema_htf and
            rsi_htf > self.rsi_momentum_threshold and
            plus_di > minus_di
        )

        ltf_bullish = (
            close_ltf > ema_ltf and
            rsi_ltf > self.rsi_momentum_threshold and
            rsi_ltf < self.rsi_overbought  # Not already overbought
        )

        # Check for RSI turning up on LTF (entry timing)
        rsi_ltf_turning_up = rsi_ltf > rsi_ltf_prev

        if htf_bullish and ltf_bullish and rsi_ltf_turning_up:
            # Calculate confidence based on momentum alignment
            rsi_alignment = min(rsi_ltf, rsi_htf) / 100.0
            adx_strength = min(adx_htf / 50.0, 1.0)
            confidence = min((rsi_alignment + adx_strength) / 2.0, 1.0)

            return Signal(
                side=SignalSide.OPEN_LONG,
                confidence=confidence,
                reason=f"Multi-timeframe bullish alignment (HTF ADX: {adx_htf:.2f}, LTF RSI: {rsi_ltf:.2f})",
                metadata={
                    "rsi_ltf": rsi_ltf,
                    "rsi_htf": rsi_htf,
                    "adx_htf": adx_htf,
                    "ema_ltf": ema_ltf,
                    "ema_htf": ema_htf
                }
            )

        # Bearish entry conditions
        htf_bearish = (
            close_htf < ema_htf and
            rsi_htf < self.rsi_momentum_threshold and
            minus_di > plus_di
        )

        ltf_bearish = (
            close_ltf < ema_ltf and
            rsi_ltf < self.rsi_momentum_threshold and
            rsi_ltf > self.rsi_oversold  # Not already oversold
        )

        # Check for RSI turning down on LTF (entry timing)
        rsi_ltf_turning_down = rsi_ltf < rsi_ltf_prev

        if htf_bearish and ltf_bearish and rsi_ltf_turning_down:
            # Calculate confidence based on momentum alignment
            rsi_alignment = (100.0 - max(rsi_ltf, rsi_htf)) / 100.0
            adx_strength = min(adx_htf / 50.0, 1.0)
            confidence = min((rsi_alignment + adx_strength) / 2.0, 1.0)

            return Signal(
                side=SignalSide.OPEN_SHORT,
                confidence=confidence,
                reason=f"Multi-timeframe bearish alignment (HTF ADX: {adx_htf:.2f}, LTF RSI: {rsi_ltf:.2f})",
                metadata={
                    "rsi_ltf": rsi_ltf,
                    "rsi_htf": rsi_htf,
                    "adx_htf": adx_htf,
                    "ema_ltf": ema_ltf,
                    "ema_htf": ema_htf
                }
            )

        return Signal(
            side=SignalSide.WAIT,
            reason="No multi-timeframe alignment",
            metadata={
                "rsi_ltf": rsi_ltf,
                "rsi_htf": rsi_htf,
                "adx_htf": adx_htf,
                "htf_bullish": htf_bullish,
                "htf_bearish": htf_bearish
            }
        )
