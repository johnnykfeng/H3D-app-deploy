import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Tab 1', value='tab-1'),
        dcc.Tab(label='app_readme.md', value='tab-2'),
    ]),
    html.Div(id='tab-content')
])

@app.callback(Output('tab-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H3('Tab 1 content'),
            dcc.Graph(
                id='graph-1',
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'Tab 1'},
                    ],
                    'layout': {
                        'title': 'Tab 1 Graph'
                    }
                }
            )
        ])
    elif tab == 'tab-2':
        with open('app_readme.md', 'r') as file:
            markdown_content = file.read()
        return html.Div([
            html.H3('Tab 2 content'),
            dcc.Markdown(children=markdown_content)
        ])

if __name__ == '__main__':
    app.run_server(debug=True)
