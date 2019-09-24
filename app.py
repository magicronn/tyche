import datetime as dt
from tyche.backtest import Backtest
from strategy.buyhold import BuyHold

if __name__ == '__main__':

    # Get options from args
    # Create broker
    # Create strategy
    # Create a backtest per symbol for the given dates
    bt = Backtest('TEAM', BuyHold, 200000)
    bt.run()
