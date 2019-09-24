import datetime as dt
from util import opra_code


class Position:

    def __init__(self, quantity, underlying, instrument_type, strike=0.0, expiration: dt.datetime=None,
                 entry_price=None, current_price=None):
        """
        Represents a holding of one symbol, typically created by one or more orders.
        Bit sneaky as it represents both an option and a stock position.
        Created only by the Brokerage object, but seen by the Strategy
        :param quantity: Number of contracts or shares
        :param underlying: Symbol for the underlying stock or the stock itself
        :param instrument_type: Put, Call, or Stock
        :param strike: Strike price for an option, Entry share price for a stock. Arguably this and cost
                       shouldn't both be entered.
        :param expiration:  Option expiration or None
        :param unit_price: cost for the one stock share or contract.
        """
        self.quantity = quantity
        self.underlying = underlying
        self.instr_type = instrument_type
        self.strike = strike
        self.expiration = expiration
        self.entry_price = entry_price if entry_price else 0.0
        self.current_price = current_price if current_price else self.entry_price

    def __str__(self):
        if self.instr_type[0] == 'S':
            t = "{} x {} @ ${} / ${}".format(self.underlying, self.quantity, self.current_price, self.entry_price)
        else:
            t = opra_code(self.underlying, self.expiration, self.strike, self.instr_type) + \
                " x {} @ ${} / ${}".format(self.quantity, self.current_price, self.entry_price)
        return t

    def opra_code(self):
        if self.instr_type[0] == 'S':
            t = self.underlying
        else:
            t = opra_code(self.underlying, self.expiration, self.strike, self.instr_type)
        return t

    def is_option(self):
        return self.instr_type[0] != 'S'

    def is_call(self):
        return self.instr_type[0] == 'C'

    def is_put(self):
        return self.instr_type[0] == 'P'

    def current_pl(self):
        cpl = self.quantity * (self.current_price - self.entry_price)
        if self.is_option():
            cpl *= 100.0
        return cpl

    def current_value(self):
        cv = self.quantity * self.current_price
        if self.is_option():
            cv *= 100.0
        return cv
