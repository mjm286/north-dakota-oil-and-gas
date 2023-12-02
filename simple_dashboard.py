import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import os
import glob
import pickle

# load oil and well data
oil = pd.read_pickle("North_Dakota_Well_Production_Data_2015_2023.pickle")
oil = oil.reset_index(drop=True)
api_data = pd.read_csv('api_lateral_length.csv')
api_data = api_data.reset_index(drop=True)
api_data.api_wellno = api_data.api_wellno/10
data = pd.merge(oil, api_data, on='api_wellno', how='left')
data["ground_level_elevation"] = data["ground_level_evelation"]
data = data.drop("ground_level_evelation", axis=1)
data = data.dropna(subset=['company'])
data = data.query('oil_per_day!=0')

# print(data.company.unique())



# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app*
app.layout = html.Div([
    html.H1("North Dakota Oil and Gas Dashboard"),
    
    html.H3("Select Years"),
    dcc.RadioItems(
        id="year-button",
        options=[
            {'label': year, 'value': year} for year in ["All Years", 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
        ],
        value=2023,
        inline=True,
    ),

    html.H2("State Totals"),

    html.Div([
        dcc.Graph(id="total-oil-production"),
        dcc.Graph(id="total-gas-production"),
        dcc.Graph(id="total-operating-wells"),
    ], style={"columnCount":3}),

    html.H3("Company Dropdown Menu"),
    # Dropdown menu for selecting company
    dcc.Dropdown(
        id='company-dropdown',
        options=[
            {'label': company, 'value': company} for company in sorted(data['company'].unique())
        ],
        value='CHORD ENERGY',  # Default selected company
        searchable=True,
        style={'width': '75%'}
    ),
    
    # Graph to display data based on the selected company
    html.Div([
        dcc.Graph(id='company-graph-wells'),
        dcc.Graph(id='company-graph-oil'),
        dcc.Graph(id='company-graph-gas'),
    ], style={"columnCount":3}),
    
    html.Div([
        dcc.Graph(id='company-graph-total-boed'),
        dcc.Graph(id='company-graph-true-vertical-depth'),
        dcc.Graph(id='company-graph-lateral-length'),
    ], style={"columnCount":3}),
], style={
        'backgroundColor': '#f2f2f2',  # Set the background color to a desired color code
        'padding': '20px'  # Add some paddi)
        })

@app.callback(
    [Output('company-dropdown', 'options')],
    #  Output('company-dropdown', 'value')],
    [Input('year-button', 'value')]
)

def update_dropdown(selected_radio):
    print(f"updated dropdown {selected_radio}")
    if selected_radio == 'All Years':
        options=[
            {'label': company, 'value': company} for company in sorted(data['company'].unique())
        ],
        # value='CHORD ENERGY'  # Default selected company
    else:
        filtered_year_data = data.query('year==@selected_radio')
        print(filtered_year_data)
        options=[
            {'label': company, 'value': company} for company in sorted(filtered_year_data['company'].unique())
        ],
        # value='CHORD ENERGY'  # Default selected company
    # print(value)
    return options#, value


@app.callback(
    [Output("total-oil-production", 'figure'),
     Output("total-gas-production", 'figure'),
     Output("total-operating-wells", 'figure')],
    [Input('year-button', 'value')]
)

def update_total_metrics_oil(year):
    if year == "All Years":
        year = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    # print(year)
    filtered_year = data.query('year==@year')
    production_mean = filtered_year.groupby(["year", "month"]).agg(
        {"api_wellno":"count","oil_per_day":"sum","gas_per_day":"sum"}).reset_index()
    
    production_mean = production_mean.rename(columns={"api_wellno":"wells_producing",
                                                      "oil_per_day":"bbl/day",
                                                      "gas_per_day":"scm/day"})
    

    
    fig1 = px.line(production_mean, x="month", y="bbl/day",
                   color="year", markers=True, labels={"year":"Year"}
                   )
    
    fig1.update_layout(
        title="Oil Production",
        title_x=0.5,
        xaxis_title='Month',
        yaxis_title='bbl/day',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig1.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    fig2 = px.line(production_mean, x="month", y="scm/day",
                   color="year", markers=True, labels={"year":"Year"}
                   )
    
    fig2.update_layout(
        title="Gas Production",
        title_x=0.5,
        xaxis_title='Month',
        yaxis_title='scm/day',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig2.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    fig3 = px.line(production_mean, x="month", y="wells_producing",
                   color="year", markers=True, labels={"year":"Year"}
                   )
    
    fig3.update_layout(
        title="Number of Producing Wells",
        title_x=0.5,
        xaxis_title='Month',
        yaxis_title='Number of Producing Wells',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig3.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    
    return fig1, fig2, fig3


# Define callback to update the graph based on the selected category
@app.callback(
    [Output('company-graph-wells', 'figure'),
     Output('company-graph-oil', 'figure'),
     Output('company-graph-gas', 'figure'),
     Output('company-graph-total-boed', 'figure'),
     Output('company-graph-true-vertical-depth', 'figure'),
     Output('company-graph-lateral-length', 'figure')],
    [Input('company-dropdown', 'value'),
     Input('year-button', 'value')]
)

def update_graph_oil(selected_company, year):
    if year == "All Years":
        year = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    filtered_company = data[data['company'] == selected_company]
    filtered_year = data.query('year==@year')
    filtered_year = filtered_year.query('company==@selected_company')
    production_mean = filtered_year.groupby(["company","year", "month"]).agg(
        {"api_wellno":"count","oil_per_day":"sum","gas_per_day":"sum"}).reset_index()
    
    production_mean = production_mean.rename(columns={"api_wellno":"wells_producing",
                                                      "oil_per_day":"bbl/day",
                                                      "gas_per_day":"scm/day"})
    

    # production_mean["company_colors"] = ["#990000" if color==selected_company else "#999999" for color in production_mean["company"]]
    fig1 = px.line(production_mean, x="month", y="wells_producing",
                   color="year", markers=True, labels={"year":"Year"}
                   )
    
    fig1.update_layout(
        title="Number of Producing Wells",
        title_x=0.5,
        xaxis_title='Month',
        yaxis_title='Number of Producing Wells',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig1.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    
    fig2 = px.line(production_mean, x="month", y="bbl/day",
                   color="year", markers=True, labels={"year":"Year"},
                   hover_data={"bbl/day":":.2f"}
                   )
    
    fig2.update_layout(
        title="Oil Production",
        title_x = 0.5,
        xaxis_title='Month',
        yaxis_title='bbl/day',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig2.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    
    fig3 = px.line(production_mean, x="month", y="scm/day",
                   color="year", markers=True, labels={"year":"Year"},
                   hover_data={"scm/day":":.2f"}
                   )
    
    fig3.update_layout(
        title="Gas Production",
        title_x = 0.5,
        xaxis_title='Month',
        yaxis_title='scm/day',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig3.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    
    fig4 = px.line(production_mean, x="month", y="scm/day",
                   color="year", markers=True, labels={"year":"Year"},
                   hover_data={"scm/day":":.2f"}
                   )
    
    fig4.update_layout(
        title="Gas Production",
        title_x = 0.5,
        xaxis_title='Month',
        yaxis_title='scm/day',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig4.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    
    fig5 = px.line(production_mean, x="month", y="scm/day",
                   color="year", markers=True, labels={"year":"Year"},
                   hover_data={"scm/day":":.2f"}
                   )
    
    fig5.update_layout(
        title="Gas Production",
        title_x = 0.5,
        xaxis_title='Month',
        yaxis_title='scm/day',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig5.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    
    fig6 = px.line(production_mean, x="month", y="scm/day",
                   color="year", markers=True, labels={"year":"Year"},
                   hover_data={"scm/day":":.2f"}
                   )
    
    fig6.update_layout(
        title="Gas Production",
        title_x = 0.5,
        xaxis_title='Month',
        yaxis_title='scm/day',
        template='plotly_white',  # You can experiment with different Plotly templates
        margin=dict(l=0, r=0, b=0, t=100)),  # Adjust the margin as needed

    fig6.update_xaxes(
        tickvals=[month for month in production_mean.month.unique()])    # ticktext=custom_ticks,
    
    return fig1, fig2, fig3, fig4, fig5, fig6

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
