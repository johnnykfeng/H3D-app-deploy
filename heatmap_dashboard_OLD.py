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
from Extract_module import (
    ExtractModule,
    TransformDf,
    OrganizeData,
    extract_metadata_list,
)

# csv_file = r"data_analysis\Co57_2mins_2000V_20cycles.csv"
csv_file = r"data\\Co57_2mins_2000V_20cycles_yaxis.csv"
EM = ExtractModule(csv_file)
extracted_df_list = EM.extract_all_modules2df()
# df_transformed_list = EM.transform_all_df()
TD = TransformDf()
TD.transform_all_df(extracted_df_list)

peak_bin = 224
peak_halfwidth = 50

TD.add_peak_counts_all(peak_bin, peak_halfwidth)

OD = OrganizeData(TD.df_transformed_list, EM.csv_file, include_peak_count=True)
all_data_dict = OD.all_data_dict
N_MODULES = EM.number_of_modules  # number of dataframes, used for slider
N_PIXELS_X = EM.n_pixels_x  # 11 pixels
N_PIXELS_Y = EM.n_pixels_y  # 11 pixels
x_positions = extract_metadata_list(csv_file, "Stage position x (in mm):")
y_positions = extract_metadata_list(csv_file, "Stage position y (in mm):")

peak_bin = 224
peak_halfwidth = 50

del EM, TD, OD  # delete the original objects to free up memory


def update_heatmap(counter, heatmap_type, normalization="raw", color_scale="viridis"):
    stage_x = x_positions[counter]
    stage_y = y_positions[counter]

    if heatmap_type == "total_counts":
        heatmap_table = all_data_dict[counter]["heatmap_table"]
    elif heatmap_type == "peak_counts":
        heatmap_table = all_data_dict[counter]["heatmap_peak"]
    elif heatmap_type == "non_peak_counts":
        heatmap_table = all_data_dict[counter]["heatmap_non_peak"]
    elif heatmap_type == "pixel_id":
        heatmap_table = all_data_dict[counter]["pixel_id_map"]
    else:
        heatmap_table = all_data_dict[counter]["heatmap_peak"]

    if normalization == "normalized":
        max_pixel_value = heatmap_table.values.max()
        heatmap_table = (heatmap_table / max_pixel_value).round(2)

    title_string = f"""Stage X: {stage_x}, Stage Y: {stage_y}, 
    Sum all pixels: {all_data_dict[counter]['sum_total_counts']},
    Max count: {all_data_dict[counter]['max_total_counts']}"""
    heatmap_fig = px.imshow(
        heatmap_table,
        color_continuous_scale=color_scale,
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


def add_peak_lines(fig, bin_peak, max_y, peak_halfwidth=peak_halfwidth):
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


def update_spectrum_avg(counter, x_range, y_range):
    df = all_data_dict[counter]["df"]

    summed_array_bins = np.sum(df["array_bins"].values, axis=0)
    avg_array_bins = summed_array_bins / len(df)
    spectrum_avg_fig = go.Figure()
    spectrum_avg_fig.add_trace(
        go.Scatter(
            x=np.arange(1, len(avg_array_bins) + 1),
            y=avg_array_bins,
            mode="lines",
            name="Spectrum avg of all pixels",
        )
    )

    spectrum_avg_fig.update_xaxes(range=[x_range[0], x_range[-1]])
    spectrum_avg_fig.update_yaxes(range=[y_range[0], y_range[-1]])
    title_string = f"""Avg all pixels, Avg total counts: {all_data_dict[counter]['avg_total_counts']}, 
Avg peak counts: {all_data_dict[counter]['avg_peak_counts']}"""
    spectrum_avg_fig.update_layout(
        title=title_string,
        xaxis_title="Bins",
        yaxis_title="Counts",
        width=700,
        height=350,
    )

    spectrum_avg_fig = add_peak_lines(spectrum_avg_fig, peak_bin, max(avg_array_bins))

    return spectrum_avg_fig


def update_spectrum_pixel(counter, x_idx, y_idx, x_range, y_range):
    df = all_data_dict[counter]["df"]

    # filter of one pixel based on x and y index
    pixel_df = df[(df["x_index"] == x_idx) & (df["y_index"] == y_idx)]

    pixel_total_counts = pixel_df["total_count"].values[0]

    pixel_peak_counts = pixel_df["peak_count"].values[0]

    spectrum_pixel = pixel_df["array_bins"].values[0]

    spectrum_pixel_fig = go.Figure()
    spectrum_pixel_fig.add_trace(
        go.Scatter(
            x=np.arange(1, len(spectrum_pixel) + 1),
            y=spectrum_pixel,
            mode="lines",
            name="Spectrum of pixel",
        )
    )

    spectrum_pixel_fig.update_xaxes(range=[x_range[0], x_range[-1]])
    spectrum_pixel_fig.update_yaxes(range=[y_range[0], y_range[-1]])
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
                                            "label": "Peak Counts",
                                            "value": "peak_counts",
                                        },
                                        {
                                            "label": "Total Counts",
                                            "value": "total_counts",
                                        },
                                        {
                                            "label": "Non-Peak Counts",
                                            "value": "non_peak_counts",
                                        },
                                        {"label": "Pixel ID", "value": "pixel_id"},
                                    ],
                                    value="peak_counts",
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
    return update_heatmap(slider_value, count_type, normalization, color_scale)


@app.callback(
    Output("spectrum-avg-figure", "figure"),
    [
        Input("heatmap-slider", "value"),
        Input("x-axis-slider", "value"),
        Input("y-axis-slider", "value"),
    ],
)
def update_spectrum_avg_callback(slider_value, x_range, y_range):
    return update_spectrum_avg(slider_value, x_range, y_range)


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
    return update_spectrum_pixel(slider_value, x_index, y_index, x_range, y_range)


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
    print(f"{x_index_click = }, {y_index_click = }")
    return update_spectrum_pixel(
        slider_value, x_index_click, y_index_click, x_range, y_range
    )


if __name__ == "__main__":
    app.run_server(debug=True, port=8057, use_reloader=True)