import new_protos_edge as npe
import pandas as pd
import numpy as np

"""
# 
# Strategy Parameters:
#
"""
# NVT or NVV (Transaction Volume or Trading Volume)
fundamental = "nvt"
# Buy/Sell the largest/smallest (in terms of NVT/NVV) x Nr. of tickers
nr_tickers = 6
""" 
Strategy:
 "smallest": buy smallest x tickers (in terms of NVT/NVV)
 "largest": buy largest x tickers (in terms of NVT/NVV)
 "long-short": buy x largest, sell x smallest tickers
 "short-long": buy x smallest, sell x largest tickers
"""
strategy = "long-short"

param = [strategy, nr_tickers]

"""
# 
# Load Data
#
"""
if(fundamental == "nvv"): 
    vol, prices, mcap = npe.loadData('nvv')
    vol_roll = vol.rolling(90).mean()
if(fundamental == "nvt"): 
    vol, prices, mcap = npe.loadData('nvt')
    vol_roll = vol.rolling(90).mean()
nvx = mcap/vol_roll


"""
#
# Backtest Parameters
#
"""
#Rebalance the portfolio every x days
rebalancing_period = 4
# Spread above and below market when buying / selling
# Gets subtracted from Portfolio Balance as transaction costs
spread = 0.006
# Start backtest on xth (lb) day (leave it at 1)
lb = 1

"""
#
# Start the Backtest
#
"""
# Balance parameter to plot and calculate statistics on
track_balance = []
portfolio = npe.initPortfolio(prices.iloc[:1], vol.iloc[:1], param,"nvx")

for i in range(lb,prices.shape[0]):
    
    if(i > lb):
        portfolio = npe.updateBalance(portfolio,prices.iloc[:i,:])
    
    signals = npe.getSignals("nvx",prices.iloc[:i,:],nvx.iloc[:i,:],param)
    
    targetAlloc = npe.RiskManagement(signals,portfolio,prices.iloc[:i,:])
    
    if(i%rebalancing_period == 0):
        portfolio = npe.updatePositions(portfolio,targetAlloc,prices.iloc[:i,:], spread)
    
    track_balance.append(portfolio['balance'])


"""
#
# Results:
#
"""

balance = pd.DataFrame(track_balance)
balance.plot()
returns = balance.pct_change()


print("Balance: " + str(portfolio['balance']))
print("--------------------------------------")
print(portfolio['positions'])
print("--------------------------------------")
print("Sharpe: " + str((returns.mean()/(returns.std())*np.sqrt(365)).values))
print("--------------------------------------")
print("Gain-to-Pain : " + str((returns.sum()/abs(returns[returns < 0].sum())).values))
