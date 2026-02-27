import pytest
from coinrule_x_indicators import EMA, RSI, ADX, Candle
from coinrule_x_strategies.strategies.dual_momentum.strategy import DualMomentum
from coinrule_x_strategies.core import SignalSide

def test_dual_momentum_indicators_declaration():
    """Test that indicators are properly declared with market aliases."""
    strategy = DualMomentum(ema_period_ltf=20, ema_period_htf=50)
    reqs = strategy.indicators()

    # Check LTF indicators
    assert isinstance(reqs["close_ltf"][0], Candle)
    assert reqs["close_ltf"][0].config["field"] == "close"
    assert reqs["close_ltf"][1] == "ltf"

    assert isinstance(reqs["ema_ltf"][0], EMA)
    assert reqs["ema_ltf"][0].config["period"] == 20
    assert reqs["ema_ltf"][1] == "ltf"

    assert isinstance(reqs["rsi_ltf"][0], RSI)
    assert reqs["rsi_ltf"][1] == "ltf"

    # Check HTF indicators
    assert isinstance(reqs["close_htf"][0], Candle)
    assert reqs["close_htf"][1] == "htf"

    assert isinstance(reqs["ema_htf"][0], EMA)
    assert reqs["ema_htf"][0].config["period"] == 50
    assert reqs["ema_htf"][1] == "htf"

    assert isinstance(reqs["rsi_htf"][0], RSI)
    assert reqs["rsi_htf"][1] == "htf"

    assert isinstance(reqs["adx_htf"][0], ADX)
    assert reqs["adx_htf"][1] == "htf"

def test_dual_momentum_insufficient_data():
    """Test that strategy waits when insufficient data is available."""
    strategy = DualMomentum(ema_period_htf=50)
    indicator_values = {
        "close_ltf": [100.0] * 10,
        "ema_ltf": [100.0] * 10,
        "rsi_ltf": [50.0] * 10,
        "close_htf": [100.0] * 10,
        "ema_htf": [100.0] * 10,
        "rsi_htf": [50.0] * 10,
        "adx_htf": [{"adx": 25.0, "plus_di": 20.0, "minus_di": 15.0}] * 10
    }
    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.WAIT
    assert "Insufficient data" in signal.reason

def test_dual_momentum_bullish_entry():
    """Test bullish entry signal when both timeframes align."""
    strategy = DualMomentum(
        ema_period_ltf=20,
        ema_period_htf=50,
        adx_threshold=25.0,
        rsi_momentum_threshold=50.0,
        rsi_overbought=70.0
    )

    indicator_values = {
        "close_ltf": [110.0] * 100,
        "ema_ltf": [108.0] * 100,
        "rsi_ltf": [55.0] * 98 + [57.0, 60.0],  # RSI turning up (57 -> 60), not overbought
        "close_htf": [110.0] * 100,
        "ema_htf": [102.0] * 100,  # Price above HTF EMA (bullish)
        "rsi_htf": [65.0] * 100,
        "adx_htf": [{"adx": 30.0, "plus_di": 25.0, "minus_di": 15.0}] * 100
    }

    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.OPEN_LONG
    assert signal.confidence > 0
    assert "bullish alignment" in signal.reason.lower()

def test_dual_momentum_bearish_entry():
    """Test bearish entry signal when both timeframes align."""
    strategy = DualMomentum(
        ema_period_ltf=20,
        ema_period_htf=50,
        adx_threshold=25.0,
        rsi_momentum_threshold=50.0,
        rsi_oversold=30.0
    )

    indicator_values = {
        "close_ltf": [90.0] * 100,
        "ema_ltf": [92.0] * 100,
        "rsi_ltf": [45.0] * 98 + [43.0, 40.0],  # RSI turning down (43 -> 40), not oversold
        "close_htf": [90.0] * 100,
        "ema_htf": [98.0] * 100,  # Price below HTF EMA (bearish)
        "rsi_htf": [35.0] * 100,
        "adx_htf": [{"adx": 30.0, "plus_di": 15.0, "minus_di": 25.0}] * 100
    }

    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.OPEN_SHORT
    assert signal.confidence > 0
    assert "bearish alignment" in signal.reason.lower()

def test_dual_momentum_exit_long_overbought():
    """Test exit long signal when LTF RSI becomes overbought."""
    strategy = DualMomentum(rsi_overbought=70.0)

    indicator_values = {
        "close_ltf": [110.0] * 100,
        "ema_ltf": [108.0] * 100,
        "rsi_ltf": [75.0] * 100,  # Overbought
        "close_htf": [110.0] * 100,
        "ema_htf": [105.0] * 100,
        "rsi_htf": [65.0] * 100,
        "adx_htf": [{"adx": 30.0, "plus_di": 25.0, "minus_di": 15.0}] * 100
    }

    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.CLOSE_LONG
    assert "overbought" in signal.reason.lower()

def test_dual_momentum_exit_short_oversold():
    """Test exit short signal when LTF RSI becomes oversold."""
    strategy = DualMomentum(rsi_oversold=30.0, adx_threshold=25.0)

    indicator_values = {
        "close_ltf": [90.0] * 100,
        "ema_ltf": [92.0] * 100,
        "rsi_ltf": [25.0] * 100,  # Oversold
        "close_htf": [90.0] * 100,
        "ema_htf": [88.0] * 100,  # Price above HTF EMA (not triggering other exits)
        "rsi_htf": [35.0] * 100,
        "adx_htf": [{"adx": 30.0, "plus_di": 15.0, "minus_di": 25.0}] * 100
    }

    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.CLOSE_SHORT
    assert "oversold" in signal.reason.lower()


def test_dual_momentum_wait_weak_htf_trend_for_entry():
    """Test that strategy waits when HTF trend is too weak for new entries."""
    strategy = DualMomentum(
        adx_threshold=25.0,
        rsi_momentum_threshold=50.0,
        rsi_overbought=70.0
    )

    # Bullish setup but weak ADX - should wait
    indicator_values = {
        "close_ltf": [110.0] * 100,
        "ema_ltf": [108.0] * 100,
        "rsi_ltf": [55.0, 60.0] + [60.0] * 98,  # Turning up
        "close_htf": [110.0] * 100,
        "ema_htf": [102.0] * 100,
        "rsi_htf": [65.0] * 100,
        "adx_htf": [{"adx": 20.0, "plus_di": 20.0, "minus_di": 15.0}] * 100  # Weak trend
    }

    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.WAIT
    assert "not strong enough" in signal.reason.lower()


def test_dual_momentum_wait_no_alignment():
    """Test that strategy waits when timeframes don't align.

    Note: This test demonstrates misalignment where LTF and HTF disagree.
    Since exit conditions check HTF price vs EMA, we need both prices in
    neutral territory to avoid triggering exits and focus on entry logic.
    """
    strategy = DualMomentum(
        adx_threshold=25.0,
        rsi_momentum_threshold=50.0,
        rsi_overbought=70.0,
        rsi_oversold=30.0
    )

    # HTF and LTF conditions don't align - should wait
    # HTF: neutral/ranging (price near EMA), LTF bearish
    indicator_values = {
        "close_ltf": [90.0] * 100,  # LTF bearish
        "ema_ltf": [92.0] * 100,
        "rsi_ltf": [45.0, 40.0] + [40.0] * 98,
        "close_htf": [105.0] * 100,  # HTF neutral (at EMA)
        "ema_htf": [105.0] * 100,
        "rsi_htf": [50.0] * 100,  # Neutral momentum
        "adx_htf": [{"adx": 30.0, "plus_di": 20.0, "minus_di": 20.0}] * 100  # No clear direction
    }

    signal = strategy.evaluate(indicator_values)
    assert signal.side == SignalSide.WAIT
    assert "no multi-timeframe alignment" in signal.reason.lower()
