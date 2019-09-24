import os
from adapters.adapter import Adapter
import pandas as pd


# Sample data
# (index) | symbol | quotedate | open | high   | low   | close | volume  | adjustedclose
# 3571    | TEAM   | 8/1/2018  | 72.5 | 74.555 | 72.41 | 73.29 | 1358735 | 73.29

# Sample option data
# OptionSymbol | (Index) | UnderlyingSymbol | UnderlyingPrice | Exchange | OptionExt | Type | Expiration | DataDate |
#   Strike | Last | Bid | Ask | Volume | OpenInterest | IV | Delta | Gamma | Theta | Vega | AKA
# TEAM180615C00020000 | 719624 | TEAM | 66.12 | * |  | call | 6/15/2018 | 6/15/2018 | 20 | 0 | 45.4 | 48.3 | 0 | 0 |
#   0.3 | 1 | 0 | 0 | 0 | TEAM180615C00020000

# TODO: Make this overrideable here
option_path = '/OneDrive/dev/option_history/'
quote_path = '/OneDrive/dev/quote_history/'


class DeltaNeutralAdapater(Adapter):

    def load_option_csv(self, symbol):
        """

        :param symbol:
        :return: pandas dataframe
        """
        fn = os.environ['HOMEPATH'].replace('\\', '/') + option_path + symbol + '.csv'
        option_date_cols = ['Expiration', 'DataDate']
        frame = pd.read_csv(fn, parse_dates=option_date_cols)
        return frame

    def load_quote_csv(self, symbol):
        """

        :param symbol:
        :return: pandas dataframe
        """
        fn = os.environ['HOMEPATH'].replace('\\', '/') + quote_path + symbol + '.csv'
        fn = quote_path + symbol + '.csv'
        quote_date_cols = ['quotedate']
        frame = pd.read_csv(fn, parse_dates=quote_date_cols)
        return frame
