# -*- coding: utf-8 -*-
import sqlalchemy as sql
import pandas as pd
from datetime import timedelta
import numpy as np


def load_nvx(nvx,tickers,start_date,end_date):
##############################################
#
#   Loads Data for Fundamental Value Ratios: 
#   
#   nvx
#   'nvt': Network Value (Marketcap) to Transaction Volume
#   'nvv': Network Value (Marketcap) to Trading Volume
#   'nva': Network Value (Marketcap) to Active Addresses
#   'metcalfe': Network Value (Marketcap) to (Active Addresses)^2
#
#   tickers 
#   List of Tickers to get Ratios for.
#   ['ticker1','ticker2']
#   Complete List of possible tickers: 
#
#   start_date, end_date
#   'YYYY-MM-DD' 
#   Example: '2018-01-01'
#
#   Returns a Pandas Dataframe.
#   Missing Values = 'NaN'
#
##############################################

    
    ## Load Data:
    
    tickers = ['Date'] + tickers
    ticker_str = ', '.join("`{}`".format(ticker) for ticker in tickers)
    
    engine = sql.create_engine('mysql+pymysql://protos-public:protos-public@google-sheet-data.cfyqhzfdz93r.eu-west-1.rds.amazonaws.com:3306/public')     
        
    data = pd.read_sql("Select " + str(ticker_str) + " From " + str(nvx), con=engine)
        
    ## Clean Data:
        
    data.set_index('Date', inplace=True)
    data.index = pd.to_datetime(data.index)
    date_filter = (data.index >= start_date) & (data.index <= end_date)
    data = data[date_filter]
    # frequency_filter = data['Date'] == ...
    # price = price[frequency_filter]
    data.fillna("NaN")
    
    try:
        data = data.apply(lambda x: x.str.replace(',',''))
    except: pass

    data = data.apply(pd.to_numeric, errors='coerce')
        
    return data  


def load_ohlc(tickers,start_date,end_date):
##############################################
#
#   Loads Open, High, Low, Close Price Data:
#   
#   tickers 
#   List of Tickers to get Ratios for.
#   ['ticker1','ticker2']
#   Complete List of possible tickers: 
#
#   start_date, end_date
#   'YYYY-MM-DD' 
#   Example: '2018-01-01'
#
#   Returns a List of Pandas Dataframes.
#   ohlc[0]: Open Dataframe
#   ohlc[1]: High Dataframe
#   ohlc[2]: Low Dataframe
#   ohlc[3]: Close Dataframe
#
##############################################
    
    ## Load Data:
    
    tickers = ['Date'] + tickers
    ticker_str = ', '.join("`{}`".format(ticker) for ticker in tickers)
    
    engine = sql.create_engine('mysql+pymysql://protos-public:protos-public@google-sheet-data.cfyqhzfdz93r.eu-west-1.rds.amazonaws.com:3306/public')
            
    opening = pd.read_sql("Select " + str(ticker_str) + " From open", con=engine)
    high = pd.read_sql("Select " + str(ticker_str) + " From high", con=engine)
    low = pd.read_sql("Select " + str(ticker_str) + " From low", con=engine)
    closing = pd.read_sql("Select " + str(ticker_str) + " From close", con=engine)
    
    ## Clean Data:
    
    data = [opening, high, low, closing]
    cleaned_data = []
    
    for i in data:
    
        i.set_index('Date', inplace=True)
        i.index = pd.to_datetime(i.index)
        date_filter = (i.index >= start_date) & (i.index <= end_date)
        i = i[date_filter]
        # frequency_filter = data['Date'] == ...
        # price = price[frequency_filter]
        i.fillna('NaN')
        i = i.apply(lambda x: x.str.replace(',',''))
        i = i.apply(pd.to_numeric, errors='coerce')
        
        cleaned_data.append(i)

    return cleaned_data


def get_signals(strategy,ohlc,data,parameters):
##############################################
#
#   Get Signals for Trading Strategies:
#   
#   strategy
#   'fundamental-strategy': Buy/Sell the largest/smallest tickers according to a value ratio
#   
#   parameters
#   List of Parameters for the chosen Strategy
#   [param1,param2,param3]
#   param1: 
#       'long-only': Buy the tickers with the largest/smallest value ratio
#       'long-short': Buy the tickers with the largest/smallest value ratio
#   param2: 
#       'largest': buys the largest tickers (long-only) and shorts the smallest tickers (long-short)
#       'smallest': buys the smallest tickers (long-only) and shorts the largest tickers (long-short)
#   param3:
#       x: number of tickers to buy (long-only) and sell (long-short)
#   
#   data
#   Fundamental Value Ratio as a Dataframe (from load_nvx())
#   
#   ohlc
#   List of Price Dataframes
#   ohlc[0]: Open 
#   ohlc[1]: High 
#   ohlc[2]: Low 
#   ohlc[3]: Close 
#   
#   Returns a Signal for every ticker
#
##############################################
    
                
    if(strategy == 'fundamental-value'): signals = nvx(ohlc,data, parameters)
        
    return signals


def nvx(ohlc,nvx, param):
##############################################
#
#   Calculate Signals for the Fundamental Value Strategy
#   
#   ohlc
#   List of Price Dataframes
#   ohlc[0]: Open 
#   ohlc[1]: High 
#   ohlc[2]: Low 
#   ohlc[3]: Close 
#   
#   nvx
#   Fundamental Value Ratio as a Dataframe (from load_nvx())
#   
#   Returns a Signal for every ticker
#
##############################################
    
    if(param[0] == "long-only"):      
        if(param[1] == "smallest"):        
            selection = nvx.iloc[-1].nsmallest(param[2])        
        if(param[1] == "largest"):        
            selection = nvx.iloc[-1].nlargest(param[2])
        signals = ohlc[3].iloc[-1]*selection
        signals = signals.notnull().astype('int')
    
    if(param[0] == "long-short"):      
        if(param[1] == "smallest"):            
            long_selection = nvx.iloc[-1].nsmallest(param[2])
            short_selection = nvx.iloc[-1].nlargest(param[2])
            long_signals = ohlc[3].iloc[-1]*long_selection
            short_signals = ohlc[3].iloc[-1]*short_selection
            signals = long_signals.notnull().astype('int') - short_signals.notnull().astype('int')
        
        if(param[1] == "largest"):
            long_selection = nvx.iloc[-1].nlargest(param[2])
            short_selection = nvx.iloc[-1].nsmallest(param[2])
            long_signals = ohlc[3].iloc[-1]*long_selection
            short_signals = ohlc[3].iloc[-1]*short_selection
            signals = long_signals.notnull().astype('int') - short_signals.notnull().astype('int')
        
    return signals


def risk_management(portfolio,signals,ohlc,param):
##############################################
#
#   Calculates Target Allocation according to Risk Management Parameters
#   
#   portfolio
#   Portfolio Class Instance
#   portfolio.balance: Current Portfolio Balance
#   portfolio.positions: Current Portfolio Positions
#   
#   signals
#   Trading Signals (from get_signals())
#   
#   ohlc
#   List of Price Dataframes
#   ohlc[0]: Open 
#   ohlc[1]: High 
#   ohlc[2]: Low 
#   ohlc[3]: Close 
#
#   param
#   List of Risk Management Parameters
#   [param1]
#   param1:
#       'equal-weight': same target allocation for tickers with active signals
#       'vol-normed': volatility normed target allocation with higher allocation for tickers...
#                     ...with lower volatility and vice versa
#
#   Returns a Target Allocation for every Ticker   
#
##############################################

    if(param[0] == "equal-weight"):
        active_tickers = signals.astype(bool).sum()
        weights = signals/active_tickers
        
    if(param[0] == "vol-normed"):
        weights = vol_norming(signals,ohlc[3].iloc[-1])
    
    target_allocation =  portfolio.balance[-1]*weights/ohlc[3].iloc[-1]
    
    return target_allocation


def vol_norming(signals,ohlc):
##############################################
#
#   Calculate Target Allocation Weights that account for Volatility
#   (higher weights on tickers with lower volatility and vice versa)
#   
#   Exponentially Weighted Moving Average of Volatility over a certain Time Period
#   
#   ohlc
#   List of Price Dataframes
#   ohlc[0]: Open 
#   ohlc[1]: High 
#   ohlc[2]: Low 
#   ohlc[3]: Close 
#   
#   signals
#   Trading Signals (from get_signals())
#
#   Parameters for calculating the volatility:
#   ewma_init: time period in days to average volatility over
#   0.94: weight given to yesterdays volatility
#   0.06: weight given to yesterdays squared returns
#   
#   Returns weights for the target allocation for every ticker 
#
##############################################
    
    returns = ohlc[3].pct_change()
    ewma_init = 30
    ewma = signals*0
    if(returns.shape[0] >= ewma_init):
        ewma = signals*(returns.iloc[:ewma_init,:].std(axis=0)**2)
        for i in range(ewma_init+1,returns.shape[0]):
            ewma = 0.94*ewma.squeeze() + 0.06*((signals*returns.iloc[i,:].rename())**2).T.squeeze()
        ewma = (ewma.sum()/ewma).replace(np.inf, np.nan)
        ewma = ewma/ewma.sum()
    weights = ewma*signals
    
    return weights


def equalWeight(signals):
##############################################
#
#   Gives Equal Weight to Tickers with Active Signals
#
#   Returns Weights for target Allocation
#
##############################################
    active_tickers = signals.astype(bool).sum()
    
    return signals/active_tickers


def execute_target_allocation(portfolio,target_alloc,ohlc,spread):
##############################################
#
#   Executes Target Allocation and adds to / removes from the Portfolios Positions
#
#   portfolio
#   Portfolio Class Instance
#   portfolio.balance: Current Portfolio Balance
#   portfolio.positions: Current Portfolio Positions
#
#   target_alloc
#   Target Allocation for every Ticker
#
#   ohlc
#   List of Price Dataframes
#   ohlc[0]: Open 
#   ohlc[1]: High 
#   ohlc[2]: Low 
#   ohlc[3]: Close 
#
#   spread
#   Spread above/below market prices that has to be paid when executing trades
#   spread*price*trading_quantity gets subtracted from the portfolio balance
#
#   Returns Portfolio with updated Positions and Balance
#
##############################################
    
    deltaTrades = target_alloc - portfolio.positions
    
    # For Portfolio type of rebalancing: positions = target_alloc
    # For Trading type of executing (with exit_allocations in risk_management): 
    # positions += target_alloc
    portfolio.positions = target_alloc

    new_balance = portfolio.balance[-1] - abs((deltaTrades*ohlc[3].iloc[-1]*spread).sum())
    
    portfolio.balance.append(new_balance)
    
    return portfolio


def update_balance(portfolio,ohlc):
##############################################
#    
#   Updates Portfolio Balance when Prices change on the Next Day    
#    
#   Returns Portfolio with updates Balance
#
##############################################
    
    new_balance = portfolio.balance[-1] + (portfolio.positions*(
            ohlc[3].iloc[-1] - ohlc[3].iloc[ohlc[3].shape[0]-2])).sum()
    
    portfolio.balance[-1] = new_balance
    
    # Updated Balance gets appended later in the execute_target_allocation function    
    
    return portfolio



class Portfolio(object):
##############################################
#    
#   Portfolio Class
#    
#   self.balance: List with the current portfolio balance, which gets ...
#                 ...appended (updated) with update_balance()
#   self.positions: Pandas Series with Positions (Quantity) for every Ticker
#
##############################################
 
    def __init__(self, ohlc,tickers):
        self.balance = [100]
        data = [np.float(0) for ticker in tickers]
        self.positions = pd.Series(data=data, index=tickers, name=ohlc[3].iloc[0].name)
