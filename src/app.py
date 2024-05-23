import dash
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import geopandas as gpd
import json

# Sample DataFrame
df = pd.read_csv("merged_df.csv")
df1 = df.groupby(['Year','Peak'])[['TTI','PTI','BTI','Severity','Variability']].mean().reset_index()

# read geojson
with open('t6ej_final.geojson') as response:
    gdf = json.load(response)

# create id var
i=1
for feature in gdf["features"]:
    feature ['id'] = str(i).zfill(2)
    i += 1

# create df
dff = gpd.read_file("t6ej_final.geojson")
dff = pd.DataFrame(dff)

# reformat
dff['Poverty'] = dff['Poverty'].astype('int')
dff['Disabled'] = dff['Disabled'].astype('int')
dff['Foreigner'] = dff['Foreigner'].astype('int')

# Initialize the Dash app
app = dash.Dash(__name__,suppress_callback_exceptions=True)
server = app.server

# Navbar layout
navbar = html.Nav([
    dcc.Link('Trend', href='/line-plot'),
    html.Span(' | '),
    dcc.Link('Congestion', href='/grouped-bar-chart'),
    html.Span(' | '),
    dcc.Link('Impact', href='/scatter-chart'),
    html.Span(' | '),
    dcc.Link('Equity', href='/map-chart')
])

# Define callbacks
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/line-plot':
        return line_plot_layout
    elif pathname == '/grouped-bar-chart':
        return grouped_bar_chart_layout
    elif pathname == '/scatter-chart':
        return scatter_chart_layout
    elif pathname == '/map-chart':
        return map_layout
    else:
        return line_plot_layout

# Line plot layout
line_plot_layout = html.Div([
    html.H1('Congestion Trend by Peak Period'),
    dcc.Dropdown(
        id='line-dropdown',
        options=[
            {'label': 'TTI', 'value': 'TTI'},
            {'label': 'PTI', 'value': 'PTI'},
            {'label': 'BTI', 'value': 'BTI'}
        ],
        value='TTI'
    ),
    dcc.Graph(id='line-plot')
])

# Grouped bar chart layout
grouped_bar_chart_layout = html.Div([
    html.H1('Levels of Congestion by Peak Period'),
    dcc.Dropdown(
        id='bar-dropdown',
        options=[
            {'label': '2018', 'value': 2018},
            {'label': '2019', 'value': 2019},
            {'label': '2020', 'value': 2020}
        ],
        value=2018
    ),
    dcc.Graph(id='bar-chart')
])

# scatter chart layout
scatter_chart_layout = html.Div([
    html.H1('Relationship between Congestion and Impact'),
    dcc.Dropdown(
        id='Impact',
        options=[{'label': i, 'value': i} for i in ['Severity', 'Variability']],
        value='Severity'),
    dcc.Dropdown(
        id='Congestion',
        options=[{'label': i, 'value': i} for i in ['TTI', 'PTI', 'BTI']],
        value='TTI'),
    dcc.Graph(id='scatter-chart')
])

# map layout
map_layout = html.Div([
    html.H1('Equity Population Distribution'),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': year, 'value': year} for year in dff['year'].unique()],
        value=2013),
    dcc.Dropdown(
        id='category-dropdown',
        options=[{'label': 'Poverty', 'value': 'Poverty'}, 
                 {'label': 'Disabled', 'value': 'Disabled'}, 
                 {'label': 'Foreigner', 'value': 'Foreigner'}],
        value='Poverty'),
    dcc.Graph(id='choropleth-map')
])

# App layout
app.layout = html.Div([
    navbar,
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Define callbacks for updating plots
@app.callback(
    Output('line-plot', 'figure'),
    [Input('line-dropdown', 'value')]
)
def update_line_plot(selected_value):
    fig = px.line(df1, x='Year', y=selected_value, color='Peak')
    fig.update_layout(xaxis=dict(tickmode='linear'),plot_bgcolor='white')
    return fig

@app.callback(
    Output('bar-chart', 'figure'),
    [Input('bar-dropdown', 'value')]
)
def update_bar_chart(selected_year):
    filtered_df = df1[df1['Year'] == selected_year]
    fig = px.bar(filtered_df, x=['TTI', 'PTI', 'BTI'], y='Peak', barmode='group')
    fig.update_layout(plot_bgcolor='white')
    return fig

@app.callback(
    Output('scatter-chart', 'figure'),
    [Input('Impact', 'value'),
     Input('Congestion', 'value')]
)
def update_scatter_plot(selected_dropdown1, selected_dropdown2):
    fig = px.scatter(df, x=df[selected_dropdown1], y=df[selected_dropdown2], color=df['Peak'], 
                     labels={selected_dropdown1: selected_dropdown1, selected_dropdown2: selected_dropdown2})
    fig.update_layout(title=f'Scatter Plot of {selected_dropdown1} vs {selected_dropdown2}',plot_bgcolor='white')
    return fig
@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('category-dropdown', 'value')]
)
def update_map(year, category):
    filtered_dff = dff[dff['year'] == year]
    fig = px.choropleth(
        filtered_dff, geojson=gdf, color=category, color_discrete_sequence= px.colors.sequential.Plasma_r,
        locations="GEOID", featureidkey="properties.GEOID", projection="mercator")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_traces(marker_line_width=0)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
