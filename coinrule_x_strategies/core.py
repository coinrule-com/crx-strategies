from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from coinrule_x_indicators.core import CandleData, Indicator

class SignalSide(Enum):
    OPEN_LONG = "OPEN_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    WAIT = "WAIT"

@dataclass
class Signal:
    side: SignalSide
    confidence: float = 1.0
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PositionContext:
    """Current position state passed to strategy.evaluate().

    Provided by the execution engine from Redis — survives runner restarts.
    Strategies should use this instead of maintaining their own state.

    Attributes:
        side:        "LONG" or "SHORT"
        entry_price: Average entry price across all legs
        quantity:    Total position size
        legs:        Number of legs (1 = single entry, >1 = DCA/pyramiding)
        pnl_pct:     Unrealized P&L percentage at current price
    """
    side: str
    entry_price: float
    quantity: float
    legs: int = 1
    pnl_pct: Optional[float] = None

class Strategy(ABC):
    """Base class for all Coinrule X strategies."""

    def __init__(self, **kwargs):
        """Initialize strategy with configuration arguments."""
        self.config = kwargs

    @abstractmethod
    def indicators(self) -> Union[
        Dict[str, Indicator],  # Legacy: single-market
        Dict[str, Tuple[Indicator, str]]  # New: (indicator, market_label)
    ]:
        """
        Define indicators with optional market binding.

        Single-market (legacy):
            {"rsi": RSI(14)}

        Multi-market (new):
            {"rsi_timeframe_1": (RSI(14), "market_1"), "rsi_timeframe_2": (RSI(14), "market_2")}
        """
        pass

    @abstractmethod
    def evaluate(self, indicators: Dict[str, List[Any]], position: Optional[PositionContext] = None) -> Signal:
        """
        Evaluate market data and return a signal.

        Args:
            indicators: Dictionary where keys are aliases and values are lists of
                       historical values for the specific indicator instances
                       returned by indicators().
            position:  Current position state (None if no open position).
                       Provided by the engine from Redis — use this instead of
                       tracking state in instance variables (which breaks on restart).

        Returns:
            A Signal object.
        """
        pass
