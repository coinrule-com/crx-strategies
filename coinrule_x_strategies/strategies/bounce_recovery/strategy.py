from typing import List, Dict, Any
from coinrule_x_strategies.core import Strategy, Signal, SignalSide
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators import EMA, RSI, ATR, ADX, Candle

class BounceRecovery(Strategy):
    """
    Mean-reversion strategy designed to capture controlled pullbacks.
    
    ENTRY LOGIC ONLY - No exits, stops, or position sizing.
    
    Core Principle:
    Enter only when price is overextended in a non-trending environment,
    and momentum shows early signs of reversal.
    
    Three-Layer Filter:
    1. Market Context: Confirm we're not in a strong trend (ADX filter)
    2. Overextension: Detect temporary price dislocation (RSI + ATR)
    3. Bounce Confirmation: Require momentum stabilization before entry
    
    Failure Modes:
    - Will underperform during strong directional trends
    - May miss early entries in favor of confirmation
    - Requires volatility expansion to trigger overextension detection
    """
    
    def __init__(self, 
                 ema_period: int = 50,
                 rsi_period: int = 14,
                 rsi_oversold: float = 30.0,
                 rsi_recovery: float = 35.0,
                 atr_period: int = 14,
                 atr_multiplier: float = 1.5,
                 adx_period: int = 14,
                 adx_max: float = 30.0):
        super().__init__(
            ema_period=ema_period,
            rsi_period=rsi_period,
            rsi_oversold=rsi_oversold,
            rsi_recovery=rsi_recovery,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            adx_period=adx_period,
            adx_max=adx_max
        )
        self.rsi_oversold = rsi_oversold
        self.rsi_recovery = rsi_recovery
        self.atr_multiplier = atr_multiplier
        self.adx_max = adx_max

    def indicators(self) -> Dict[str, Indicator]:
        return {
            # Price structure
            "close": Candle(field="close"),
            "low": Candle(field="low"),
            "high": Candle(field="high"),
            
            # Trend context filter
            "ema": EMA(period=self.config['ema_period']),
            "adx": ADX(period=self.config['adx_period']),
            
            # Overextension detection
            "rsi": RSI(period=self.config['rsi_period']),
            "atr": ATR(period=self.config['atr_period'])
        }

    def evaluate(self, indicators: Dict[str, List[Any]]) -> Signal:
        """
        Signal Generation Logic:
        
        LAYER 1: Market Context Filter
        - ADX must be below threshold (not in strong trend)
        - Price must be below EMA (confirming pullback structure)
        
        LAYER 2: Overextension Detection
        - RSI must have been oversold recently (within last 3 bars)
        - Price must be extended below EMA by at least ATR threshold
        
        LAYER 3: Bounce Confirmation
        - RSI must be recovering (above recovery threshold)
        - Current candle must not be making new lows (stabilization)
        - Momentum must be turning (RSI slope positive)
        
        Entry triggers ONLY when all three layers align.
        """
        
        # Minimum data check
        min_required = max(self.config['ema_period'], self.config['adx_period'], 
                          self.config['rsi_period'], self.config['atr_period']) + 5
        if len(indicators["close"]) < min_required:
            return Signal(side=SignalSide.WAIT, reason="Insufficient data")
        
        # Current values
        close = indicators["close"][-1]
        low = indicators["low"][-1]
        prev_low = indicators["low"][-2]
        
        ema_val = indicators["ema"][-1]
        rsi_current = indicators["rsi"][-1]
        rsi_prev = indicators["rsi"][-2]
        rsi_history = indicators["rsi"][-3:]  # Last 3 bars
        
        adx_data = indicators["adx"][-1]
        adx_val = adx_data['adx']
        
        atr_val = indicators["atr"][-1]
        
        # ═══════════════════════════════════════════════════════════
        # LAYER 1: MARKET CONTEXT FILTER
        # ═══════════════════════════════════════════════════════════
        
        # Reject if in strong trend
        if adx_val > self.adx_max:
            return Signal(
                side=SignalSide.WAIT, 
                reason=f"Strong trend detected (ADX: {adx_val:.1f} > {self.adx_max})",
                metadata={"adx": adx_val, "rsi": rsi_current}
            )
        
        # Require pullback structure (price below EMA)
        if close > ema_val:
            return Signal(
                side=SignalSide.WAIT,
                reason="Price above EMA - no pullback structure",
                metadata={"close": close, "ema": ema_val, "adx": adx_val}
            )
        
        # ═══════════════════════════════════════════════════════════
        # LAYER 2: OVEREXTENSION DETECTION
        # ═══════════════════════════════════════════════════════════
        
        # Check if RSI was oversold recently (within last 3 bars)
        was_oversold = any(rsi < self.rsi_oversold for rsi in rsi_history)
        
        if not was_oversold:
            return Signal(
                side=SignalSide.WAIT,
                reason="No recent oversold condition",
                metadata={"rsi": rsi_current, "adx": adx_val}
            )
        
        # Require meaningful distance from EMA (volatility-adjusted)
        distance_from_ema = ema_val - close
        min_extension = atr_val * self.atr_multiplier
        
        if distance_from_ema < min_extension:
            return Signal(
                side=SignalSide.WAIT,
                reason=f"Insufficient overextension ({distance_from_ema:.2f} < {min_extension:.2f})",
                metadata={"distance": distance_from_ema, "threshold": min_extension}
            )
        
        # ═══════════════════════════════════════════════════════════
        # LAYER 3: BOUNCE CONFIRMATION
        # ═══════════════════════════════════════════════════════════
        
        # RSI must be recovering (above recovery threshold)
        if rsi_current < self.rsi_recovery:
            return Signal(
                side=SignalSide.WAIT,
                reason=f"RSI not yet recovering ({rsi_current:.1f} < {self.rsi_recovery})",
                metadata={"rsi": rsi_current, "adx": adx_val}
            )
        
        # RSI must be turning upward (momentum reversal)
        rsi_slope = rsi_current - rsi_prev
        if rsi_slope <= 0:
            return Signal(
                side=SignalSide.WAIT,
                reason="RSI not turning upward",
                metadata={"rsi": rsi_current, "rsi_slope": rsi_slope}
            )
        
        # Price must not be making new lows (stabilization check)
        if low < prev_low:
            return Signal(
                side=SignalSide.WAIT,
                reason="Price still making new lows - no stabilization",
                metadata={"low": low, "prev_low": prev_low}
            )
        
        # ═══════════════════════════════════════════════════════════
        # ENTRY SIGNAL
        # ═══════════════════════════════════════════════════════════
        
        # Calculate confidence based on:
        # - How far RSI has recovered from oversold
        # - Strength of RSI momentum turn
        recovery_strength = (rsi_current - self.rsi_oversold) / (100 - self.rsi_oversold)
        momentum_strength = min(rsi_slope / 10.0, 1.0)  # Normalize slope
        confidence = min((recovery_strength + momentum_strength) / 2.0, 1.0)
        
        return Signal(
            side=SignalSide.OPEN_LONG,
            confidence=confidence,
            reason=f"Bounce confirmed: RSI recovery {rsi_current:.1f}, slope {rsi_slope:.1f}",
            metadata={
                "rsi": rsi_current,
                "rsi_slope": rsi_slope,
                "adx": adx_val,
                "distance_from_ema": distance_from_ema,
                "atr": atr_val,
                "ema": ema_val
            }
        )
