def get_strategy(data):
    def get_strategy_1(data, params):
        close = data.close
        w_1 = 1 if close.sma(params[1]).last > close.sma(params[0]).last else -1
        w_2 = 1 if close.ema(params[2]).last > close.ema(params[3]).last else 0
        return w_1 * w_2

    def get_strategy_3(data, params):
        open = data.open
        for_shift = open.roc(params[4])
        f_1 = for_shift[-params[0]] < for_shift[-params[1]]
        f_2 = for_shift[-params[2]] > for_shift[-params[3]]
        return 1 if f_1 * f_2 else 0

    def get_strategy_6(data, params):
        open = data.open
        for_shift = open.rsi(params[4])
        f_1 = for_shift[-params[0]] < for_shift[-params[1]]
        f_2 = for_shift[-params[2]] > for_shift[-params[3]]
        return 1 if f_1 * f_2 else 0

    ## the main, private part of the algorithm

    if r >= 1:
        return 1
    if r < 0:
        return -1

    return 0


@enable_margin_trading()
def initialize(state):
    state.previous_trend = 0


@schedule(interval="1d", symbol="BTCUSDT", window_size=200)
def handler(state, data):
    try:
        trend = get_strategy(data)
    except:
        return

    print(trend)

    portfolio = query_portfolio()
    balance_quoted = portfolio.excess_liquidity_quoted
    buy_value = float(balance_quoted) * 1.00
    sel_value = float(balance_quoted) * 0.02

    position = query_open_position_by_symbol(data.symbol, include_dust=False)
    has_position = position is not None

    if trend == 0 and has_position:
        close_position(data.symbol)

    if trend == 1 and not has_position:
        order_market_value(symbol=data.symbol, value=buy_value)

    if trend == -1 and not has_position:
        margin_order_market_value(symbol=data.symbol, value=sel_value,
                                  side_effect=OrderMarginSideEffect.AutoDetermine)

    if trend != 0 and has_position:

        is_trend_changed = state.previous_trend != trend

        if is_trend_changed and trend == 1:
            with OrderScope.sequential(fail_on_error=False, wait_for_entire_fill=False):
                close_position(data.symbol)
                order_market_value(symbol=data.symbol, value=buy_value)

        if is_trend_changed and trend == -1:
            with OrderScope.sequential(fail_on_error=False, wait_for_entire_fill=False):
                close_position(data.symbol)
                margin_order_market_value(symbol=data.symbol, value=sel_value,
                                          side_effect=OrderMarginSideEffect.AutoDetermine)

    state.previous_trend = trend
