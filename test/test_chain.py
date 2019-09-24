import datetime as dt
import pytest
from util import opra_code
from tyche.chain import Chain


option_path = '../../option_history/'
quote_path = '../../quote_history/'
symbols = {'TEAM', 'TLT'}


def test_get_nearest_expiration():
    symbol = 'MS'

    chain = Chain(symbol, option_path)
    current_date = dt.datetime(year=2018, month=6, day=5)
    chain.set_current_date(current_date)

    expected_expiration = dt.datetime(year=2018, month=6, day=8)

    ref_date = current_date
    expiration = chain.find_expiration(ref_date, 1, weekly=True)
    assert expiration == expected_expiration

    ref_date = dt.datetime(year=2018, month=6, day=11)
    expiration = chain.find_expiration(ref_date, -1, weekly=True)
    assert expiration == expected_expiration

    ref_date = dt.datetime(year=2018, month=6, day=1)
    expiration = chain.find_expiration(ref_date, 1, weekly=False)
    expected_expiration = dt.datetime(year=2018, month=6, day=15)
    assert expiration == expected_expiration


def test_get_by_opra():
    symbol = 'MS'

    chain = Chain(symbol, option_path)
    current_date = dt.datetime(year=2018, month=6, day=7)
    chain.set_current_date(current_date)

    expiration = dt.datetime(year=2018, month=6, day=8)
    strike = 56
    opt_type = 'Call'
    oc = opra_code(symbol, expiration, strike, opt_type)
    x = chain.get_by_opra(oc)
    assert x['UnderlyingSymbol'] == symbol
    assert x['Strike'] == strike
    assert x['Expiration'] == expiration
    assert x['DataDate'] == current_date

    current_date = dt.datetime(year=2018, month=7, day=18)
    chain.set_current_date(current_date)

    expiration = dt.datetime(year=2018, month=7, day=20)
    strike = 43
    opt_type = 'PUT'
    oc = opra_code(symbol, expiration, strike, opt_type)
    x = chain.get_by_opra(oc)
    assert x['UnderlyingSymbol'] == symbol
    assert x['Strike'] == strike
    assert x['Expiration'] == expiration
    assert x['DataDate'] == current_date


@pytest.mark.parametrize("symbol", symbols)
def test_load_chain(symbol):
    chain = Chain(symbol, option_path)
    start, end = chain.date_range()
    assert start < end
    chain.set_current_date(start)
