import datetime as dt
import pytest
from util import decompose_opra
from tyche.position import Position
from tyche.chain import Chain
from tyche.quote import Quote
from tyche.broker import Broker


valid_opra = {
    'TEAM': [
        ('TEAM180615C00055000', '98,TEAM180615C00055000,704622,TEAM,66.67,*,,call,2018-06-15,2018-06-05,55.0,11.35,'
                                '11.7,12.0,19,789,0.5017,0.9928,0.0037,-3.3675,0.2135,TEAM180615C00055000,1.0'),
        ('TEAM190315C00095000', '15998,TEAM190315C00095000,751040,TEAM,80.7,*,,call,2019-03-15,2018-11-28,95.0,3.3,'
                                '3.3,3.8,1,173,0.4661,0.3093,0.0174,-12.7395,15.3477,TEAM190315C00095000,'
                                '0.267553073795217'),
        ('TEAM190524C00102000', '31998,TEAM190524C00102000,745368,TEAM,126.08,*,,call,2019-05-24,2019-05-15,102.0,'
                                '15.2,22.8,25.6,0,1,0.4082,0.9997,0.0001,-2.7994,0.018000000000000002,'
                                'TEAM190524C00102000,1.0'),
        ('TEAM190621P00105000', '47998,TEAM190621P00105000,727266,TEAM,104.12,*,,put,2019-06-21,2019-02-20,105.0,9.4,'
                                '9.0,9.6,1,46,0.3891,-0.4564,0.017,-12.6315,23.6733,TEAM190621P00105000,1.0'),
        ('TEAM191220C00150000', '59998,TEAM191220C00150000,747370,TEAM,117.17,*,,call,2019-12-20,2019-05-08,150.0,'
                                '0.0,4.5,6.5,0,0,0.3986,0.2806,0.0092,-10.7242,31.0223,TEAM191220C00150000,'
                                '0.3143846634076346'),
        ('TEAM210115P00195000', '78449,TEAM210115P00195000,771091,TEAM,125.88,*,,put,2021-01-15,2019-05-31,195.0,0.0,'
                                '74.6,77.0,0,0,0.4766,-0.6351,0.0048,-5.0587,59.6021,TEAM210115P00195000,1.0')
    ],
    'TLT': [
        ('TLT180928P00121500', '54998,TLT180928P00121500,752147,TLT,116.8,*,,put,2018-09-28,2018-09-24,121.5,4.77,'
                               '4.6,4.8,0,22,0.1356,-0.9987,0.0027,2.4747,0.0464,TLT180928P00121500,1.0'),
        ('TLT181221P00104000', '109998,TLT181221P00104000,715831,TLT,119.71,*,,put,2018-12-21,2018-06-05,104.0,0.55,'
                               '0.26,0.33,0,351,0.135,-0.0558,0.0094,-1.0705,9.9295,TLT181221P00104000,'
                               '0.03413479945010925'),
        ('TLT190222P00128500', '164998,TLT190222P00128500,773729,TLT,120.48,*,,put,2019-02-22,2019-01-14,128.5,0.0,'
                               '7.9,8.65,0,0,0.1433,-0.912,0.0277,-4.2808,6.0546,TLT190222P00128500,1.0'),
        ('TLT190503C00130500', '219998,TLT190503C00130500,749744,TLT,123.9,*,,call,2019-05-03,2019-05-01,130.5,0.07,'
                               '0.0,0.02,0,341,0.1314,0.0,0.0,0.0,0.0,TLT190503C00130500,4.759169835999444e-08'),
        ('TLT190920C00092000', '274998,TLT190920C00092000,775484,TLT,125.99,*,,call,2019-09-20,2019-05-17,92.0,0.0,'
                               '33.85,34.45,0,0,0.0469,1.0,0.0,-2.3606,0.0,TLT190920C00092000,1.0'),
        ('TLT210115P00126000', '329998,TLT210115P00126000,731196,TLT,124.37,*,,put,2021-01-15,2019-04-01,126.0,8.34,'
                               '8.25,8.85,0,3,0.1102,-0.5069,0.0204,-2.1069999999999998,62.3853,TLT210115P00126000,'
                               '1.0'),
        ('TLT210115P00170000', '333285,TLT210115P00170000,783649,TLT,131.83,*,,put,2021-01-15,2019-05-31,170.0,43.0,'
                               '37.5,42.0,0,12,0.1869,-0.7959,0.0074,-1.8645,38.9568,TLT210115P00170000,1.0')
    ],
    'MS': [
        ('MS180601C00040000', '3,MS180601C00046000,500705,MS,51.21,*,,call,2018-06-01,2018-06-01,46.0,0.0,5.0,5.4,0,'
                              '0,0.3,1.0,0.0,0.0,0.0,MS180601C00046000,0.0'),
        ('MS180706P00044000', '4998,MS180706P00044000,478308,MS,51.32,*,,put,2018-07-06,2018-06-12,44.0,0.0,0.0,0.06,'
                              '0,0,0.2845,-0.0142,0.0098,-1.0256,0.4675,MS180706P00044000,0.015044175245536497'),
        ('MS181207C00044000', '49998,MS181207C00044000,515836,MS,45.82,*,,call,2018-12-07,2018-11-05,44.0,1.42,2.73,'
                              '2.8,0,35,0.3123,0.6952,0.0835,-9.2342,4.7009,MS181207C00044000,1.0'),
        ('MS190418P00045000', '99998,MS190418P00045000,484663,MS,48.71,*,,put,2019-04-18,2018-09-04,45.0,2.03,1.95,'
                              '2.05,1200,19,0.2505,-0.2958,0.0359,-2.4936,13.1578,MS190418P00045000,'
                              '0.3497343971075503'),
        ('MS200117C00055000', '149998,MS200117C00055000,507564,MS,42.71,*,,call,2020-01-17,2019-05-23,55.0,0.4,0.32,'
                              '0.4,10,9376,0.2191,0.1067,0.0243,-1.1736,6.3476,MS200117C00055000,0.29802925221883325'),
        ('MS210115P00070000', '165457,MS210115P00070000,512453,MS,40.69,*,,put,2021-01-15,2019-05-31,70.0,22.85,'
                              '28.95,29.95,0,173,0.4015,-0.7599,0.0139,-0.7399,15.075999999999999,MS210115P00070000,'
                              '1.0')
    ]
}
symbols = list(valid_opra.keys())
option_path = '../../option_history/'
quote_path = '../../quote_history/'


@pytest.mark.parametrize("symbol", symbols)
def test_broker_set_current_date(symbol):
    """
    Ideally I'd create a stock and chain here that I could easily test against...
    set_current_date(self, current_date: dt.datetime)
    place_order(self, positions)
        positions(self)
        stock_buying_power(self)
        option_buying_power(self, current_price, cash_available)
    """
    # TODO: Implement a test data generator that we can easily predict outcomes versus these manually computed ones.
    chain = Chain(symbol, option_path)
    quote = Quote(symbol, quote_path)
    broker = Broker(100000.0, chain, quote)

    min_date, max_date = chain.date_range()
    broker.open_current_date(min_date)

    opra_codes = [x for x, y in valid_opra[symbol]]
    # rows = [y for x, y in valid_opra[symbol]]

    total_profit_loss = 0.0

    for oc in opra_codes:

        # buy this position the week before
        symbol, expiration, strike, option_type = decompose_opra(oc)
        if expiration > max_date or \
           expiration - dt.timedelta(days=7) < min_date:
            break

        p = Position(1, symbol, option_type, strike, expiration)

        broker.open_current_date(expiration - dt.timedelta(days=7))
        status_code, status_message = broker.place_order([p])
        assert status_code == 0

        pp = broker.positions()
        assert len(pp) == 1
        assert pp[0].opra_code() == oc
        entry_price = chain.get_current_price(oc, pp[0].quantity)
        profit_loss = -100.0 * entry_price
        assert broker.stock_buying_power() == 100000.0 + profit_loss + total_profit_loss

        # move date forward 7 days
        broker.open_current_date(expiration)
        pp = broker.positions()
        assert len(pp) == 1
        assert pp[0].opra_code() == oc
        assert broker.stock_buying_power() == 100000.0 + profit_loss + total_profit_loss

        # expire the position and possibly impact cash balance
        print("expiring {}".format(oc))
        current_price = chain.get_current_price(oc, pp[0].quantity)
        profit_loss = 100.0 * (current_price - entry_price)
        broker.close_current_date()
        pp = broker.positions()
        assert not pp
        assert broker.stock_buying_power() == 100000.0 + profit_loss + total_profit_loss

        total_profit_loss += profit_loss
