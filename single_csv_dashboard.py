import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add root directory to sys.path to import ExtractModule
project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root_dir)
from Extract_module import ExtractModule
import os
from icecream import ic
from spectrum_peak_finder import PeakFinder


def find_csv_files(directory):
    """Find all CSV files in the given directory and its subdirectories"""
    csv_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    return csv_files


directory = r"data/leaky_pixel_data"
csv_files = find_csv_files(directory)
ic(csv_files)


def calculate_peak_count(array: np.array, peak_bin: int, peak_halfwidth=25):
    """Calculate the counts in a peak given the array and the peak bin number."""
    peak_count = np.sum(array[peak_bin - peak_halfwidth : peak_bin + peak_halfwidth])
    return peak_count


def extract_csv2df(csv_file, module_number=0):
    # ic(csv_file)
    filename = os.path.basename(csv_file)
    # ic(filename)
    filename_no_ext = os.path.splitext(filename)[0]
    # ic(filename_no_ext)

    EM = ExtractModule(csv_file)
    if csv_file.endswith("14892_M010710_20240208-1449__testresults.csv"):
        # only this csv file has "Pixel" as header
        EM.target_string = "Pixel"
    else:
        EM.target_string = "H3D_Pixel"

    df = EM.extract_module2df(module_number=module_number)
    df = EM.transform_df(df)

    max_count_value = df["array_bins"].apply(lambda x: max(x)).max()
    avg_array_bins = df["array_bins"].sum(axis=0) / 121

    if "Cs137" in filename_no_ext:
        # ic("Cs137 data")
        if "Co57" in filename_no_ext:
            PF = PeakFinder(avg_array_bins, source="co57")
            # bin_peak = PF.find_peaks_scipy()
            bin_peak = PF.find_max_bin()
            starting_x_range = [0, 1999]
        else:
            ic("Cs137 data")
            PF = PeakFinder(avg_array_bins, source="cs137")
            PF.source_peak_bins["cs137"] = 1395
            # bin_peak = PF.find_peaks_scipy()
            bin_peak = PF.find_max_bin()
            starting_x_range = [0, 1499]

        df["peak_count"] = df["array_bins"].apply(
            lambda x: calculate_peak_count(x, bin_peak)
        )
        starting_y_range = [0, max_count_value]

    elif "Am241" in filename_no_ext:
        # ic("Am241 data")
        PF = PeakFinder(avg_array_bins, source="am241")
        PF.source_peak_bins["am241"] = 75
        # bin_peak = PF.find_peaks_scipy()
        bin_peak = PF.find_max_bin()
        # bin_peak = 90
        df["peak_count"] = df["array_bins"].apply(
            lambda x: calculate_peak_count(x, bin_peak)
        )
        starting_x_range = [0, 199]
        starting_y_range = [0, max_count_value]

    else:
        # ic("contains neither Cs137 nor Am241 data")
        # use Cs137 as default
        PF = PeakFinder(avg_array_bins, source="cs137")
        PF.source_peak_bins["cs137"] = 1395
        # bin_peak = PF.find_peaks_scipy()
        bin_peak = PF.find_max_bin()
        df["peak_count"] = df["array_bins"].apply(
            lambda x: calculate_peak_count(x, bin_peak)
        )
        starting_x_range = [0, 1999]
        starting_y_range = [0, max_count_value]

    return df, bin_peak, starting_x_range, starting_y_range


csv2df = {}
for csv_file in csv_files:
    filename = os.path.basename(csv_file)
    ic(filename)
    df, bin_peak, starting_x_range, starting_y_range = extract_csv2df(
        csv_file, module_number=0
    )
    csv2df[csv_file] = (df, bin_peak, starting_x_range, starting_y_range)


def update_heatmap(csv_file, count_type="peak_counts"):
    # ic(csv_file)
    filename = os.path.basename(csv_file)
    # ic(filename)
    filename_no_ext = os.path.splitext(filename)[0]
    # ic(filename_no_ext)

    df, bin_peak, _, _ = csv2df[csv_file]
    if count_type == "total_counts":
        heatmap_table = df.pivot_table(
            index="y_index", columns="x_index", values="total_count"
        )
    else:
        heatmap_table = df.pivot_table(
            index="y_index", columns="x_index", values="peak_count"
        )

    heatmap_fig = px.imshow(
        heatmap_table,
        color_continuous_scale="viridis",
        text_auto=True,
        labels=dict(color="Value", x="X", y="Y"),
        title=f"Heatmap_of_{filename_no_ext}_{count_type}",
    )

    heatmap_fig.update_layout(
        xaxis=dict(title="X-index of Pixel"),
        yaxis=dict(title="Y-index of Pixel"),
        xaxis_nticks=12,
        yaxis_nticks=12,
        margin=dict(l=40, r=40, t=40, b=40),
        width=700,
        height=700,
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


def update_spectrum_avg(csv_file, x_range, y_range):
    filename = os.path.basename(csv_file)
    filename_no_ext = os.path.splitext(filename)[0]

    df, bin_peak, _, _ = csv2df[csv_file]
    summed_array_bins = np.sum(df["array_bins"].values, axis=0)
    avg_array_bins = summed_array_bins / len(df)
    avg_peak_counts = calculate_peak_count(avg_array_bins, bin_peak)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(len(avg_array_bins)), y=avg_array_bins))

    fig = add_peak_lines(fig, bin_peak, max(avg_array_bins))
    fig = update_axis_range(fig, x_range, y_range)

    fig.update_layout(
        title=f"Average spectrum, Peak count = {avg_peak_counts:.1f} ",
        xaxis_title="Bin Index",
        yaxis_title="Average Counts",
        width=700,
        height=350,
    )

    return fig


def update_spectrum_pixel(csv_file, x_index, y_index, x_range, y_range):
    filename = os.path.basename(csv_file)
    filename_no_ext = os.path.splitext(filename)[0]

    df, bin_peak, _, _ = csv2df[csv_file]
    pixel_df = df[(df["x_index"] == x_index) & (df["y_index"] == y_index)]
    peak_count = pixel_df["peak_count"].values[0]
    array_bins = pixel_df["array_bins"].values[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(1, len(array_bins) + 1), y=array_bins))

    fig = add_peak_lines(fig, bin_peak, max(array_bins))
    fig = update_axis_range(fig, x_range, y_range)

    fig.update_layout(
        title=f"Pixel ({x_index}, {y_index}), Peak count = {peak_count}",
        xaxis_title="Bin Index",
        yaxis_title="Counts",
        width=700,
        height=350,
    )
    return fig


def create_app():

    app = dash.Dash(__name__)

    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2("Heatmap Dashboard"),
                    dcc.Dropdown(
                        id="csv-dropdown",
                        options=[
                            {"label": os.path.basename(csv_file), "value": csv_file}
                            for csv_file in csv_files
                        ],
                        value=csv_files[0],
                        style={"width": "80%"},
                    ),
                    dcc.RadioItems(
                        id="count-type",
                        options=[
                            {"label": "Peak Counts", "value": "peak_counts"},
                            {"label": "Total Counts", "value": "total_counts"},
                        ],
                        value="total_count",
                        labelStyle={"display": "inline-block"},
                    ),
                    dcc.Graph(
                        id="heatmap-graph",
                        clickData=(
                            {"points": [{"x": 3, "y": 3}]}
                            if "clickData" not in locals()
                            else "clickData"
                        ),
                    ),
                ],
                style={"display": "flex", "flex-direction": "column"},
            ),
            html.Div(
                [
                    html.H2("Spectrum Dashboard"),
                    dcc.Graph(id="spectrum-avg-graph"),
                    dcc.Graph(id="spectrum-pixel-graph-1"),
                    # dcc.Input(id="x-index", type="number", value=1),
                    html.Div(
                        [
                            html.Label("X -  "),
                            dcc.Dropdown(
                                id="x-index-dropdown",
                                options=[
                                    {"label": str(i), "value": i} for i in range(1, 12)
                                ],
                                value=9,
                                style={"width": "40%"},
                            ),
                            html.Label("Y -  "),
                            dcc.Dropdown(
                                id="y-index-dropdown",
                                options=[
                                    {"label": str(i), "value": i} for i in range(1, 12)
                                ],
                                value=3,
                                style={"width": "40%"},
                            ),
                        ],
                        style={"display": "flex", "flex-direction": "row"},
                    ),
                    dcc.Graph(id="spectrum-pixel-graph-2"),
                    # bins range slider (x-axis)
                    html.Div(
                        [
                            html.Label("X"),
                            dcc.RangeSlider(
                                min=0,
                                max=1499,
                                value=[1, 200],
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
                                max=100,
                                value=[0, 60],
                                id="y-axis-slider",
                            ),
                        ],
                        style={
                            "width": "70%",
                        },
                    ),
                ],
                style={"display": "flex", "flex-direction": "column"},
            ),
        ],
        style={
            "display": "flex",
        },
    )

    @app.callback(
        Output("heatmap-graph", "figure"),
        [Input("csv-dropdown", "value"), Input("count-type", "value")],
    )
    def update_heatmap_graph(csv_file, count_type):
        return update_heatmap(csv_file, count_type)

    @app.callback(
        Output("spectrum-avg-graph", "figure"),
        [
            Input("csv-dropdown", "value"),
            Input("x-axis-slider", "value"),
            Input("y-axis-slider", "value"),
        ],
    )
    def update_spectrum_avg_graph(csv_file, x_range, y_range):
        return update_spectrum_avg(csv_file, x_range, y_range)

    @app.callback(
        Output("spectrum-pixel-graph-1", "figure"),
        [
            Input("csv-dropdown", "value"),
            Input("heatmap-graph", "clickData"),
            Input("x-axis-slider", "value"),
            Input("y-axis-slider", "value"),
        ],
    )
    def update_spectrum_pixel_graph(csv_file, clickData, x_range, y_range):
        # print(f"{clickData = }")
        # ic(clickData)
        x_index_click = clickData["points"][0]["x"]
        y_index_click = clickData["points"][0]["y"]
        # print(f"{x_index_click = }, {y_index_click = }")
        ic(x_index_click, y_index_click)
        return update_spectrum_pixel(
            csv_file, x_index_click, y_index_click, x_range, y_range
        )

    @app.callback(
        Output("spectrum-pixel-graph-2", "figure"),
        [
            Input("csv-dropdown", "value"),
            Input("x-index-dropdown", "value"),
            Input("y-index-dropdown", "value"),
            Input("x-axis-slider", "value"),
            Input("y-axis-slider", "value"),
        ],
    )
    def update_spectrum_pixel_graph(csv_file, x_index, y_index, x_range, y_range):
        return update_spectrum_pixel(csv_file, x_index, y_index, x_range, y_range)

    @app.callback(
        [
            Output("x-axis-slider", "value"),
            Output("x-axis-slider", "max"),
            Output("y-axis-slider", "value"),
            Output("y-axis-slider", "max"),
        ],
        [Input("csv-dropdown", "value")],
    )
    def update_slider_values(csv_file):
        _, _, x_range, y_range = csv2df[csv_file]
        if "Cs137" in csv_file:
            x_max, y_max = 1499, 200
        elif "Am241" in csv_file:
            x_max, y_max = 199, 80
        else:
            x_max, y_max = 1499, 200

        return x_range, x_range[1], y_range, y_range[1]

    return app


if __name__ == "__main__":
    app = create_app()
    app.run_server(debug=True, port=8080, use_reloader=True)
