from typing import List
import datetime as dt
from tyche.chain import Chain, InvalidChainDate
from tyche.quote import Quote, InvalidQuoteDate
from tyche.portfolio import Portfolio
from tyche.position import Position


class Broker:
    """
    Broker is a set of methods used by the Strategy to perform it's inner loop, daily evaluation during a backtest.
    A larger, outer object will run multiple backtests with multiple symbols, time ranges, params and strategies.
    For now, consider a broker a one-use, expensive object.
    """

    def __init__(self, starting_balance, chain: Chain, quote: Quote, margin_multiple=0.3):
        """
        Initialize the broker for a backtest. Must be created for each backtest run - not yet reusable.
        :param starting_balance: Initial balance for the account
        :param chain: option chain for evaluating derivative positions
        :param quote: quote history for evaluating equity positions
        :param margin_multiple: ratio of intrinsic option impact to cash that must be held in reserve
        """

        # Current datetime in the backtest. *Should only roll forward.*
        self._current_date = None

        # Portfolio holds this list of open and closed orders at the Brokerage
        self._portfolio = Portfolio()

        # Maximum HighBalance, LowBalance for this backtest
        self._high_balance = starting_balance
        self._low_balance = starting_balance

        # Current cash balance. Adjusted after each order is placed or day ends.
        self._cash_balance = starting_balance

        # Discount for covering with cash. $10 with a margin multiple of 0.5 yields $20 of option buying power
        self._margin_multiple = margin_multiple

        # Total money of covering margin we have for making option trades. Does not include cash.
        self._cover_shares = 0

        # Chain and Quote hold the prices, etc. for all traded symbols
        self._chain: Chain = chain
        self._quote: Quote = quote
        self._underlying_price = 0.0

        self._order_codes = [
            "Order Placed",
            "Insufficient Cash",
            "Insufficient Option Buying Power",
            "OPRA Not Traded",
            "Symbol Not Found",
            "Insufficient Open Interest",
            "Not Filled at That Price"
        ]

    def open_current_date(self, current_date: dt.datetime):
        """
        Acts as the entry point for a new simulation state. Must be called before placing orders or handling
        expirations.
        :param current_date:
        :return:
        """
        # First verify current date is valid
        # We'll automatically skip the weekends (Mon is 0, Sunday is 6)
        if current_date.weekday() > 4:
            current_date = current_date + dt.timedelta(days=1)

        # Now skip over holidays and closures
        valid_date = False
        while not valid_date:
            try:
                self._quote.set_current_date(current_date)
                self._chain.set_current_date(current_date)
                self._current_date = current_date
                self._underlying_price = self._quote.get_current_price()
                self._portfolio.update_prices(self._chain, self._quote)
                valid_date = True
            except InvalidQuoteDate:
                # Nope, try again.
                current_date = current_date + dt.timedelta(days=1)
            except InvalidChainDate:
                # Nope, try again.
                current_date = current_date + dt.timedelta(days=1)
        return current_date

    def close_current_date(self):
        """
        Up to invoking class to deal with assignments as seen fit.
        :return: Count of shares assigned
        """
        cnt_assigned = self._handle_expirations()
        self._low_balance = min(self._low_balance, self._cash_balance)
        self._high_balance = max(self._high_balance, self._cash_balance)
        # TODO: handle margin calls and such here, or possibly end backtest.
        return cnt_assigned

    def option_chain(self):
        return self._chain

    def stock_quote(self):
        return self._quote

    def place_order(self, positions):
        """
        Strategy calls this method to attempt to place an order.
        First, evaluate the cost of the order in terms of option margin and cash. If it costs too much, reject it.
        Where does the current_date come from?
        The cost should be set here and the price should be validated!
        :param positions:
        :return: status code = 1 for success, etc., status_description such as "balance error"
        :rtype: int, str
        """
        # TODO: Add more validations before placing order
        # For all Stock orders, check for Symbol exists
        # For all Option orders,  opra code existence, sufficient open interest
        # Do not allow purchase on date of expiration (will just be a shortcoming of this version)
        status_code = 0

        # Set current price on the positions provided by the Strategy.
        for p in positions:
            p.entry_price = self._get_current_position_price(p)

        # Compute impact to marginable_shares and cash.
        # i.e. if there are marginable shares, then each sold option can impact that count.
        # Any such order not covered will impact cash by the margin multiple.
        total_cost, total_cover = self._get_total_costs_to_place(positions)

        if total_cost > self._cash_balance:
            status_code = 1
            return -status_code, self._order_codes[status_code]

        option_buy_power = self.option_buying_power(self._cash_balance - total_cost)
        if total_cover * self._underlying_price > option_buy_power:
            status_code = 2
            return -status_code, self._order_codes[status_code]

        for p in positions:
            self._portfolio.add_order(p.quantity, p.underlying, p.expiration, p.instr_type,
                                      p.strike, self._current_date, p.entry_price)

        self._cash_balance -= total_cost
        self._cover_shares -= total_cover

        return -status_code, self._order_codes[status_code]

    def positions(self):
        return self._portfolio.gen_statement()

    def stock_buying_power(self):
        return self._cash_balance

    def option_buying_power(self, cash_available):
        """
        Return the maximum option margin we can do.
        :param cash_available: Amount of cash avaiable to margin against. Note that this may not be the
        same as cash on hand.
        :return: money buying power
        """
        bp = 0.0
        if self._cover_shares > 0:
            bp = self._cover_shares * self._underlying_price
        bp += cash_available / self._margin_multiple
        return bp

    def net_liquid(self):
        return self._portfolio.current_value() + self._cash_balance

    @staticmethod
    def _get_total_costs_to_place(positions: List[Position]):
        """
        Given a list of Positions, and knowing the current date, quote, and chain, compute the total cost in cash and
        covering shares (margin) to execute this trade. Up to the calling methods to determine current option buying
        power and margin requirements.
        :param positions: List of positions to be considered a single transaction
        :return: total_cash_cost, count_of_covering_shares_needed
        :rtype: double, int
        """
        total_cash = 0.0
        cover_count = 0
        for p in positions:
            if p.is_option():
                total_cash += p.quantity * p.entry_price * 100
                # Selling so need to cover.
                if p.quantity < 0:
                    # Write Call/Put - Need to own/short the stock or must have margin to potentially buy the stock
                    cover_count += p.quantity * 100
            else:
                total_cash += p.quantity * p.entry_price
                cover_count -= p.quantity
        return total_cash, cover_count

    def _handle_expirations(self):
        """
        The Broker gets the list of expiring positions from the Portfolio and disposes of them.
        To close a position, the broker adds a position with the negated quantity.
        If a position should be assigned, then the broker must place an order for the stock. Pretty simple really.
        The portfolio is responsible for balances.
        :return: List of positions created by assignment
        """
        assigned_positions = 0
        expiry = self._portfolio.expire_positions(self._current_date)
        if expiry:
            # Handle long/short itm/otm and then close all expired positions.
            p: Portfolio.Order
            for p in expiry:
                current_underlying_price = self._get_current_underlying_price(p)
                if p.quantity >= 0:   # Long position
                    if p.is_call() and p.strike <= current_underlying_price or \
                       p.is_put() and p.strike >= current_underlying_price:
                        # ITM!  - Adjust the cash balance.
                        self._cash_balance += p.current_value()
                else:   # Short position
                    if p.is_call() and p.strike <= current_underlying_price:
                        # Short Call assigned: Must sell stock at that price.
                        self._handle_assigned_call(p)
                    elif p.is_put() and p.strike >= current_underlying_price:
                        # Short Put expired: Must buy the stock at the strike.
                        assigned_positions += self._handle_assigned_put(p)
            # Clean up all these expired positions.
            self._portfolio.expire_positions(self._current_date)
        return assigned_positions

    def _get_current_position_price(self, p: Position):
        if p.is_option():
            price = self._chain.get_current_price(p.opra_code(), p.quantity)
        else:
            price = self._quote.get_current_price()
        return price

    def _get_current_underlying_price(self, p: Position):
        oc = p.opra_code()
        if p.is_option():
            price = self._chain.get_current_underlying_price(oc)
            return price
        return 0.0  # OR throw an exception here

    def _handle_assigned_call(self, p: Position):
        """
        A call was sold and expired. Strategy is obligated to sell stock at the Strike.
        Will take from current Portfolio first, then from cash balance.
        :param p: Expiring short Call
        """
        uncovered_shares = self._portfolio.add_order(-p.quantity*100, p.underlying, p.expiration,
                                                     'S',
                                                     p.strike,
                                                     self._current_date,
                                                     p.strike,
                                                     reconcile_only=True)
        if uncovered_shares:
            self._cash_balance -= uncovered_shares * self._quote.get_current_price()
        # Verify the option p has current_price  0.0

    def _handle_assigned_put(self, p: Position):
        """
        A put was sold and expired. Strategy is obligated to buy the underlying at the Strike.
        :param p: Expiring short PUT
        :return: count of assigned shares
        """
        self._portfolio.add_order(p.quantity * 100, p.underlying, dt.datetime.today(), 'S',
                                  p.strike, self._current_date, 100.0 * p.strike)
        # Verify the option has current_price to 0
        return p.quantity * 100
