import datetime as dt
import random
from strategy.strategy import Strategy
from tyche.position import Position
from tyche.broker import Broker


class BuyHold(Strategy):

    def __init__(self):
        super(BuyHold, self).__init__()
        self._symbol = None

    def prepare(self, symbol):
        self._symbol = symbol

    def update(self, current_date: dt.datetime, broker):
        """
        This method is called once for every day of the backtest.
        Currently, there are no niceties like being handled a list of actions taken by the market such as expiring
        options that are expiring - closing for cash if they are ITM. Only assignment is handled specially.\
        The method gets the current date, list of positions, current option Chain and corresponding stock Quote.
        The last item passed in is the Broker object where the tyche can open/close Positions.
        Buying power should also be passed in, but since that is a real-time accounting, the Broker also keeps track.
        :param current_date: Current date in the backtest. This method will only be called once with this date.
        :param statement: list of Positions that are still open. May include Positions expiring on the current date.
        :param broker:
        :return:
        """
        positions = broker.positions()
        if not positions:
            cash = broker.stock_buying_power()
            price = broker.stock_quote().get_current_price()
            cnt = int(cash/price)
            p = Position(cnt, self._symbol, 'S', 0.0)
            broker.place_order([p])
