from typing import List
from math import copysign
import datetime as dt
from util import opra_code
# import sys
# sys.path.append("..")
from tyche.position import Position
from tyche.chain import Chain
from tyche.quote import Quote


# Reminder: The user does not have access to this class inside the simulator so price is correctly managed by the
# Simulator and Market.
class Portfolio:

    class Order(Position):

        def __init__(self, quantity, underlying, instrument_type, strike,
                     expiration: dt.datetime, unit_price, open_date: dt.datetime):
            """
            Init internal structure for holding an order transaction in the portfolio
            :param quantity: number of options in the transaction
            :param underlying: underlying stock or the stock itself
            :param instrument_type: C or P or S (we will only keep the first letter of what is given)
            :param strike: Strike price of the option or initial Share price for a stock
            :param expiration: Obvious. Unused for stocks.
            :param unit_price: Current price. Since this is internal to the Simulation, we assume price is correct
            :param open_date: Date of the simulation order was executed.
            """
            super().__init__(quantity, underlying, instrument_type, strike, expiration, unit_price)
            self.open_date = open_date
            self.close_date = None

        def __str__(self):
            t = "Order: {} x {} @ ${} / ${}".format(self.opra_code(), self.quantity,
                                                    self.current_price, self.entry_price)
            return t

        def mark_closed(self, current_date):
            self.close_date = current_date

        def set_current_price(self, chain, quote):
            """
            Given the current day's option Chain and stock Quote, compute the current_PL for this order.
            :param chain:
            :param quote:
            :return:
            """
            if self.is_option():
                price = chain.get_current_price(self.opra_code(), self.quantity)
            else:
                price = quote.get_current_price()
            self.current_price = price

        def gen_position(self) -> Position:
            p = Position(self.quantity, self.underlying, self.instr_type,
                         self.strike, self.expiration, self.entry_price, self.current_price)
            return p

        @staticmethod
        def gen_merged_position(orders):
            """
            Folds a list of Orders with identical opra_codes into a single Position. Used in making Statements for
            the Strategy.
            Quantities are added (closing or opening effectively), Prices are averaged, open dates are lost, and
            Current_PL are summed.
            NOte: Putting a return specifier on the signature "-> Position", but returning None violates that type.
            :param orders: list of Orders that are to be merged into a single Position for reporting in the statement
            :return:
            """
            cnt = len(orders)
            if cnt:
                p: Position = orders[0].gen_position()
                if cnt > 1:
                    for order in orders[1:]:
                        p.entry_price = p.entry_price * p.quantity + order.entry_price * order.quantity
                        p.entry_price /= abs(p.quantity) + abs(order.quantity)
                        p.current_price = p.current_price * p.quantity + order.current_price * order.quantity
                        p.current_price /= abs(p.quantity) + abs(order.quantity)
                        p.quantity += order.quantity
                return p
            return None

    def __init__(self):
        self._orders = {}  # dict of order lists keyed by OPRA
        self._closed_orders = {}  # same, but have close dates
        self._closed_pl = 0.0
        self._open_pl = 0.0
        self._liquid = 0.0

    def __str__(self):
        lines = []
        for oc, pp in self._orders.items():
            x = oc + ": " + str(pp)
            lines.append(x)
        return "\n".join(lines)

    def add_order(self, count, underlying, expiration: dt.datetime, instrument_type, strike,
                  exec_date: dt.datetime, unit_price, reconcile_only = False):
        """
        For use by the Brokerage only!
        Reconcile this order against the current open orders, creating a closed order if that is what happened.
        That is, if we are long in X with M options, and we get an order for +N, then we add an order to the open
        orders set.
        However, if we are long (short) in X with M options, and we get an order for -N (+N), then we are closing part
        or all of the current position.
        If abs(N) == abs(M), then simply close the order (set close date, price, etc.) then move to closed orders.
        If abs(N) < abs(M), then we have only closed part of it. Clone X to make Y.  Reduce X quantity by M and leave
        it alone. Set Y to closed and update the closed parameters -> Set quantity to -M, with the opposite sign, to
        the number of options closed.
        If abs(N) > abs(M), then we have over closed the position. Mark X closed, update params, and move it to closed.
        Reduce new order quantity to N+M, and continue onto the next order.

        ASSUMES that current price is set on all open orders.

        :param count: Number of contracts, positive to buy, negative to sell.
        :param underlying:
        :param expiration:
        :param instrument_type:
        :param strike:
        :param exec_date: Assumed to be the current_date. May need to explicity have that in the future - just in case.
        :param unit_price: Price paid for for one Share or one Contract in this order
        :param reconcile_only: Only close existing positions with this order. Do not place new ones.
        :return: number of units unordered (only non-zero if reconcile_only is true)
        """

        oc = opra_code(underlying, expiration, strike, instrument_type)
        if oc not in self._orders:
            if not reconcile_only:
                # Haven't seen this opra before? Great. Start a new Order list for it.
                p = self.Order(count, underlying, instrument_type, strike, expiration, unit_price, exec_date)
                self._orders[oc] = [p]
        else:
            # Orders exist for this OC. Close them from front to back.
            # Compare to the first order in the current list. All orders in the list are the same - long or short.
            pp: List = self._orders[oc]
            while pp and count != 0:
                p = pp.pop()
                new_sign = copysign(1, count)
                cur_sign = copysign(1, p.quantity)

                if new_sign == cur_sign:
                    # We are extending the current position with a new Order. Put pp back to front of the list,
                    pp.insert(0, p)
                    # And add the new one to the end.
                    p = self.Order(count, underlying, instrument_type, strike, expiration, unit_price, exec_date)
                    self._orders[oc].append(p)
                    count = 0
                else:
                    # We are closing part or all of the current position p
                    if abs(count) >= abs(p.quantity):
                        # Complete closed this one.
                        p.mark_closed(exec_date)
                        self._add_closed_orders(oc, [p])
                        # reduce current quantity by the closed quantity (add since signs differ).
                        count += p.quantity

                    else:
                        # Partially close this one. Adjust quantity and push it back onto the front.
                        p.quantity += count
                        self._orders[oc].insert(0, p)
                        # And add a closed order with the current count.
                        p = self.Order(count, underlying, instrument_type, strike, expiration, unit_price, exec_date)
                        p.mark_closed(exec_date)  # Definitely need to set the P/L
                        self._add_closed_orders(oc, [p])
                        count = 0

            # If count!=0, then the active orders should be empty as we closed them all.
            # Create a new order and put in the actives.
            if count != 0 and not reconcile_only:
                p = self.Order(count, underlying, instrument_type, strike, expiration, unit_price, exec_date)
                self._orders[oc].append(p)
                count = 0

        return count

    def update_prices(self, chain: Chain, quote: Quote):
        """
        This is where the money gets counted.
        For each open order, update its current profit and loss using the day's option chain.
        Note that PL does deduct entry cost, so on minute 0, PL is 0 (theoretically).
        Add total open current_pl to get the equity balance
        Add total closed current_pl to get the pl balance
        The broker will compute net_liquid and available balance with these.
        :param chain: the current day's option chain
        :param quote: the current day's stock quote
        :return: equity balance from open orders, cash balance from closed orders
        :rtype: (double, double)
        """
        self._open_pl = 0.0
        self._liquid = 0.0
        # Total the open orders, setting current_pl as we go
        for oc, pp in self._orders.items():
            p: Portfolio.Order
            for p in pp:
                p.set_current_price(chain, quote)
                self._open_pl += p.current_pl()
                self._liquid += p.current_value()
        # Total the closed orders again because I am not yet confident the sum can be cached and updated correctly :-)
        self._closed_pl = 0.0
        for oc, pp in self._closed_orders.items():
            for p in pp:
                self._closed_pl += p.current_pl()
        return self._open_pl, self._closed_pl, self._liquid

    def gen_statement(self) -> List[Position]:
        """
        Create a read-only view of the open Positions for the Strategy to peruse.
        :return: A list of open positions
        :rtype: List[Position]
        """
        flat: List[Position] = []
        for oc, pp in self._orders.items():
            p = self.Order.gen_merged_position(pp)
            if p:
                flat.append(p)
        return flat

    def expire_positions(self, current_date):
        """
        Check each position to see if this is the expiration date.
        If it has expired, move it to closed and add it to the return list
        :param current_date:
        :return:
        """
        expiry: List[Portfolio.Order] = []

        # iterate over a separate copy of the keys to avoid modifying the dict during iteration
        ocs = list(self._orders.keys())
        for oc in ocs:
            pp = self._orders[oc]

            # Does this oc have expiring options?
            ex = [p for p in pp if p.expiration and p.expiration <= current_date]
            if ex:
                # First, add these to the return list
                expiry.extend(ex)

                # Second, remove them from the original list for that oc
                self._orders[oc] = [p for p in pp if not (p.expiration and p.expiration <= current_date)]

                # Speed up loops by removing empty lists
                if not self._orders[oc]:
                    del self._orders[oc]

                # Add them to the closed order list
                self._add_closed_orders(oc, ex)

        # Mark them closed and return the final list
        map(lambda p: p.mark_closed(current_date), expiry)
        return expiry

    def current_open_pl(self):
        return self._open_pl

    def current_value(self):
        return self._liquid

    def _add_closed_orders(self, closing_opra_code, closing_orders):
        """
        :param closing_opra_code: Must be the code for all of the given orders to be added to the closed list
        :param closing_orders: list of orders
        :ptype pp: list of Order
        """
        if closing_opra_code not in self._closed_orders:
            self._closed_orders[closing_opra_code] = []
        self._closed_orders[closing_opra_code].extend(closing_orders)
