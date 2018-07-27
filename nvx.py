import protos_edge as pe
import pandas as pd
import numpy as np


### Load Data: OHLC for Top 5
tickers = ['bitcoin','ethereum','ripple','litecoin','dash','nem', 'ethereum-classic',
           'zcash','pivx','golem-network-tokens','decred','digibyte','dogecoin',
           'verge']

start_date = '2017-01-01'
end_date = '2018-07-23'

ohlc = pe.load_ohlc(tickers,start_date,end_date)

nvx = pe.load_nvx('nva',tickers,start_date,end_date)

portfolio = pe.Portfolio(ohlc,tickers)

spread = 0.004

strategies = ['fundamental-value']
signal_parameters = ['long-only','smallest',5]

risk_mgmt_param = ["equal-weight"]

rebalancing_period = 7

"""
################################ TEST ############################
signals = pe.get_signals(strategies,[i.iloc[:530] for i in ohlc],nvx.iloc[:530],signal_parameters)
target_alloc = pe.risk_management(portfolio,signals,[i.iloc[:530] for i in ohlc],risk_mgmt_param)
portfolio, delta = pe.execute_target_allocation(portfolio,target_alloc,[i.iloc[:530] for i in ohlc],spread)
#portfolio = pe.update_balance(portfolio,[i.iloc[:531] for i in ohlc])

print(target_alloc)
print("-------------------")
print(portfolio.positions)
print("-------------------")
print(delta)
"""



track_balance = []
dates = []

for day in range(1,ohlc[0].shape[0]):
    
    # Update Balance
    if(day > 1):
        portfolio = pe.update_balance(portfolio,[i.iloc[:day] for i in ohlc])

    
    # Get Signals
    signals = pe.get_signals(strategies,[i.iloc[:day] for i in ohlc],nvx.iloc[:day],signal_parameters)


    # Risk Management --> Target Allocation
    target_alloc = pe.risk_management(portfolio,signals,[i.iloc[:day] for i in ohlc],risk_mgmt_param)


    # Execute Target Allocation
    if(day == 1):
        portfolio = pe.execute_target_allocation(portfolio,target_alloc,[i.iloc[:day] for i in ohlc],spread)
    if(day % rebalancing_period == 0):
        portfolio = pe.execute_target_allocation(portfolio,target_alloc,[i.iloc[:day] for i in ohlc],spread)


    # Track returns for Plotting
    track_balance.append(portfolio.balance[-1])
    dates.append(ohlc[3].iloc[day-1].name)
  
    
    

balance = pd.DataFrame(track_balance, index=dates)
balance.plot()
returns = balance.pct_change()

print("Balance: " + str(portfolio.balance[-1]))
print("--------------------------------------")
print(portfolio.positions)
print("--------------------------------------")
print("Sharpe: " + str((returns.mean()/(returns.std())*np.sqrt(365)).values))
print("--------------------------------------")
print("Gain-to-Pain : " + str((returns.sum()/abs(returns[returns < 0].sum())).values))


