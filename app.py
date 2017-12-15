# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly.graph_objs import *



## /FCN DEFS (should be loaded from a module)
def ups_downs_cnt(df,threshold_up,threshold_down):
    ups_cnt=sum(df['pct_max_price_change']>threshold_up)
    stil_cnt=sum(df['pct_max_price_change']>threshold_up)
    still_cnt=sum((df['pct_max_price_change']<threshold_up)&(df['pct_max_price_change']>threshold_down))
    downs_cnt=sum(df['pct_max_price_change']<threshold_down)
    
    return ups_cnt,still_cnt,downs_cnt
## FCN DEFS/

# loads data
try:
    df=pd.read_csv('df.csv')
except:
    exit("Error: the DataFrame could not be loaded. Pleas make sure that you have run the main.py script which generated df.csv file!")
diffs_df=pd.DataFrame(df.groupby('date').apply(lambda t: ups_downs_cnt(t,threshold_up=0.03,threshold_down=-0.03)))
diffs_df.reset_index(level=0,inplace=True)
diffs_df.columns=['date','changes']

# set colour
colors = {
    'background': '#ffffff',
    'text':'#03070f'
}

app = dash.Dash()
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

# set app layout
app.layout = html.Div(style={'backgroundColor': colors['background']},children=[
    html.Div([
        html.H1(
            children='Hello Dash',
            style={
                'textAlign': 'center',
                'color': colors['text']
            }
        ),

        html.Div(children='A Proof Of Concept Dash - App.', style={
            'textAlign': 'center',
            'color': colors['text']
        })

        
    ]),
    dcc.Dropdown(
        id='stock-ticker-input',
        options=[{'label': s, 'value': s}
                 for s in ['ALL MARKETS']+list(pd.unique(df['market']))],
        value=['ALL MARKETS'],
        multi=True
    ),
    html.Div(id='fig')
    ]

)

# create reactive DataFrame & plot
@app.callback(
    dash.dependencies.Output('fig','children'),
    [dash.dependencies.Input('stock-ticker-input', 'value')])
def update_df(tickers):
    # loads data
    df=pd.read_csv('df.csv')
    if ('ALL MARKETS' not in tickers):
        df=df[df['market'].isin(tickers)]
    diffs_df=pd.DataFrame(df.groupby('date').apply(lambda t: ups_downs_cnt(t,threshold_up=0.03,threshold_down=-0.03)))
    diffs_df.reset_index(level=0,inplace=True)
    diffs_df.columns=['date','changes']

    # set clour
    colors = {
        'background': '#ffffff',
        'text':'#03070f'
    }

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
        xaxis=dict(title='Date'),
        yaxis=dict(title='Number of coins'),         
        barmode='stack',
        plot_bgcolor= colors['background'],
        paper_bgcolor= colors['background']
    )

    fig = dcc.Graph(
            id='example-graph',
            figure=go.Figure(data=data, layout=layout)
        )

    return fig

# run server
if __name__ == '__main__':
    app.run_server(debug=True)

