import re
import math
import datetime as dt
import pandas as pd
from scipy.stats import norm


option_path = '../option_history/'


def opra_code(symbol: str, expiration: dt.datetime, strike, opt_type: str):
    """
    returns the OPRA code for the option per https://www.schwabpt.com/public/file/P-9423758/spt011453.pdf
    :param symbol:
    :param expiration:
    :param strike:
    :param opt_type:
    :return: opra code
    :rtype: str
    """
    # Note that OPRA code for a stock is just the underlying symbol.
    if opt_type[0] == 'S':
        opra = symbol
    else:
        # Would be smarter to compute the 2 digit year code differently. Lazy because our data starts past 2001
        opra = "{}{:02d}{:02d}{:02d}{}{:08d}".format(symbol,
                                                     expiration.year-2000, expiration.month, expiration.day,
                                                     opt_type[0],
                                                     int(strike*1000))
    return opra


def decompose_opra(oc):
    """
    Parse oc like MS180601C00040000
    :param oc:
    :return: symbol, expiration, strike, option_type
    """
    symbol_match_string = '([A-Z]+)([0-9][0-9])([0-9][0-9])([0-9][0-9])([CP])([0-9]+)'
    reg = re.match(symbol_match_string, oc)
    symbol = reg.group(1)
    exp_yr = int(reg.group(2))
    exp_mo = int(reg.group(3))
    exp_day = int(reg.group(4))
    opt_type = reg.group(5)
    strike = int(reg.group(6))/1000.0
    expiration = dt.datetime(2000 + exp_yr, exp_mo, exp_day)
    return symbol, expiration, strike, opt_type


def _prob_itm(row):
    prob_itm = 0.0
    dte = float((row['Expiration'] - row['DataDate']).days) / 365.0
    atm_iv = row['ProbITM']
    denom = atm_iv * math.sqrt(dte)
    if denom > 0:
        current_price = row['UnderlyingPrice']
        strike_price = row['Strike']
        typ = row['Type']
        prob_itm = 1.0
        if typ == 'put' and strike_price <= current_price:
            prob_itm = norm.cdf(math.log(strike_price/current_price) / denom)
        elif typ == 'call' and strike_price > current_price:
            prob_itm = 1 - norm.cdf(math.log(strike_price/current_price) / denom)
    return prob_itm


def _opra_code_from_df_row(row):
    """
    returns the OPRA code for the option per https://www.schwabpt.com/public/file/P-9423758/spt011453.pdf
    :param row: a Numpy
    :return: opra code
    :rtype: str
    """
    symbol = row['UnderlyingSymbol']
    expiration = row['Expiration']
    strike = row['Strike']
    opt_type = row['Type']
    opra = "{}{}{}{}{}{:08d}".format(symbol.ljust(6, ' '),
                                 expiration.year, expiration.month, expiration.day,
                                 opt_type[0],
                                 int(strike*1000))
    return opra


def add_studies_histories():
    """
    One time function to run on all new data extracts.
    Adds a few additional columns to each:
       Options: ProbITM
       Quotes: ADX
    """
    symbols = ['RUT']

    for symbol in symbols:
        fn = option_path + symbol + '.csv'
        print("Loading {}".format(fn))
        option_date_cols = ['Expiration', 'DataDate']
        frame = pd.read_csv(fn, parse_dates=option_date_cols)

        # Let's store the atm_TYPE_iv for every expiration, type
        # First, we compute distance of each to the current strike in abs terms
        print("  Compute atm distance")
        frame['ProbITM'] = frame.apply(lambda row: abs(row['Strike'] - row['UnderlyingPrice']), axis=1)

        # Now we return the index of the row with the min for the group as a series indexed by DataDate and Type
        print("  Compute min atm dist indices")
        min_atm_idx = frame.groupby(['DataDate', 'Type'])['ProbITM'].idxmin()

        # For every row in the frame, look up it's atm_iv index from the series and get the IV from that row.
        print("  Store atm_iv")
        frame['ProbITM'] = frame.apply(lambda row: frame['IV'].loc[min_atm_idx.loc[(row['DataDate'], row['Type'])]],
                                       axis=1)

        print("  Compute prob_iv")
        frame['ProbITM'] = frame.apply(lambda row: _prob_itm(row), axis=1)

        print("  Adding OPRA codes")
        frame['OPRA'] = frame.apply(lambda row: _opra_code_from_df_row(row), axis=1)

        # and save it back to disk
        print("  Save file")
        with open(fn, mode='w', newline='\n') as fh:
            frame.to_csv(fh, line_terminator='\n')


def build_data_lakes():
    symbols = ['MS']
    for symbol in symbols:
        fn = option_path + symbol + '.csv'
        print("Loading {}".format(fn))
        option_date_cols = ['Expiration', 'DataDate']
        frame = pd.read_csv(fn, parse_dates=option_date_cols)

        # First, write the big file at $ROOT/SYMBOL/YEAR/SYMBOL_chains.csv
        full_fn = option_path + symbol + "/" + symbol + "_chains.csv"
        with open(full_fn, mode='w', newline='\n') as fh:
            frame.to_csv(fh, line_terminator='\n')

        # Next, split frame by month of the DataDate and write out as CSV in these files:
        # $ROOT/SYMBOL/YEAR/MM/SYMBOL_chains.csv
        # TODO: Subdivide and write the files in the new locations
