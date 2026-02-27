import pytest
from coinrule_x_indicators import EMA, ADX, Candle, DonchianChannels, BollingerBands
from coinrule_x_indicators.indicators import Candle as CandleIndicator
from coinrule_x_strategies.strategies.volatility_breakout.strategy import VolatilityBreakout
from coinrule_x_strategies.core import SignalSide

# Mock classes to simplify data creation
class MockCandle:
    def __init__(self, close):
        self.close = close

def test_vbo_indicators():
    strategy = VolatilityBreakout()
    reqs = strategy.indicators()
    
    assert isinstance(reqs["donchian"], DonchianChannels)
    assert isinstance(reqs["bb"], BollingerBands)
    assert isinstance(reqs["ema"], EMA)
    assert isinstance(reqs["adx"], ADX)
    assert isinstance(reqs["candle"], CandleIndicator)

def test_vbo_insufficient_data():
    strategy = VolatilityBreakout(compression_lookback=20)
    # Provide just 5 candles
    indicators = {
        "bb": [{"bandwidth": 0.1}] * 5,
        "donchian": [{"upper": 100, "lower": 90}] * 5,
        "ema": [100.0] * 5,
        "adx": [25.0] * 5,
        "candle": [MockCandle(100.0)] * 5
    }
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.WAIT
    assert "Insufficient history" in signal.reason

def test_vbo_long_breakout():
    lookback = 50
    strategy = VolatilityBreakout(
        compression_lookback=lookback,
        compression_factor=0.8,
        adx_threshold=20
    )
    
    N = lookback + 10
    
    # Setup Compression Context
    # Average bandwidth = 0.1
    # Previous bandwidth = 0.05 (Compressed: 0.05 < 0.1 * 0.8)
    # Current bandwidth = 0.06 (Expanding: 0.06 > 0.05)
    
    bb_history = [{"bandwidth": 0.1}] * (N-2) + [{"bandwidth": 0.05}, {"bandwidth": 0.06}]
    
    # Setup Breakout Context
    # Previous Donchian Upper = 100
    # Current Close = 101 (Breakout)
    donchian_history = [{"upper": 100.0, "lower": 90.0}] * N
    
    # Setup Trend Context
    # EMA = 95 (Uptrend: Close 101 > 95)
    ema_history = [95.0] * N
    
    # Setup ADX
    # ADX = 25 (Strong: 25 > 20)
    adx_history = [25.0] * N
    
    # Candles
    candle_history = [MockCandle(100.0)] * (N-1) + [MockCandle(101.0)]
    
    indicators = {
        "bb": bb_history,
        "donchian": donchian_history,
        "ema": ema_history,
        "adx": adx_history,
        "candle": candle_history
    }
    
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.OPEN_LONG
    assert "Volatility Breakout LONG" in signal.reason

def test_vbo_short_breakout():
    lookback = 50
    strategy = VolatilityBreakout(compression_lookback=lookback)
    N = lookback + 10
    
    # Compression + Expansion
    bb_history = [{"bandwidth": 0.1}] * (N-2) + [{"bandwidth": 0.05}, {"bandwidth": 0.06}]
    
    # Breakout Lower
    # Prev Donchian Lower = 90
    # Close = 89
    donchian_history = [{"upper": 100.0, "lower": 90.0}] * N
    
    # Downtrend: Close < EMA
    ema_history = [95.0] * N # Close 89 < 95
    
    adx_history = [30.0] * N
    
    candle_history = [MockCandle(92.0)] * (N-1) + [MockCandle(89.0)]
    
    indicators = {
        "bb": bb_history,
        "donchian": donchian_history,
        "ema": ema_history,
        "adx": adx_history,
        "candle": candle_history
    }
    
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.OPEN_SHORT
    assert "Volatility Breakout SHORT" in signal.reason

def test_vbo_no_compression():
    lookback = 50
    strategy = VolatilityBreakout(compression_lookback=lookback, compression_factor=0.8)
    N = lookback + 10
    
    # Avg Bandwidth ~ 0.1
    # Prev Bandwidth = 0.09 (Not compressed: 0.09 > 0.1 * 0.8 = 0.08)
    bb_history = [{"bandwidth": 0.1}] * (N-2) + [{"bandwidth": 0.09}, {"bandwidth": 0.10}]
    
    # Valid Breakout otherwise
    donchian_history = [{"upper": 100.0, "lower": 90.0}] * N
    ema_history = [95.0] * N
    adx_history = [25.0] * N
    candle_history = [MockCandle(101.0)] * N
    
    indicators = {
        "bb": bb_history,
        "donchian": donchian_history,
        "ema": ema_history,
        "adx": adx_history,
        "candle": candle_history
    }
    
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.WAIT
    assert "No volatility expansion" in signal.reason # Or compression failure logic
