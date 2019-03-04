def show(msg):
    '''
    Sample price handler. If on_price_update is registered for a symbol,
    it will update the symbol's values (stored in a symbol hash) with
    that price update.symbol hash.

    :return: none
    '''
    try:
        md = json.loads(msg)
        symbol = md["Symbol"]
        t = trader
        si = trader.symbol_info.get(symbol, {})
        p_up = dict(symbol_info=t.symbol_info[symbol], parent=t)
        t.symbols[symbol] = t.symbols.get(symbol, fxcm_rest_api
                                          .PriceUpdate(p_up,
                                                       symbol_info=si))
        trader.symbols[symbol].bid, trader.symbols[symbol].ask,\
            trader.symbols[symbol].high,\
            trader.symbols[symbol].low = md['Rates']
        trader.symbols[symbol].updated = md['Updated']
        print(t.symbols[symbol])
    except Exception as e:
        trader.logger.error("Can't handle price update: " + str(e))
