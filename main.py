import pandas as pd
import os
import itertools
import numpy as np

## /INPUT PARMS
# name of the folder with bittrex data
markets_folder_path='Bittrex_data'
## INPUT PARMS/

## /FCN DEFS
def get_inside_files_path(folder_path):
    """
    Get a list of files in a folder, that has folder_path path.
    """
    inside_files_path_list=[folder_path+'/'+file for file in os.listdir(folder_path)]
    
    return inside_files_path_list

def get_market_file_paths(market,markets_folder_path):
    """
    Get list of paths of all files for a given market and path to data.
    :param market : name of market, for which the DF is built
    :param markets_folder_path : path to the main folder, where markets' data are stored

    :return market_file_path_list : list of zipped data file's paths 
    """
    market_folder_path=markets_folder_path+'/'+market
    market_month_folder_list=os.listdir(market_folder_path)
    market_month_folder_path_list=[market_folder_path+'/'+month for month in market_month_folder_list if not month.startswith(".")]
    market_file_path_list=list(itertools.chain.from_iterable([get_inside_files_path(month_folder_path) for month_folder_path in market_month_folder_path_list]))
    
    return market_file_path_list

def pandas_read_csv(file):
    """
    Tryes whether the data file is readable by Pandas.
    """
    try:
        df=pd.read_csv(file)
        return(df)
    except:
        print("The file "+file+' could not be loaded by Pandas.')
        pass
    
def concat_files_to_df(file_path_list):
    """
    Get a Pandas DataFrame, concatted of all files in a file_path_list. Also changes DF's unix time to datetime.
    """
    # load data to pandas DataFrame
    df_list=[pandas_read_csv(file) for file in file_path_list]
    df_clean_list=[x for x in df_list if not ((x is None) or (x.empty))]
    df=pd.concat(df_clean_list)
    # change unix to datetime
    df['date']=pd.to_datetime(df['date'],unit='ms')
    
    return df    

def get_market_daily_df(market,markets_folder_path):
    """
    Get a Pandas DataFrame, concatted of all files of given market and path to data.
    :param market : name of market, for which the DF is built
    :param markets_folder_path : path to the main folder, where markets' data are stored

    :return market_df : Pandas DataFrame, with columns: ['date', 'price_w_mean', 'market', 
    'price_maximum', 'pct_avg_price_change', 'pct_max_price_change']
    """
    print("Preparing "+market+' DataFrame...')
    
    # get market data file's paths
    market_file_path_list=get_market_file_paths(market,markets_folder_path)
    
    # get market orders df
    market_orders_df=concat_files_to_df(market_file_path_list)

    # groups DF by date & gets daily percent change of mean price
    times = market_orders_df['date']
    #market_df=pd.DataFrame(market_orders_df.groupby([times.dt.date]).price.mean())
    market_df=pd.DataFrame(market_orders_df.groupby([times.dt.date]).apply(lambda x: np.average(x.price, weights=x.amount)))
    market_df.columns=['price_w_mean']
    market_df['market']=market
    market_df['price_maximum']=pd.DataFrame(market_orders_df.groupby([times.dt.date]).apply(lambda x: max(x.price)))
    market_df['pct_avg_price_change']=market_orders_df.groupby([times.dt.date]).apply(lambda x: np.average(x.price, weights=x.amount)).pct_change()
    market_df['pct_max_price_change']=market_orders_df.groupby([times.dt.date]).apply(lambda x: max(x.price)).pct_change()
    # sets index to column
    market_df.reset_index(level=0, inplace=True)
    
    return market_df

def get_all_markets_daily_df(markets_folder_path,market_list='all'):
    """
    Get a Pandas DataFrame, concatted of all files for given path to data.
    :param markets_folder_path: path to the main folder, where markets' data are stored
    :param market_list: list of markets to be computed OR 'all' string
    
    :return market_df: Pandas DataFrame, with columns: ['date', 'price_w_mean', 'market', 
    'price_maximum', 'pct_avg_price_change', 'pct_max_price_change']
    """
    if (market_list=='all'):
        market_list=os.listdir(markets_folder_path)
    
    df=pd.concat([get_market_daily_df(market,markets_folder_path) for market in market_list if not market.startswith(".")])
    # reset index (concation duplicated them)
    df.reset_index(level=0,inplace=True)
    df.drop('index',axis=1,inplace=True)
    print('All markets successfuly loaded into a single df.')
    
    return(df)

def ups_downs_cnt(df,threshold_up,threshold_down):
    """
    Computes the number of ups/downs/else of maximas in the df.
    """
    ups_cnt=sum(df['pct_max_price_change']>threshold_up)
    stil_cnt=sum(df['pct_max_price_change']>threshold_up)
    still_cnt=sum((df['pct_max_price_change']<threshold_up)&(df['pct_max_price_change']>threshold_down))
    downs_cnt=sum(df['pct_max_price_change']<threshold_down)
    
    return ups_cnt,still_cnt,downs_cnt

## FCN DEFS/

# Gets all the data & transforms into a single Pandas DF & calculates 
# daily [maximas,weighted_avgs]
# for testing use subset of markets eg:
# df=get_all_markets_daily_df(markets_folder_path,['PTCBTC','LSKBTC'])
df=get_all_markets_daily_df(markets_folder_path,'all') 
# Saves for the web app to just load & read
df.to_csv('df.csv',index=False)


## /PLOT BUILDER
# loads data
df=pd.read_csv('df.csv')
diffs_df=pd.DataFrame(df.groupby('date').apply(lambda t: ups_downs_cnt(t,threshold_up=0.03,threshold_down=-0.03)))
diffs_df.reset_index(level=0,inplace=True)
diffs_df.columns=['date','changes']

import plotly.plotly as py
import plotly.graph_objs as go
from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly.graph_objs import *
import numpy as np
init_notebook_mode(connected=True)

trace1 = go.Bar(
    x=diffs_df['date'],  
    y=[x[2] for x in diffs_df['changes']],
    name='Downs'
)
trace2 = go.Bar(
    x=diffs_df['date'],
    y=[x[1] for x in diffs_df['changes']],
    name='Stills (± 3 %)'
)

trace3 = go.Bar(
    x=diffs_df['date'],
    y=[x[0] for x in diffs_df['changes']],
    name='Ups'
)

data = [trace1, trace2, trace3]
layout = go.Layout(
    title='Daily counts of coins\' maximas\' changes',
    xaxis=dict(
        title='Date'),
    yaxis=dict(
        title='Number of coins'), 
    barmode='stack'
)

fig = go.Figure(data=data, layout=layout)
iplot(fig, filename='stacked-bar')

## PLOT BUILDER/