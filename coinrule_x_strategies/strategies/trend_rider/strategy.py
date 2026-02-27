from typing import List, Dict, Any
from coinrule_x_strategies.core import Strategy, Signal, SignalSide
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators import EMA, RSI, ADX, Candle, Price

class TrendRider(Strategy):
    """
    A trend-following strategy that uses EMA for trend direction,
    RSI for momentum, and ADX for trend strength.
    
    ENTRY LOGIC ONLY - No exits, stops, or position sizing.
    """
    
    def __init__(self, 
                 ema_fast_period: int = 50, 
                 ema_slow_period: int = 200, 
                 rsi_period: int = 14, 
                 adx_period: int = 14,
                 adx_threshold: float = 25.0):
        super().__init__(
            ema_fast_period=ema_fast_period,
            ema_slow_period=ema_slow_period,
            rsi_period=rsi_period,
            adx_period=adx_period,
            adx_threshold=adx_threshold
        )
        self.adx_threshold = adx_threshold

    def indicators(self) -> Dict[str, Indicator]:
        return {
            # Use Candle indicator to get closed candle data
            "close": Candle(field="close"),
            # Use Price indicator if we wanted live price (demo purpose)
            "live_price": Price(),
            "ema_fast": EMA(period=self.config['ema_fast_period']),
            "ema_slow": EMA(period=self.config['ema_slow_period']),
            "rsi": RSI(period=self.config['rsi_period']),
            "adx": ADX(period=self.config['adx_period'])
        }

    def evaluate(self, indicators: Dict[str, List[Any]]) -> Signal:
        # Minimum data check
        if len(indicators["close"]) < self.config['ema_slow_period']:
            return Signal(side=SignalSide.WAIT, reason="Insufficient data")
            
        # Get latest values from closed candles
        last_close = indicators["close"][-1]
        
        # We could also use indicators["live_price"][-1] for real-time logic
        # but for this trend strategy we stick to closed ones.
        
        ema_fast_val = indicators["ema_fast"][-1]
        ema_slow_val = indicators["ema_slow"][-1]
        rsi_val = indicators["rsi"][-1]
        adx_data = indicators["adx"][-1]
        
        adx_val = adx_data['adx']
        plus_di = adx_data['plus_di']
        minus_di = adx_data['minus_di']
        
        # Bullish conditions
        is_bullish_trend = last_close > ema_fast_val > ema_slow_val
        is_strong_trend = adx_val > self.adx_threshold
        is_bullish_momentum = rsi_val > 50 and plus_di > minus_di
        
        # Bearish conditions
        is_bearish_trend = last_close < ema_fast_val < ema_slow_val
        is_bearish_momentum = rsi_val < 50 and minus_di > plus_di
        
        if is_bullish_trend and is_strong_trend and is_bullish_momentum:
            return Signal(
                side=SignalSide.OPEN_LONG, 
                confidence=min(adx_val / 50.0, 1.0),
                reason=f"Strong bullish trend (ADX: {adx_val:.2f}, RSI: {rsi_val:.2f})",
                metadata={"rsi": rsi_val, "adx": adx_val, "ema_fast": ema_fast_val}
            )
            
        if is_bearish_trend and is_strong_trend and is_bearish_momentum:
            return Signal(
                side=SignalSide.OPEN_SHORT,
                confidence=min(adx_val / 50.0, 1.0),
                reason=f"Strong bearish trend (ADX: {adx_val:.2f}, RSI: {rsi_val:.2f})",
                metadata={"rsi": rsi_val, "adx": adx_val, "ema_fast": ema_fast_val}
            )
            
        return Signal(side=SignalSide.WAIT, reason="No strong trend detected", metadata={
          "rsi": rsi_val,
          "adx": adx_val,
          "ema_fast": ema_fast_val,
          "ema_slow": ema_slow_val
        })
