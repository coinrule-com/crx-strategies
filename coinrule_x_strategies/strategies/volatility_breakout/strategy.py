from typing import List, Dict, Any, Tuple
from coinrule_x_indicators.core import Indicator
from coinrule_x_indicators.indicators import DonchianChannels, BollingerBands, ADX, EMA, Candle
from coinrule_x_strategies.core import Strategy, Signal, SignalSide

class VolatilityBreakout(Strategy):
    """
    Volatility Breakout Strategy.
    
    Captures high-quality volatility expansion moves transitioning from low to high volatility.
    
    Logic:
    1. Compression: BB Bandwidth is low relative to recent history (lower quartile).
    2. Breakout: Close breaks above/below previous Donchian Channel High/Low.
    3. Expansion: BB Bandwidth is expanding.
    4. Trend Filter: Trade in direction of EMA 50.
    5. Quality: ADX confirms trend strength > threshold.
    """
    
    def __init__(self, 
                 donchian_period: int = 20,
                 bb_period: int = 20,
                 bb_std: float = 2.0,
                 ema_period: int = 50,
                 adx_period: int = 14,
                 adx_threshold: float = 20.0,
                 compression_lookback: int = 50,
                 compression_factor: float = 0.8):
        
        super().__init__(
            donchian_period=donchian_period,
            bb_period=bb_period,
            bb_std=bb_std,
            ema_period=ema_period,
            adx_period=adx_period,
            adx_threshold=adx_threshold,
            compression_lookback=compression_lookback,
            compression_factor=compression_factor
        )

    def indicators(self) -> Dict[str, Indicator]:
        return {
            "donchian": DonchianChannels(self.config["donchian_period"]),
            "bb": BollingerBands(self.config["bb_period"], self.config["bb_std"]),
            "ema": EMA(self.config["ema_period"]),
            "adx": ADX(self.config["adx_period"]),
            "candle": Candle()
        }

    def evaluate(self, indicators: Dict[str, List[Any]]) -> Signal:
        # Get history
        bb_history = indicators["bb"]
        donchian_history = indicators["donchian"]
        ema_history = indicators["ema"]
        adx_history = indicators["adx"]
        
        # Need at least lookback + 1 candles
        min_len = self.config["compression_lookback"] + 2
        if len(bb_history) < min_len:
            return Signal(SignalSide.WAIT, reason="Insufficient history")
            
        current_idx = -1
        prev_idx = -2
        
        # Current values
        close = indicators["candle"][current_idx].close
        bb = bb_history[current_idx]
        prev_bb = bb_history[prev_idx]
        
        donchian_prev = donchian_history[prev_idx] # Breakout vs previous channel
        ema = ema_history[current_idx]
        adx = adx_history[current_idx]
        
        # 1. Compression Detection
        # Calculate recent average bandwidth
        recent_bandwidths = [x["bandwidth"] for x in bb_history[-self.config["compression_lookback"]:-1]]
        avg_bandwidth = sum(recent_bandwidths) / len(recent_bandwidths)
        
        # Is current (or strictly previous) bandwidth compressed?
        # We check if *previous* bandwidth was compressed, to catch the expansion *now*.
        is_compressed = prev_bb["bandwidth"] < (avg_bandwidth * self.config["compression_factor"])
        
        # 2. Expansion Confirmation
        # Currently expanding relative to previous
        is_expanding = bb["bandwidth"] > prev_bb["bandwidth"]
        
        if not (is_compressed and is_expanding):
             # Try slightly looser logic: 
             # Maybe we are just emerging from compression.
             # Allow if we were compressed recently (within last 3 candles) AND expanding now.
             was_compressed_recently = any(b < (avg_bandwidth * self.config["compression_factor"]) 
                                           for b in recent_bandwidths[-3:])
             if not (was_compressed_recently and is_expanding):
                 return Signal(SignalSide.WAIT, reason="No volatility expansion from compression")

        # 3. Direction Filter
        trend_long = close > ema
        trend_short = close < ema
        
        # 4. ADX Filter
        strong_trend = adx > self.config["adx_threshold"]
        
        # 5. Breakout Trigger
        # Long: Close > Previous Donchian Upper
        breakout_long = close > donchian_prev["upper"]
        # Short: Close < Previous Donchian Lower
        breakout_short = close < donchian_prev["lower"]
        
        # Logic Composition
        if breakout_long and trend_long and strong_trend:
            return Signal(
                SignalSide.OPEN_LONG, 
                reason="Volatility Breakout LONG (Compressed -> Expanding, > Donchian Upper, > EMA)"
            )
            
        if breakout_short and trend_short and strong_trend:
            return Signal(
                SignalSide.OPEN_SHORT, 
                reason="Volatility Breakout SHORT (Compressed -> Expanding, < Donchian Lower, < EMA)"
            )
            
        return Signal(SignalSide.WAIT)
