import datetime as dt
from tyche.chain import Chain
from tyche.quote import Quote
from tyche.broker import Broker


option_path = '../option_history/'
quote_path = '../quote_history/'

"""
Creates the Broker, Strategy and executes the sim loop for a single backtest.
Can re-use the Broker (avoid chain load times) by calling broker.reset()  (or does the chain live with the BackTest?)
Broker is told to execute an iteration for a day by the backtest. Broker handles buys, sells, expirations, assignments.
Broker produces the list of expirations and adjusts positions accordingly. It returns the list of assignments to the
Backtest so it can invoke Strategy.hand_assignments(list of Positions, Broker)
Note that the positions are already in the Portfolio. 
BackTest looks at resulting values after end-of-day. If there are no open positions and net liquid is <= 0, then we are
broke and done.
"""


class Backtest:

    def __init__(self, symbol, strategy_cls, starting_balance):
        self._symbol = symbol
        self._chain = Chain(symbol, option_path)
        self._quote = Quote(symbol, quote_path)
        from_dt, to_dt = self._chain.date_range()
        self._strategy = strategy_cls()
        self._start_dt = from_dt
        self._end_dt = to_dt
        self._start_balance = starting_balance
        self._broker = None

    def run(self):
        """

        :return:
        """
        one_day = dt.timedelta(days=1)

        self._broker = Broker(100000.0, self._chain, self._quote)
        self._strategy.prepare(self._symbol)

        current_date = self._start_dt
        while current_date < self._end_dt:

            self._broker.open_current_date(current_date)
            self._strategy.update(current_date, self._broker)

            assigned_shares_count = self._broker.close_current_date()
            if assigned_shares_count:
                self._strategy.assignment(assigned_shares_count, self._symbol, current_date, self._broker)

            print("Day {}\tcash: ${:.2f}\tobp: ${:.2f}\tnet-liquid: ${:.2f}".format(
                  current_date.date(),
                  self._broker.stock_buying_power(),
                  self._broker.option_buying_power(self._broker.stock_buying_power()),
                  self._broker.net_liquid()))

            # Advance!
            current_date = current_date + one_day
