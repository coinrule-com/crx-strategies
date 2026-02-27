import pytest
from coinrule_x_indicators import EMA, RSI, ATR, ADX, Candle
from coinrule_x_strategies.strategies.bounce_recovery.strategy import BounceRecovery
from coinrule_x_strategies.core import SignalSide

def test_bounce_recovery_indicators():
    strategy = BounceRecovery()
    reqs = strategy.indicators()
    
    assert isinstance(reqs["close"], Candle)
    assert reqs["close"].config["field"] == "close"
    assert isinstance(reqs["ema"], EMA)
    assert isinstance(reqs["rsi"], RSI)
    assert isinstance(reqs["atr"], ATR)
    assert isinstance(reqs["adx"], ADX)

def test_bounce_recovery_insufficient_data():
    strategy = BounceRecovery()
    # Provide minimal dummy data
    indicators = {
        "close": [100.0] * 5,
        "low": [99.0] * 5,
        "high": [101.0] * 5,
        "ema": [100.0] * 5,
        "rsi": [50.0] * 5,
        "atr": [1.0] * 5,
        "adx": [{"adx": 15.0}] * 5
    }
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.WAIT
    assert "Insufficient data" in signal.reason

def test_bounce_recovery_valid_entry():
    strategy = BounceRecovery(
        ema_period=50, 
        rsi_oversold=30, 
        rsi_recovery=35,
        atr_multiplier=1.5,
        adx_max=30
    )
    
    # Construct scenario:
    # 1. ADX Low (20)
    # 2. Price far below EMA (EMA=110, Close=100, ATR=2. Extension=10 > 2*1.5=3)
    # 3. RSI was oversold recently (25, 30, 36) -> Recovered to 36 > 35
    # 4. Lows stabilizing (98, 99)
    # 5. RSI Slope Positive (30 -> 36)
    
    N = 100
    indicators = {
        "close": [100.0] * (N-3) + [98.0, 99.0, 100.0],
        "low":   [99.0] * (N-3) + [97.0, 98.0, 99.0], # Last lows: 97, 98, 99 (Rising/Stabilizing)
        "high":  [101.0] * N,
        "ema":   [110.0] * N, # EMA well above price
        "rsi":   [50.0] * (N-3) + [25.0, 30.0, 36.0], # 25 (oversold), 30, 36 (recovered)
        "atr":   [2.0] * N,
        "adx":   [{"adx": 20.0}] * N
    }
    
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.OPEN_LONG
    assert "Bounce confirmed" in signal.reason

def test_bounce_recovery_trend_filter_rejection():
    # ADX too high
    strategy = BounceRecovery(adx_max=30)
    N = 100
    indicators = {
        "close": [100.0] * N,
        "low": [99.0] * N,
        "high": [101.0] * N,
        "ema": [110.0] * N,
        "rsi": [36.0] * N, # Recovered
        "atr": [2.0] * N,
        "adx": [{"adx": 40.0}] * N # Strong Trend -> Reject
    }
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.WAIT
    assert "Strong trend" in signal.reason

def test_bounce_recovery_no_oversold():
    # RSI Never went below 30
    strategy = BounceRecovery(rsi_oversold=30)
    N = 100
    indicators = {
        "close": [100.0] * N,
        "low": [99.0] * N,
        "high": [101.0] * N,
        "ema": [110.0] * N,
        "rsi": [35.0, 36.0, 37.0] * 35, # Always > 30
        "atr": [2.0] * N,
        "adx": [{"adx": 20.0}] * N
    }
    # Need to match list lengths roughly
    indicators["rsi"] = indicators["rsi"][:N]
    
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.WAIT
    assert "No recent oversold" in signal.reason

def test_bounce_recovery_new_lows_rejection():
    # Price making new lows - catching falling knife
    strategy = BounceRecovery()
    N = 100
    indicators = {
        "close": [100.0] * (N-3) + [95.0, 94.0, 93.0],
        "low":   [99.0] * (N-3) + [94.0, 93.0, 92.0], # Making new lows (93, 92)
        "high":  [101.0] * N,
        "ema":   [110.0] * N,
        "rsi":   [50.0] * (N-3) + [25.0, 30.0, 36.0], # RSI recovering divergence?
        "atr":   [2.0] * N,
        "adx":   [{"adx": 20.0}] * N
    }
    signal = strategy.evaluate(indicators)
    assert signal.side == SignalSide.WAIT
    assert "making new lows" in signal.reason
