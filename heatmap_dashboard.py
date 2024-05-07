import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from data_handling_modules import (
    ExtractModule,
    TransformDf,
)
from plotting_modules import (
    create_spectrum_average,
    create_spectrum_pixel,
    create_pixelized_heatmap,
)

# csv_file = r"data_analysis\Co57_2mins_2000V_20cycles.csv"
csv_file = r"data\\Co57_2mins_2000V_20cycles_yaxis.csv"
EM = ExtractModule(csv_file)
extracted_df_list = EM.extract_all_modules2df()
TD = TransformDf()
df_transformed_list = TD.transform_all_df(extracted_df_list)

peak_bin = 224
peak_halfwidth = 50

TD.add_peak_counts_all(peak_bin, peak_halfwidth)

N_MODULES = EM.number_of_modules  # number of dataframes, used for slider
N_PIXELS_X = EM.n_pixels_x  # 11 pixels
N_PIXELS_Y = EM.n_pixels_y  # 11 pixels
x_positions = EM.extract_metadata_list(csv_file, "Stage position x (in mm):")
y_positions = EM.extract_metadata_list(csv_file, "Stage position y (in mm):")

peak_bin = 224
peak_halfwidth = 50

del EM, TD  # delete the original objects to free up memory


app_defaults = {
    "heatmap_type": "peak_count",
    "measurement_slider": 2,
    "click-x": 5,
    "click-y": 7,
    "dropdown-x": 5,
    "dropdown-y": 6,
    "x_range": [1, 350],
    "y_range": [0, 12],
}

app = dash.Dash(__name__)

# layout for heatmap & slider
app.layout = html.Div(
    [
        html.Div(  # container for the first two fixed heatmaps
            [
                # # container for the first two fixed heatmaps
                # html.Div(
                #     [
                #         # first heatmap (cycle 1)
                #         html.Div(
                #             [
                #                 html.H1("Background - No Source"),
                #                 dcc.Graph(
                #                     id="heatmap-plot-0",
                #                     figure=update_heatmap(0, "total_count"),
                #                 ),
                #             ],
                #             style={"flex": 1},
                #         ),
                #         # second heatmap (cycle 2)
                #         html.Div(
                #             [
                #                 html.H1("Source Exposure - No Mask"),
                #                 dcc.Graph(
                #                     id="heatmap-plot-1",
                #                     figure=update_heatmap(1, "total_count"),
                #                 ),
                #             ],
                #             style={"flex": 1},
                #         ),
                #     ],
                #     style={
                #         "display": "flex",
                #         "flex-direction": "row",
                #         "justify-content": "space-between",
                #     },
                # ),
            ]
        ),
        html.Div(
            [
                # container for interactive heatmap and its slider
                html.Div(
                    [
                        html.H1(
                            "Moving Mask Measurement",
                        ),
                        html.Div(  # Radio buttons for heatmap
                            [
                                dcc.RadioItems(
                                    id="count-type",
                                    options=[
                                        {
                                            "label": "Peak Count",
                                            "value": "peak_count",
                                        },
                                        {
                                            "label": "Total Count",
                                            "value": "total_count",
                                        },
                                        {
                                            "label": "Non-Peak Count",
                                            "value": "non_peak_count",
                                        },
                                        {"label": "Pixel ID", "value": "pixel_id"},
                                    ],
                                    value="peak_count",
                                    style={
                                        "display": "flex",
                                        "flex-direction": "column",
                                        "font-size": "20px",  # Adjust the font size as desired
                                        "margin-top": "20px",
                                        "margin-left": "20px",
                                        "margin-bottom": "20px",
                                    },
                                    # labelStyle={"display": "inline-block"},
                                ),
                                dcc.RadioItems(
                                    id="normalization-buttons",
                                    options=[
                                        {"label": "Raw Counts", "value": "raw"},
                                        {"label": "Normalized", "value": "normalized"},
                                    ],
                                    value="raw",
                                    style={
                                        "display": "flex",
                                        "flex-direction": "column",
                                        "font-size": "20px",  # Adjust the font size as desired
                                        "margin-top": "20px",
                                    },
                                ),
                                dcc.RadioItems(
                                    id="color-scale",
                                    options=[
                                        {"label": "Viridis", "value": "viridis"},
                                        {"label": "Plasma", "value": "plasma"},
                                        {"label": "Inferno", "value": "inferno"},
                                        {"label": "Jet", "value": "jet"},
                                    ],
                                    value="viridis",
                                    style={
                                        "display": "flex",
                                        "flex-direction": "column",
                                        "font-size": "20px",  # Adjust the font size as desired
                                        "margin-top": "20px",
                                        "margin-left": "20px",
                                    },
                                ),
                            ],
                            style={"display": "flex", "flex-direction": "row"},
                        ),  # End of radio buttons for heatmap
                        html.Div(
                            [
                                dcc.Graph(
                                    id="heatmap-dynamic-figure",
                                    clickData=(
                                        {
                                            "points": [
                                                {
                                                    "x": app_defaults["click-x"],
                                                    "y": app_defaults["click-y"],
                                                }
                                            ]
                                        }
                                    ),
                                )
                            ],
                            id="heatmap-dynamic-container",
                            style={
                                "width": "80%",
                                "margin-top": "20px",
                            },
                        ),
                        # slider for rest of the heatmaps
                        html.Div(
                            [
                                html.Label("Measurement Slider"),
                                dcc.Slider(
                                    id="heatmap-slider",
                                    min=0,
                                    max=N_MODULES - 1,
                                    value=app_defaults[
                                        "measurement_slider"
                                    ],  # start from the second heatmap
                                    marks={str(i): str(i) for i in range(0, N_MODULES)},
                                    step=1,
                                ),
                            ],
                            style={
                                "width": "80%",
                            },
                        ),
                    ],
                    style={"flex": 1, "margin-top": "100px", "margin-left": "40px"},
                ),
                # spectrum plots container -- per pixel and avg
                html.Div(
                    [
                        html.H1("Spectrum Plots"),
                        html.Div(
                            [dcc.Graph(id="spectrum-avg-figure")],
                            id="spectrum-avg-container",
                        ),
                        html.Div(
                            [dcc.Graph(id="spectrum-pixel-1-figure")],
                            id="spectrum-pixel-1-container",
                        ),
                        # container for the spectrum of pixel plot -- includes dropdown menus
                        html.Div(
                            [
                                # x-index dropdown
                                html.Div(
                                    [
                                        html.Label("Select X Index"),
                                        dcc.Dropdown(
                                            id="x-index-dropdown",
                                            options=[
                                                {"label": str(i), "value": i}
                                                for i in range(1, N_PIXELS_X + 1)
                                            ],
                                            style={
                                                "width": "100%",
                                                "display": "inline-block",
                                            },
                                            value=app_defaults["dropdown-x"],
                                            placeholder="Select X Index",
                                        ),
                                    ],
                                    style={
                                        "display": "inline-block",
                                        "padding-right": "20px",
                                    },
                                ),
                                # y-index dropdown
                                html.Div(
                                    [
                                        html.Label("Select Y Index"),
                                        dcc.Dropdown(
                                            id="y-index-dropdown",
                                            options=[
                                                {"label": str(i), "value": i}
                                                for i in range(1, N_PIXELS_Y + 1)
                                            ],
                                            style={
                                                "width": "100%",
                                                "display": "inline-block",
                                            },
                                            value=app_defaults["dropdown-y"],
                                            placeholder="Select Y Index",
                                        ),
                                    ],
                                    style={"display": "inline-block"},
                                ),
                                html.Div(
                                    [dcc.Graph(id="spectrum-pixel-2-figure")],
                                    id="spectrum-pixel-2-container",
                                ),
                            ],
                        ),
                        # bins range slider (x-axis)
                        html.Div(
                            [
                                html.Label("X"),
                                dcc.RangeSlider(
                                    min=1,
                                    max=1999,
                                    value=app_defaults["x_range"],
                                    id="x-axis-slider",
                                ),
                            ],
                            style={
                                "width": "70%",
                            },
                        ),
                        # counts range slider (y-axis)
                        html.Div(
                            [
                                html.Label("Y"),
                                dcc.RangeSlider(
                                    min=0,
                                    max=20,
                                    value=app_defaults["y_range"],
                                    id="y-axis-slider",
                                ),
                            ],
                            style={
                                "width": "70%",
                            },
                        ),
                    ],
                    style={"width": "100%", "flex": 1},
                ),
            ],
            style={
                "display": "flex",
                "flex-direction": "row",
            },
        ),
    ]
)


# callback function for heatmaps based on slider and dropdown menu
@app.callback(
    Output("heatmap-dynamic-figure", "figure"),
    [
        Input("heatmap-slider", "value"),
        Input("count-type", "value"),
        Input("normalization-buttons", "value"),
        Input("color-scale", "value"),
    ],  # Add dropdown menu value as input
)
def update_dynamic_heatmaps(slider_value, count_type, normalization, color_scale):
    df = df_transformed_list[slider_value]

    return create_pixelized_heatmap(df, count_type, normalization, color_scale)


@app.callback(
    Output("spectrum-avg-figure", "figure"),
    [
        Input("heatmap-slider", "value"),
        Input("x-axis-slider", "value"),
        Input("y-axis-slider", "value"),
    ],
)
def update_spectrum_avg_callback(slider_value, x_range, y_range):
    df = df_transformed_list[slider_value]
    return create_spectrum_average(df, bin_peak=peak_bin, x_range=x_range, y_range=y_range)


@app.callback(
    Output("spectrum-pixel-1-figure", "figure"),
    [
        Input("heatmap-slider", "value"),
        Input("x-index-dropdown", "value"),
        Input("y-index-dropdown", "value"),
        Input("x-axis-slider", "value"),
        Input("y-axis-slider", "value"),
    ],
)
def update_spectrum_pixel_callback(slider_value, x_index, y_index, x_range, y_range):
    df = df_transformed_list[slider_value]
    return create_spectrum_pixel(df, (x_index, y_index), 
                              bin_peak=peak_bin, 
                              x_range=x_range, 
                              y_range=y_range)


@app.callback(
    Output("spectrum-pixel-2-figure", "figure"),
    [
        Input("heatmap-slider", "value"),
        Input("heatmap-dynamic-figure", "clickData"),
        Input("x-axis-slider", "value"),
        Input("y-axis-slider", "value"),
    ],
)
def update_spectrum_pixel_graph(slider_value, clickData, x_range, y_range):
    x_index_click = clickData["points"][0]["x"]
    y_index_click = clickData["points"][0]["y"]
    # print(f"{x_index_click = }, {y_index_click = }")
    df = df_transformed_list[slider_value]

    return create_spectrum_pixel(df, (x_index_click, y_index_click), 
                                        bin_peak=peak_bin, 
                                        x_range=x_range, 
                                        y_range=y_range)

# @app.callback(
#     [
#         Output("x-axis-slider", "max"),
#         Output("y-axis-slider", "max"),
#         Output("x-axis-slider", "value"),
#         Output("y-axis-slider", "value"),
#     ],
#     [Input("heatmap-slider", "value")],
# )
# def update_slider_max(slider_value):
#     df = df_transformed_list[slider_value]
#     avg_array_bins = np.sum(df["array_bins"].values, axis=0) / len(df)
#     x_range = [0, len(avg_array_bins)]
#     y_range = [0, int(avg_array_bins.max() * 1.5)]

#     return max(x_range), max(y_range), x_range, y_range


if __name__ == "__main__":
    app.run_server(debug=True, port=8057, use_reloader=True)
