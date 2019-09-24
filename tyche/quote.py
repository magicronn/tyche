import pandas as pd

option_path = '../option_history/'
quote_path = '../quote_history/'

# Sample quote data
# (index) | symbol | quotedate | open | high   | low   | close | volume  | adjustedclose
# 3571    | TEAM   | 8/1/2018  | 72.5 | 74.555 | 72.41 | 73.29 | 1358735 | 73.29

column_functions = {}  # name:fn(row) such as 'ADX':adx_for_row(row)


class InvalidQuoteDate(Exception):
    pass


class Quote:

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
        self.quote_path = path if path else quote_path
        self._cache_frame(col_fns=column_functions)

    def set_current_date(self, current_date):
        """
        Initialize the option chain to a frame and starting date.
        :param current_date: First datadate (calendar date) of the chain to load. Not to be confused with expirations.
        :type current_date: date
        """
        if self.start_date > current_date or current_date > self.end_date:
            raise InvalidQuoteDate()
        self.cur_date = current_date
        self._cache_quote(current_date)
        if self.current.empty:
            raise InvalidQuoteDate()

    def date_range(self):
        return self.start_date, self.end_date

    def query_quotes(self, query):
        tmp = self.current.query(query)
        return tmp

    def get_current_price(self):
        row = self.current.iloc[0]
        return row['close']

    def _cache_frame(self, col_fns: dict = None):
        """
        Load the entire option history file for the given symbol into memory.
        Optionally, apply any columns to the frame
        Slice out the current date chain.
        """
        fn = self.quote_path + self.symbol + '.csv'
        quote_date_cols = ['quotedate']
        self.frame = pd.read_csv(fn, parse_dates=quote_date_cols)
        if col_fns:
            for name, fn in col_fns.items():
                self._add_column_to_frame(name, fn)
        self.frame.sort_values(by='quotedate', inplace=True)
        self.start_date = self.frame['quotedate'].min()
        self.end_date = self.frame['quotedate'].max()

    def _add_column_to_frame(self, name, f):
        """
        :param name: Name for the new column
        :param f: Function to compute the new column given a row
        :return:
        """
        self.frame[name] = self.frame.apply(lambda row: f(row), axis=1)

    def _cache_quote(self, d):
        """
        Extracts the current chain from the larger frame using a filter on the given date.
        Does not current check for errors.
        :param d: date for the chain to cache.
        """
        self.current = self.frame[self.frame['quotedate'] == d]
        return

