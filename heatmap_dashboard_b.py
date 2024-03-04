# %% Import libraries
import pandas as pd
import csv
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import numpy as np

# Add root directory to sys.path to import ExtractModule
project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root_dir)
from Extract_module import ExtractModule, OrganizeData, extract_metadata_list

# %% Transform data and store in all_data_dict
"""
The following code is used to extract the data from the csv file and 
transform it into a format that can be used to create the heatmap and
spectrum plots. The data is then stored in a dictionary called all_data_dict.
"""

# csv_file = r"data_analysis\Co57_2mins_2000V_20cycles.xlsx"
csv_file = r"data\Co57_2mins_2000V_20cycles.csv"
# csv_file = r"data_analysis\Co57_2mins_2000V_20cycles_yaxis.csv"
EM = ExtractModule(csv_file)
df_transformed_list = EM.transform_all_df()
organized_data = OrganizeData(df_transformed_list, EM.csv_file)
all_data_dict = organized_data.all_data_dict
N_MODULES = EM.number_of_modules  # number of dataframes, used for slider
N_PIXELS_X = EM.n_pixels_x  # 11 pixels
N_PIXELS_Y = EM.n_pixels_y  # 11 pixels
x_positions = extract_metadata_list(csv_file, "Stage position x (in mm):")
y_positions = extract_metadata_list(csv_file, "Stage position y (in mm):")

del df_transformed_list  # delete the list of dataframes to save memory
del organized_data  # delete the organized_data object to save memory
del EM  # delete the ExtractModule object to save memory


def calculate_peak_count(array: np.array, peak_bin: int, peak_halfwidth=25):
    """Calculate the counts in a peak given the array and the peak bin number."""
    peak_count = np.sum(array[peak_bin - peak_halfwidth : peak_bin + peak_halfwidth])
    return peak_count


peak_bin = 224
peak_halfwidth = 25

for keys, values in all_data_dict.items():
    # print(f"{keys = }")
    df = values["df"]
    # create a new column for the peak count of each pixel
    df["peak_count"] = df["array_bins"].apply(
        lambda x: calculate_peak_count(x, peak_bin=peak_bin)
    )
    heatmap_peak_count = df.pivot_table(
        index="y_index", columns="x_index", values="peak_count"
    )
    all_data_dict[keys]["df"] = df
    all_data_dict[keys]["heatmap_peak"] = heatmap_peak_count


# %% functions to update the plots
def update_heatmap(test_counter, heatmap_type):
    stage_x = x_positions[test_counter]
    stage_y = y_positions[test_counter]

    heatmap_table = all_data_dict[test_counter]["heatmap_table"]

    if heatmap_type == "total_counts_normalized":
        # normalize heatmap
        max_pixel_value = heatmap_table.values.max()
        heatmap_table = (heatmap_table / max_pixel_value).round(3)

    title_string = f"""Stage X: {stage_x}, Stage Y: {stage_y}, 
    Sum all pixels: {all_data_dict[test_counter]['sum_total_counts']},
    Max count: {all_data_dict[test_counter]['max_total_counts']}"""
    heatmap_fig = px.imshow(
        heatmap_table,
        color_continuous_scale="viridis",
        text_auto=True,
        labels=dict(color="Value", x="X", y="Y"),
        title=title_string,
    )

    heatmap_fig.update_layout(
        xaxis=dict(title="X-index of Pixel"),
        yaxis=dict(title="Y-index of Pixel"),
        xaxis_nticks=12,
        yaxis_nticks=12,
        margin=dict(l=40, r=40, t=40, b=40),
        width=800,
        height=800,
    )
    return heatmap_fig


def add_peak_lines(fig, bin_peak, max_y, peak_halfwidth=25):
    fig.add_shape(
        type="line",
        x0=bin_peak,
        y0=0,
        x1=bin_peak,
        y1=max_y,
        line=dict(color="red", width=2),
        opacity=0.4,
    )
    fig.add_shape(
        type="line",
        x0=bin_peak - peak_halfwidth,
        y0=0,
        x1=bin_peak - peak_halfwidth,
        y1=max_y,
        line=dict(color="red", width=1, dash="dash"),
        opacity=0.5,
    )
    fig.add_shape(
        type="line",
        x0=bin_peak + peak_halfwidth,
        y0=0,
        x1=bin_peak + peak_halfwidth,
        y1=max_y,
        line=dict(color="red", width=1, dash="dash"),
        opacity=0.5,
    )
    return fig


def update_axis_range(fig, x_range, y_range):
    fig.update_xaxes(range=[min(x_range), max(x_range)])
    fig.update_yaxes(range=[min(y_range), max(y_range)])
    return fig


def update_heatmap_peak(test_counter, heatmap_type):
    stage_x = x_positions[test_counter]
    stage_y = y_positions[test_counter]

    heatmap_peak = all_data_dict[test_counter]["heatmap_peak"]

    if heatmap_type == "total_counts_normalized":
        # normalize heatmap
        max_pixel_value = heatmap_peak.values.max()
        heatmap_peak = (heatmap_peak / max_pixel_value).round(3)

    title_string = f"""Stage X: {stage_x}, Stage Y: {stage_y}, 
    Sum all pixels: {all_data_dict[test_counter]['sum_total_counts']},
    Max count: {all_data_dict[test_counter]['max_total_counts']}"""
    heatmap_fig = px.imshow(
        heatmap_peak,
        color_continuous_scale="viridis",
        text_auto=True,
        labels=dict(color="Value", x="X", y="Y"),
        title=title_string,
    )

    heatmap_fig.update_layout(
        xaxis=dict(title="X-index of Pixel"),
        yaxis=dict(title="Y-index of Pixel"),
        xaxis_nticks=12,
        yaxis_nticks=12,
        margin=dict(l=40, r=40, t=40, b=40),
        width=800,
        height=800,
    )
    return heatmap_fig


def update_spectrum_avg(test_counter, x_range, y_range):
    df = all_data_dict[test_counter]["df"]

    summed_array_bins = np.sum(df["array_bins"].values, axis=0)
    avg_array_bins = summed_array_bins / len(df)
    spectrum_avg_fig = go.Figure()
    spectrum_avg_fig.add_trace(
        go.Scatter(
            x=np.arange(1, len(avg_array_bins) + 1),
            y=avg_array_bins,
            mode="lines",
            name=f"Spectrum avg of all pixels",
        )
    )
    x_min = min(x_range)
    x_max = max(x_range)
    y_min = min(y_range)
    y_max = max(y_range)
    spectrum_avg_fig.update_xaxes(range=[x_min, x_max])
    spectrum_avg_fig.update_yaxes(range=[y_min, y_max])
    title_string = f"Avg all pixels, Avg total counts: {all_data_dict[test_counter]['avg_total_counts']}, Sum total counts: {all_data_dict[test_counter]['sum_total_counts']}"
    spectrum_avg_fig.update_layout(
        title=title_string,
        xaxis_title="Bins",
        yaxis_title="Counts",
        width=700,
        height=350,
    )

    spectrum_avg_fig = add_peak_lines(spectrum_avg_fig, peak_bin, max(avg_array_bins))

    return spectrum_avg_fig


def update_spectrum_pixel(test_counter, x_idx, y_idx, x_range, y_range):
    df = all_data_dict[test_counter]["df"]

    # filter of one pixel based on x and y index
    pixel_df = df[(df["x_index"] == x_idx) & (df["y_index"] == y_idx)]

    pixel_total_counts = pixel_df["total_counts"].values[0]

    pixel_peak_counts = pixel_df["peak_count"].values[0]

    spectrum_pixel = pixel_df["array_bins"].values[0]

    spectrum_pixel_fig = go.Figure()
    spectrum_pixel_fig.add_trace(
        go.Scatter(
            x=np.arange(1, len(spectrum_pixel) + 1),
            y=spectrum_pixel,
            mode="lines",
            name=f"Spectrum of pixel",
        )
    )
    x_min = min(x_range)
    x_max = max(x_range)
    y_min = min(y_range)
    y_max = max(y_range)
    spectrum_pixel_fig.update_xaxes(range=[x_min, x_max])
    spectrum_pixel_fig.update_yaxes(range=[y_min, y_max])
    title_string = f"Pixel (x={x_idx}, y={y_idx}), Total counts: {pixel_total_counts}, Peak counts: {pixel_peak_counts}"
    spectrum_pixel_fig.update_layout(
        title=title_string,
        xaxis_title="Bins",
        yaxis_title="Counts",
        width=700,
        height=350,
    )

    spectrum_pixel_fig = add_peak_lines(
        spectrum_pixel_fig, peak_bin, max(spectrum_pixel)
    )

    return spectrum_pixel_fig


# %% set up Dash app
app = dash.Dash(__name__)

# layout for heatmap & slider
app.layout = html.Div(
    [
        # heatmap type dropdown menu
        html.Div(
            [
                html.Label("Select Heatmap Type"),
                dcc.Dropdown(
                    id="heatmap-type-dropdown",
                    options=[
                        {"label": "Total Counts", "value": "total_counts"},
                        {
                            "label": "Total Counts Normalized",
                            "value": "total_counts_normalized",
                        },
                    ],
                    style={"width": "100%"},
                    value="total_counts",
                ),
            ],
            style={
                "display": "inline-block",
            },
        ),
        # container for the first two fixed heatmaps
        html.Div(
            [
                # first heatmap (cycle 1)
                html.Div(
                    [
                        html.H1("Background - No Source"),
                        dcc.Graph(
                            id="heatmap-plot-0",
                            figure=update_heatmap(0, "total_counts"),
                        ),
                    ],
                    style={"flex": 1},
                ),
                # second heatmap (cycle 2)
                html.Div(
                    [
                        html.H1("Source Exposure - No Mask"),
                        dcc.Graph(
                            id="heatmap-plot-1",
                            figure=update_heatmap(1, "total_counts"),
                        ),
                    ],
                    style={"flex": 1},
                ),
            ],
            style={
                "display": "flex",
                "flex-direction": "row",
                "justify-content": "space-between",
            },
        ),
        # container for the interactive heatmap with sliders and spectrum plots
        html.Div(
            [
                # container for interactive heatmap and its slider
                html.Div(
                    [
                        html.H1(
                            "Varying Mask Positions with Source Exposure",
                        ),
                        html.Div(
                            id="heatmap-container",
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
                                    value=2,  # start from the second heatmap
                                    marks={str(i): str(i) for i in range(0, N_MODULES)},
                                    step=1,
                                ),
                            ],
                            style={
                                "width": "80%",
                            },
                        ),
                    ],
                    style={"flex": 1, "margin-top": "150px"},
                ),
                # spectrum plots container -- per pixel and avg
                html.Div(
                    [
                        html.H1("Spectrum Plots"),
                        html.Div(id="spectrum-avg-container"),
                        html.Div(id="spectrum-pixel-graph2"),
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
                                            value=5,
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
                                            value=6,
                                            placeholder="Select Y Index",
                                        ),
                                    ],
                                    style={"display": "inline-block"},
                                ),
                                html.Div(id="spectrum-pixel-graph1"),
                            ],
                        ),
                        # bins range slider (x-axis)
                        html.Div(
                            [
                                html.Label("X"),
                                dcc.RangeSlider(
                                    min=0,
                                    max=1999,
                                    value=[1, 300],
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
                                    value=[0, 20],
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
    Output("heatmap-container", "children"),
    [
        Input("heatmap-slider", "value"),
        Input("heatmap-type-dropdown", "value"),
    ],  # Add dropdown menu value as input
)
def update_dynamic_heatmaps(slider_value, heatmap_type):
    heatmap_container = [
        dcc.Graph(
            id="heatmap-dynamic",
            style={
                "margin": "auto",
                "display": "block",
            },
            clickData=(
                {"points": [{"x": 5, "y": 7}]}
            ),
            # figure=update_heatmap(slider_value, heatmap_type),
            figure=update_heatmap_peak(slider_value, heatmap_type),
        )
    ]
    return heatmap_container


# spectrum plots callback function
@app.callback(
    [
        Output("spectrum-avg-container", "children"),
        # Output("spectrum-pixel-graph1", "children"),
        Output("spectrum-pixel-graph2", "children"),
    ],
    [
        Input("heatmap-slider", "value"),
        Input("x-index-dropdown", "value"),
        Input("y-index-dropdown", "value"),
        Input("x-axis-slider", "value"),
        Input("y-axis-slider", "value"),
    ],
)
def update_spectrum_plots(slider_value, x_idx, y_idx, x_range, y_range):
    avg_spectrum_container = [
        dcc.Graph(
            id=f"avg-spectrum",
            style={
                "display": "block",
                "width": "80%",
            },
            figure=update_spectrum_avg(slider_value, x_range, y_range),
        )
    ]

    spectrum_pixel_container2 = [
        dcc.Graph(
            id=f"spectrum-pixel",
            style={
                "display": "block",
                "width": "80%",
            },
            figure=update_spectrum_pixel(slider_value, x_idx, y_idx, x_range, y_range),
        )
    ]

    return avg_spectrum_container, spectrum_pixel_container2


@app.callback(
    Output("spectrum-pixel-graph1", "children"),
    [
        Input("heatmap-slider", "value"),
        Input("heatmap-dynamic", "clickData"),
        Input("x-axis-slider", "value"),
        Input("y-axis-slider", "value"),
    ],
)
def update_spectrum_pixel_graph(slider_value, clickData, x_range, y_range):
    # print(f"{clickData = }")
    x_index_click = clickData["points"][0]["x"]
    y_index_click = clickData["points"][0]["y"]
    print(f"{x_index_click = }, {y_index_click = }")

    spectrum_pixel_container1 = [
        dcc.Graph(
            id=f"spectrum-pixel-click",
            style={
                "display": "block",
                "width": "80%",
            },
            figure=update_spectrum_pixel(
                slider_value, x_index_click, y_index_click, x_range, y_range
            ),
        )
    ]

    return spectrum_pixel_container1


if __name__ == "__main__":
    app.run_server(
        port=8051,
        debug=True,
        use_reloader=True,
    )
