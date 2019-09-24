import numpy as np
import pandas as pd
import datetime as dt

option_path = '../../option_history/'
quote_path = '../../quote_history/'


# Sample data
# OptionSymbol | (Index) | UnderlyingSymbol | UnderlyingPrice | Exchange | OptionExt | Type | Expiration | DataDate |
#   Strike | Last | Bid | Ask | Volume | OpenInterest | IV | Delta | Gamma | Theta | Vega | AKA
# TEAM180615C00020000 | 719624 | TEAM | 66.12 | * |  | call | 6/15/2018 | 6/15/2018 | 20 | 0 | 45.4 | 48.3 | 0 | 0 |
#   0.3 | 1 | 0 | 0 | 0 | TEAM180615C00020000
# TODO: use enumerated column names to allow for other file formats.


def expiration_type_from_row(row):
    d = row['Expiration']
    return expiration_type_from_date(d)


def expiration_type_from_date(d):
    if d.weekday() == 4 and 15 <= d.day <= 21:
        return 'Monthly'
    else:
        return 'Weekly'


column_functions = {'ExpirationType': expiration_type_from_row}


class InvalidChainDate(Exception):
    pass


class Chain:

    def __init__(self, symbol, path=None):
        """
        An option chain collection defined by a symbol. Loads the CSV file from the option_history directory.
        :param symbol: Underlying symbol.
        """
        self.frame = None
        self.current = None
        self.cur_date = None
        self.start_date = None
        self.end_date = None
        self.symbol = symbol
        self.option_path = path if path else option_path
        self._cache_frame(col_fns=column_functions)

    def set_current_date(self, current_date):
        """
        Initialize the option chain to a frame and starting date.
        The frame should be indexed by the opra code - that should be unique for a given day
        :param current_date: First datadate (calendar date) of the chain to load. Not to be confused with expirations.
        :type current_date: date
        """
        if self.start_date > current_date or current_date > self.end_date:
            raise InvalidChainDate()
        self.cur_date = current_date
        self._cache_chain(current_date)
        if self.current.empty:
            raise InvalidChainDate()

    def date_range(self):
        return self.start_date, self.end_date

    def get_by_opra(self, opra_code):
        return self.current.loc[opra_code]

    def get_current_price(self, opra_code, position_size):
        row = self.get_by_opra(opra_code)
        if position_size > 0:
            price = row['Bid']
        else:
            price = row['Ask']
        return price

    def get_current_underlying_price(self, opra_code):
        row = self.get_by_opra(opra_code)
        price = row['UnderlyingPrice']
        return price

    def query(self, query):
        tmp = self.current.query(query)
        return tmp

    def find_expiration(self, ref_date: dt.datetime, min_days_out, weekly=True):
        """
        Locate the expiration that is distance from reference date. Allow for weekly expiration if flagged.
        :param ref_date: Date we want an expiry to be based off of.
        :param min_days_out: Minimum number of days past the reference date. Must be greater than or equal to 0
        :param weekly:
        :return:
        """

        # Shift the reference date by the requested amount, then search on the correct side for it.
        ref_date = ref_date + dt.timedelta(days=min_days_out)

        # Let's get the list of all expiration dates.
        # Note that everything is done in datetime64 in numpy/pandas
        expirs = self.current['Expiration'].dt.to_pydatetime()
        expirs = np.unique(expirs)
        expirs.sort()

        # Are we going forward from current?
        if min_days_out >= 0:
            current_date_limit = self.current["Expiration"].max()
            if ref_date > current_date_limit:
                raise Exception("Date exceed current chain (max is {})".format(current_date_limit))
            for exp in expirs:
                # Have we reached a qualifying expiration (past min_days_out and not weekly if not allowed)
                if exp >= ref_date and (weekly or 'Weekly' != expiration_type_from_date(exp)):
                    # Found one!
                    return exp
        else:
            current_date_limit = self.current["Expiration"].min()
            if ref_date < current_date_limit:
                raise Exception("Date exceed current chain (min is {})".format(current_date_limit))
            for exp in np.flip(expirs):
                if exp <= ref_date and (weekly or 'Weekly' != expiration_type_from_date(exp)):
                    return exp
        return None

    def _cache_frame(self, col_fns: dict = None):
        """
        Load the entire option history file for the given symbol into memory.
        Optionally, apply any columns to the frame
        Slice out the current date chain.
        """
        # TODO: Use the input adapter here to read the thing and rename columns to Tyche standard.

        fn = self.option_path + self.symbol + '.csv'
        option_date_cols = ['Expiration', 'DataDate']
        self.frame = pd.read_csv(fn, parse_dates=option_date_cols)
        if col_fns:
            for name, fn in col_fns.items():
                self._add_column_to_frame(name, fn)
        self.frame.sort_values(by='DataDate', inplace=True)
        self.start_date = self.frame['DataDate'].min()
        self.end_date = self.frame['DataDate'].max()

    def _add_column_to_frame(self, name, f):
        """
        :param name: Name for the new column
        :param f: Function to compute the new column given a row
        :return:
        """
        self.frame[name] = self.frame.apply(lambda row: f(row), axis=1)

    def _cache_chain(self, d):
        """
        Extracts the current chain from the larger frame using a filter on the given date.
        Sets the OptionSymbol (the OPRA code) as the index of this smaller frame.
        Does not current check for errors like dupe indices, or failure to extract.
        :param d: date for the single day's chain to cache.
        """
        self.current = self.frame[self.frame['DataDate'] == d]
        if self.current.empty:
            raise InvalidChainDate("Invalid date for option chain")
        self.current.set_index('OptionSymbol', inplace=True)
        return

# This takes a set of column names and one or more values for the range comparison
# i.e. Strike:(10,) means Strike>=10.  Delta:(.9, .99) means 0.9<=Delta<0.99
# A programmatic way to apply all these filters at once! Make a function that correctly evals
# the param predicate on a set of column values.
# df = df[df[['col_1','col_2']].apply(lambda x: f(*x), axis=1)]
# where f is a function that is applied to every pair of elements (x1, x2) from col_1 and col_2 and
# returns True or False depending on any condition you want on (x1, x2).
# def _filter_row(*x, params):
#     # I'll use the dataframe.query for now
#     return True
#     def filter(self, params: list):
#         """
#         Locate the option matching the given column values, and then finding the one closest to the given
#         underlying price
#         :param params:
#         :return:
#         """
#         # First, filter to strike price
#         # diff_from_price = self.current.assign(DiffStrike = self.current["Strike"] - price)
#         # diff_from_price.sort_values('DiffStrike', inplace=True)
#         # return diff_from_price
#         pass
