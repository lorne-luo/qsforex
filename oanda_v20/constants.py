from enum import Enum


class OrderType(Enum):
    MARKET = "MARKET"  # A Market Order
    LIMIT = "LIMIT"  # A Limit Order
    STOP = "STOP"  # A Stop Order
    MARKET_IF_TOUCHED = "MARKET_IF_TOUCHED"  # A Market-if-touched Order
    TAKE_PROFIT = "TAKE_PROFIT"  # A Take Profit Order
    STOP_LOSS = "STOP_LOSS"  # A Stop Loss Order
    TRAILING_STOP_LOSS = "TRAILING_STOP_LOSS"  # A Trailing Stop Loss Order
    FIXED_PRICE = "FIXED_PRICE"  # A Fixed Price Order


class CancellableOrderType(Enum):
    LIMIT = 'LIMIT'  # A Limit Order",
    STOP = 'STOP'  # A Stop Order",
    MARKET_IF_TOUCHED = 'MARKET_IF_TOUCHED'  # A Market-if-touched Order",
    TAKE_PROFIT = 'TAKE_PROFIT'  # A Take Profit Order",
    STOP_LOSS = 'STOP_LOSS'  # A Stop Loss Order",
    TRAILING_STOP_LOSS = 'TRAILING_STOP_LOSS'  # A Trailing Stop Loss Order",


class OrderState(Enum):
    PENDING = 'PENDING'  # The Order is currently pending execution",
    FILLED = 'FILLED'  # The Order has been filled",
    TRIGGERED = 'TRIGGERED'  # The Order has been triggered",
    CANCELLED = 'CANCELLED'  # The Order has been cancelled",


class OrderStateFilter(Enum):
    PENDING = 'PENDING'  # The orders that are currently pending execution",
    FILLED = 'FILLED'  # The orders that have been filled",
    TRIGGERED = 'TRIGGERED'  # The orders that have been triggered",
    CANCELLED = 'CANCELLED'  # The orders that have been cancelled",
    ALL = 'ALL'  # The orders that are in any of the possible states: PENDING, FILLED, TRIGGERED, CANCELLED",


class TimeInForce(Enum):
    GTC = 'GTC'  # The Order is “Good unTil Cancelled”",
    GTD = 'GTD'  # The Order is “Good unTil Date” and will be cancelled at the provided time",
    GFD = 'GFD'  # The Order is “Good for Day” and will be cancelled at 5pm New York time",
    FOK = 'FOK'  # The Order must be immediately “Filled Or Killed”",
    IOC = 'IOC'  # The Order must be “Immediately partially filled Or Killed”",


class OrderPositionFill(Enum):
    OPEN_ONLY = 'OPEN_ONLY'  # When the Order is filled, only allow Positions to be opened or extended.",
    REDUCE_FIRST = 'REDUCE_FIRST'  # When the Order is filled, always fully reduce an existing Position before opening a new Position.",
    REDUCE_ONLY = 'REDUCE_ONLY'  # When the Order is filled, only reduce an existing Position.",
    DEFAULT = 'DEFAULT'  # When the Order is filled, use REDUCE_FIRST behaviour for non-client hedging Accounts, and OPEN_ONLY behaviour for client hedging Accounts."


class OrderTriggerCondition(Enum):
    DEFAULT = 'DEFAULT'  # Trigger an Order the “natural” way: compare its price to the ask for long Orders and bid for short Orders",
    INVERSE = 'INVERSE'  # Trigger an Order the opposite of the “natural” way: compare its price the bid for long Orders and ask for short Orders.",
    BID = 'BID'  # Trigger an Order by comparing its price to the bid regardless of whether it is long or short.",
    ASK = 'ASK'  # Trigger an Order by comparing its price to the ask regardless of whether it is long or short.",
    MID = 'MID'  # Trigger an Order by comparing its price to the midpoint regardless of whether it is long or short."
