import datetime as dt
from abc import ABC, abstractmethod
from tyche.position import Position
from tyche.broker import Broker


class Strategy(ABC):

    def prepare(self, symbol):
        pass

    @abstractmethod
    def update(self, current_date: dt.datetime, broker: Broker):
        """
        This method is called once for every day of the backtest.
        Currently, there are no niceties like being handled a list of actions taken by the market such as expiring
        options that are expiring - closing for cash if they are ITM. Only assignment is handled specially.\
        The method gets the current date, list of positions, current option Chain and corresponding stock Quote.
        The last item passed in is the Broker object where the tyche can open/close Positions.
        Buying power should also be passed in, but since that is a real-time accounting, the Broker also keeps track.
        :param current_date: Current date in the backtest. This method will only be called once with this date.
        :param statement: list of Positions that are still open. May include Positions expiring on the current date.
        :param option_chain:
        :param stock_quote:
        :param broker:
        :return:
        """
        pass

    def assignment(self, cnt_assigned_positions, symbol, current_date: dt.datetime, broker: Broker):
        """
        Default implementation is to close the assigned position at market price.
        :param cnt_assigned_positions:
        :param current_date:
        :param broker:
        :return:
        """
        p = Position(-cnt_assigned_positions, symbol, 'S', 0, current_date)
        broker.place_order([p])
