# Tyche - Stock &amp; Option Backtesting Framework v0.1

Tyche (English: /ˈtaɪki/; Greek: Τύχη Ancient Greek: [tý.kʰɛː][1] Modern Greek: [ˈti.çi] "luck"; Roman equivalent: Fortuna) was 
the presiding tutelary deity who governed the fortune and prosperity of a city, its destiny.

*Warning: This is pre-release. Do not apply results to your life-savings just yet.*

Tyche is a quick-and-dirty backtest implementation. Given a Strategy implemented in Python, a Backtests can be instantiated with them to 
evaluate performance over the period of the data set. The data set has only one adapter at this time for data from DeltaNeutral.com. They 
do provide sample files, or you can implement an adapter rather trivially. 

Future updates include:
* Richer backtest options:
  * Slippage simulation
  * Open-to-Close evaluation vs. Close-only
  * Auto-sampled date range evaluations
* Example standard indicators for use in Strategies
  * EMA, SMA
  * ADX
* More sample strategies
  * Higher-Highs, Higher-Lows / Lower-Highs, Lower-Lows 
  * The Wheel
  * Selling Iron Condors
  * The Synthetic Wheel

Docs to follow once I get sphinx running again.
