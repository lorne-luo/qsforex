import broker.oanda.common.view as common_view


# === POSITION ===

def position_side_formatter(side_name):
    """
    Create a formatter that extracts and formats the long or short side from a
    Position

    Args:
        side_name: "long" or "short" indicating which side of the position to
                   format
    """

    def f(p):
        """The formatting function for the long or short side"""

        side = getattr(p, side_name)

        if side is None:
            return ""
        if side.units == "0":
            return ""

        return "{} @ {}".format(side.units, side.averagePrice)

    return f


def print_positions_map(positions_map, open_only=True):
    """
    Print a map of Positions in table format.

    Args:
        positions: The map of instrument->Positions to print
        open_only: Flag that controls if only open Positions are displayed
    """

    print_positions(
        sorted(
            positions_map.values(),
            key=lambda p: p.instrument
        ),
        open_only
    )


def print_positions(positions, open_only=True):
    """
    Print a list of Positions in table format.

    Args:
        positions: The list of Positions to print
        open_only: Flag that controls if only open Positions are displayed
    """

    filtered_positions = [
        p for p in positions
        if not open_only or p.long.units != "0" or p.short.units != "0"
    ]

    if len(filtered_positions) == 0:
        return

    #
    # Print the Trades in a table with their Instrument, realized PL,
    # unrealized PL long postion summary and shor position summary
    #
    common_view.print_collection(
        "{} {}Positions".format(
            len(filtered_positions),
            "Open " if open_only else ""
        ),
        filtered_positions,
        [
            ("Instrument", lambda p: p.instrument),
            ("P/L", lambda p: p.pl),
            ("Unrealized P/L", lambda p: p.unrealizedPL),
            ("Long", position_side_formatter("long")),
            ("Short", position_side_formatter("short")),
        ]
    )

    print("")


# === ORDER === 

def print_orders_map(orders_map):
    """
    Print a map of Order Summaries in table format.

    Args:
        orders_map: The map of id->Order to print
    """

    print_orders(
        sorted(
            orders_map.values(),
            key=lambda o: o.id
        )
    )


def print_orders(orders):
    """
    Print a collection or Orders in table format.

    Args:
        orders: The list or Orders to print
    """

    #
    # Mapping from Order type to human-readable name
    #
    order_names = {
        "STOP": "Stop",
        "LIMIT": "Limit",
        "MARKET": "Market",
        "MARKET_IF_TOUCHED": "Entry",
        "ONE_CANCELS_ALL": "One Cancels All",
        "TAKE_PROFIT": "Take Profit",
        "STOP_LOSS": "Stop Loss",
        "TRAILING_STOP_LOSS": "Trailing Stop Loss"
    }

    #
    # Print the Orders in a table with their ID, type, state, and summary
    #
    common_view.print_collection(
        "{} Orders".format(len(orders)),
        orders,
        [
            ("ID", lambda o: o.id),
            ("Type", lambda o: order_names.get(o.type, o.type)),
            ("State", lambda o: o.state),
            ("Summary", lambda o: o.summary()),
        ]
    )

    print("")


def print_order_create_response_transactions(response):
    """
    Print out the transactions found in the order create response
    """

    common_view.print_response_entity(
        response, None,
        "Order Create",
        "orderCreateTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Long Order Create",
        "longOrderCreateTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Short Order Create",
        "shortOrderCreateTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Order Fill",
        "orderFillTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Long Order Fill",
        "longOrderFillTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Short Order Fill",
        "shortOrderFillTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Order Cancel",
        "orderCancelTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Long Order Cancel",
        "longOrderCancelTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Short Order Cancel",
        "shortOrderCancelTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Order Reissue",
        "orderReissueTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Order Reject",
        "orderRejectTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Order Reissue Reject",
        "orderReissueRejectTransaction"
    )

    common_view.print_response_entity(
        response, None,
        "Replacing Order Cancel",
        "replacingOrderCancelTransaction"
    )


# === TRADE ===


def print_trades_map(trades_map):
    """
    Print a map of Trade Summaries in table format.

    Args:
        orders_map: The map of id->Trade to print
    """

    print_trades(
        sorted(
            trades_map.values(),
            key=lambda t: t.id
        )
    )


def print_trades(trades):
    """
    Print a collection or Trades in table format.

    Args:
        trades: The list of Trades to print
    """

    #
    # Print the Trades in a table with their ID, state, summary, upl and pl
    #
    common_view.print_collection(
        "{} Trades".format(len(trades)),
        trades,
        [
            ("ID", lambda t: t.id),
            ("State", lambda t: t.state),
            ("Summary", lambda t: t.summary()),
            ("Unrealized P/L", lambda t: t.unrealizedPL),
            ("P/L", lambda t: t.realizedPL)
        ]
    )

    print("")
