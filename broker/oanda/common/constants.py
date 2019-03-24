from broker.base import AccountType

UNIT_RATIO = 100000


class OrderType(object):
    MARKET = "MARKET"  # A Market Order
    LIMIT = "LIMIT"  # A Limit Order
    STOP = "STOP"  # A Stop Order
    MARKET_IF_TOUCHED = "MARKET_IF_TOUCHED"  # A Market-if-touched Order
    TAKE_PROFIT = "TAKE_PROFIT"  # A Take Profit Order
    STOP_LOSS = "STOP_LOSS"  # A Stop Loss Order
    TRAILING_STOP_LOSS = "TRAILING_STOP_LOSS"  # A Trailing Stop Loss Order
    FIXED_PRICE = "FIXED_PRICE"  # A Fixed Price Order


class CancellableOrderType(object):
    LIMIT = 'LIMIT'  # A Limit Order",
    STOP = 'STOP'  # A Stop Order",
    MARKET_IF_TOUCHED = 'MARKET_IF_TOUCHED'  # A Market-if-touched Order",
    TAKE_PROFIT = 'TAKE_PROFIT'  # A Take Profit Order",
    STOP_LOSS = 'STOP_LOSS'  # A Stop Loss Order",
    TRAILING_STOP_LOSS = 'TRAILING_STOP_LOSS'  # A Trailing Stop Loss Order",


class OrderState(object):
    PENDING = 'PENDING'  # The Order is currently pending execution",
    FILLED = 'FILLED'  # The Order has been filled",
    TRIGGERED = 'TRIGGERED'  # The Order has been triggered",
    CANCELLED = 'CANCELLED'  # The Order has been cancelled",


class OrderStateFilter(object):
    PENDING = 'PENDING'  # The orders that are currently pending execution",
    FILLED = 'FILLED'  # The orders that have been filled",
    TRIGGERED = 'TRIGGERED'  # The orders that have been triggered",
    CANCELLED = 'CANCELLED'  # The orders that have been cancelled",
    ALL = 'ALL'  # The orders that are in any of the possible states: PENDING, FILLED, TRIGGERED, CANCELLED",


class TimeInForce(object):
    GTC = 'GTC'  # The Order is “Good unTil Cancelled”",
    GTD = 'GTD'  # The Order is “Good unTil Date” and will be cancelled at the provided time",
    GFD = 'GFD'  # The Order is “Good for Day” and will be cancelled at 5pm New York time",
    FOK = 'FOK'  # The Order must be immediately “Filled Or Killed”",
    IOC = 'IOC'  # The Order must be “Immediately partially filled Or Killed”",


class OrderPositionFill(object):
    OPEN_ONLY = 'OPEN_ONLY'  # When the Order is filled, only allow Positions to be opened or extended.",
    REDUCE_FIRST = 'REDUCE_FIRST'  # When the Order is filled, always fully reduce an existing Position before opening a new Position.",
    REDUCE_ONLY = 'REDUCE_ONLY'  # When the Order is filled, only reduce an existing Position.",
    DEFAULT = 'DEFAULT'  # When the Order is filled, use REDUCE_FIRST behaviour for non-client hedging Accounts, and OPEN_ONLY behaviour for client hedging Accounts."


class OrderTriggerCondition(object):
    DEFAULT = 'DEFAULT'  # Trigger an Order the “natural” way: compare its price to the ask for long Orders and bid for short Orders",
    INVERSE = 'INVERSE'  # Trigger an Order the opposite of the “natural” way: compare its price the bid for long Orders and ask for short Orders.",
    BID = 'BID'  # Trigger an Order by comparing its price to the bid regardless of whether it is long or short.",
    ASK = 'ASK'  # Trigger an Order by comparing its price to the ask regardless of whether it is long or short.",
    MID = 'MID'  # Trigger an Order by comparing its price to the midpoint regardless of whether it is long or short."


class TransactionName(object):
    """transaction name in order response"""
    orderCreateTransaction = 'orderCreateTransaction'
    longOrderCreateTransaction = 'longOrderCreateTransaction'
    shortOrderCreateTransaction = 'shortOrderCreateTransaction'
    orderFillTransaction = 'orderFillTransaction'
    longOrderFillTransaction = 'longOrderFillTransaction'
    shortOrderFillTransaction = 'shortOrderFillTransaction'
    orderCancelTransaction = 'orderCancelTransaction'
    longOrderCancelTransaction = 'longOrderCancelTransaction'
    shortOrderCancelTransaction = 'shortOrderCancelTransaction'
    orderReissueTransaction = 'orderReissueTransaction'
    orderRejectTransaction = 'orderRejectTransaction'
    orderReissueRejectTransaction = 'orderReissueRejectTransaction'
    replacingOrderCancelTransaction = 'replacingOrderCancelTransaction'

    @classmethod
    def all(cls):
        return [v for k, v in TransactionName.__dict__.items() if not k.startswith('_') and isinstance(v, str)]


class TransactionType(object):
    """type list of transaction object"""
    CREATE = 'CREATE'  # Account Create Transaction
    CLOSE = 'CLOSE'  # Account Close Transaction
    REOPEN = 'REOPEN'  # Account Reopen Transaction
    CLIENT_CONFIGURE = 'CLIENT_CONFIGURE'  # Client Configuration Transaction
    CLIENT_CONFIGURE_REJECT = 'CLIENT_CONFIGURE_REJECT'  # Client Configuration Reject Transaction
    TRANSFER_FUNDS = 'TRANSFER_FUNDS'  # Transfer Funds Transaction
    TRANSFER_FUNDS_REJECT = 'TRANSFER_FUNDS_REJECT'  # Transfer Funds Reject Transaction
    # ORDER
    MARKET_ORDER = 'MARKET_ORDER'  # Market Order Transaction
    MARKET_ORDER_REJECT = 'MARKET_ORDER_REJECT'  # Market Order Reject Transaction
    FIXED_PRICE_ORDER = 'FIXED_PRICE_ORDER'  # Fixed Price Order Transaction
    LIMIT_ORDER = 'LIMIT_ORDER'  # Limit Order Transaction
    LIMIT_ORDER_REJECT = 'LIMIT_ORDER_REJECT'  # Limit Order Reject Transaction
    STOP_ORDER = 'STOP_ORDER'  # Stop Order Transaction
    STOP_ORDER_REJECT = 'STOP_ORDER_REJECT'  # Stop Order Reject Transaction
    MARKET_IF_TOUCHED_ORDER = 'MARKET_IF_TOUCHED_ORDER'  # Market if Touched Order Transaction
    MARKET_IF_TOUCHED_ORDER_REJECT = 'MARKET_IF_TOUCHED_ORDER_REJECT'  # Market if Touched Order Reject Transaction
    TAKE_PROFIT_ORDER = 'TAKE_PROFIT_ORDER'  # Take Profit Order Transaction
    TAKE_PROFIT_ORDER_REJECT = 'TAKE_PROFIT_ORDER_REJECT'  # Take Profit Order Reject Transaction
    STOP_LOSS_ORDER = 'STOP_LOSS_ORDER'  # Stop Loss Order Transaction
    STOP_LOSS_ORDER_REJECT = 'STOP_LOSS_ORDER_REJECT'  # Stop Loss Order Reject Transaction
    TRAILING_STOP_LOSS_ORDER = 'TRAILING_STOP_LOSS_ORDER'  # Trailing Stop Loss Order Transaction
    TRAILING_STOP_LOSS_ORDER_REJECT = 'TRAILING_STOP_LOSS_ORDER_REJECT'  # Trailing Stop Loss Order Reject Transaction
    ORDER_FILL = 'ORDER_FILL'  # Order Fill Transaction
    ORDER_CANCEL = 'ORDER_CANCEL'  # Order Cancel Transaction
    ORDER_CANCEL_REJECT = 'ORDER_CANCEL_REJECT'  # Order Cancel Reject Transaction
    ORDER_CLIENT_EXTENSIONS_MODIFY = 'ORDER_CLIENT_EXTENSIONS_MODIFY'  # Order Client Extensions Modify Transaction
    ORDER_CLIENT_EXTENSIONS_MODIFY_REJECT = 'ORDER_CLIENT_EXTENSIONS_MODIFY_REJECT'  # Order Client Extensions Modify Reject Transaction
    # Trade
    TRADE_CLIENT_EXTENSIONS_MODIFY = 'TRADE_CLIENT_EXTENSIONS_MODIFY'  # Trade Client Extensions Modify Transaction
    TRADE_CLIENT_EXTENSIONS_MODIFY_REJECT = 'TRADE_CLIENT_EXTENSIONS_MODIFY_REJECT'  # Trade Client Extensions Modify Reject Transaction
    MARGIN_CALL_ENTER = 'MARGIN_CALL_ENTER'  # Margin Call Enter Transaction
    MARGIN_CALL_EXTEND = 'MARGIN_CALL_EXTEND'  # Margin Call Extend Transaction
    MARGIN_CALL_EXIT = 'MARGIN_CALL_EXIT'  # Margin Call Exit Transaction
    DELAYED_TRADE_CLOSURE = 'DELAYED_TRADE_CLOSURE'  # Delayed Trade Closure Transaction
    DAILY_FINANCING = 'DAILY_FINANCING'  # Daily Financing Transaction
    RESET_RESETTABLE_PL = 'RESET_RESETTABLE_PL'  # Reset Resettable PL Transaction


OANDA_ENVIRONMENTS = {
    "streaming": {
        AccountType.REAL: "stream-fxtrade.oanda.com",
        AccountType.DEMO: "stream-fxpractice.oanda.com",
        AccountType.SANDBOX: "stream-sandbox.oanda.com"
    },
    "api": {
        AccountType.REAL: "api-fxtrade.oanda.com",
        AccountType.DEMO: "api-fxpractice.oanda.com",
        AccountType.SANDBOX: "api-sandbox.oanda.com"
    }
}
