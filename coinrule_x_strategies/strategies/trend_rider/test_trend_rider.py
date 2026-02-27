import pytest
from coinrule_x_indicators import EMA, RSI, ADX, Candle, Price
from coinrule_x_strategies.strategies.trend_rider.strategy import TrendRider
from coinrule_x_strategies.core import SignalSide

def test_trend_rider_indicators_declaration():
    strategy = TrendRider(ema_fast_period=20, ema_slow_period=50)
    reqs = strategy.indicators()
    
    assert isinstance(reqs["close"], Candle)
    assert reqs["close"].config["field"] == "close"
    assert isinstance(reqs["live_price"], Price)
    assert isinstance(reqs["ema_fast"], EMA)
    assert reqs["ema_fast"].config["period"] == 20
    assert isinstance(reqs["ema_slow"], EMA)
    assert reqs["ema_slow"].config["period"] == 50
    assert isinstance(reqs["rsi"], RSI)
    assert isinstance(reqs["adx"], ADX)

def test_trend_rider_insufficient_data():
    strategy = TrendRider(ema_slow_period=200)
    indicator_values = {
        "close": [100.0] * 10,
        "live_price": [100.0] * 10,
        "ema_fast": [100.0] * 10,
        "ema_slow": [100.0] * 10,
        "rsi": [50.0] * 10,
        "adx": [{"adx": 20.0, "plus_di": 10.0, "minus_di": 10.0}] * 10
    }
    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.WAIT
    assert "Insufficient data" in signal.reason

def test_trend_rider_bullish_signal():
    strategy = TrendRider(ema_fast_period=10, ema_slow_period=50, adx_threshold=25.0)
    indicator_values = {
        "close": [110.0] * 100,
        "live_price": [110.5] * 100,
        "ema_fast": [105.0] * 100,
        "ema_slow": [102.0] * 100,
        "rsi": [60.0] * 100,
        "adx": [{"adx": 30.0, "plus_di": 25.0, "minus_di": 15.0}] * 100
    }
    
    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.OPEN_LONG
    assert signal.confidence > 0

def test_trend_rider_bearish_signal():
    strategy = TrendRider(ema_fast_period=10, ema_slow_period=50, adx_threshold=25.0)
    indicator_values = {
        "close": [90.0] * 100,
        "live_price": [89.5] * 100,
        "ema_fast": [95.0] * 100,
        "ema_slow": [98.0] * 100,
        "rsi": [40.0] * 100,
        "adx": [{"adx": 30.0, "plus_di": 15.0, "minus_di": 25.0}] * 100
    }
    
    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.OPEN_SHORT
    assert signal.confidence > 0
