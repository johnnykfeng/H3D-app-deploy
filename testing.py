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
from Extract_module import ExtractModule, TransformDf
import os
from icecream import ic
from spectrum_peak_finder import PeakFinder

print("+++++++++++ START PROGRAM +++++++++++")


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
# ic(csv_files)


def calculate_peak_count(array: np.array, peak_bin: int, peak_halfwidth=25):
    """Calculate the counts in a peak given the array and the peak bin number."""
    peak_count = np.sum(array[peak_bin - peak_halfwidth : peak_bin + peak_halfwidth])
    return peak_count


def extract_csv2df(csv_file, module_number=0):
    """
    Extract and transform data from csv file to a pandas DataFrame.
    module_number=0 for data from production tester
    module_number=3 for data from quad-tester
    """
    filename = os.path.basename(csv_file)
    filename_no_ext = os.path.splitext(filename)[0]

    EM = ExtractModule(csv_file)
    if csv_file.endswith("14892_M010710_20240208-1449__testresults.csv"):
        # only this csv file has "Pixel" as header
        EM.target_string = "Pixel"
    else:
        EM.target_string = "H3D_Pixel"

    df = EM.extract_module2df(module_number=module_number)
    TD = TransformDf()
    df = TD.transform_df(df)

    # used to determine the range of the y axis in spectrum plots
    max_count_value = df["array_bins"].apply(lambda x: max(x)).max()
    # avg spectrum use to determine the bin_peak
    avg_array_bins = df["array_bins"].sum(axis=0) / 121

    if "Cs137" in filename_no_ext:
        if "Co57" in filename_no_ext:
            ic("Co57 data")
            PF = PeakFinder(avg_array_bins, source="co57")
            bin_peak = PF.find_max_bin()
            starting_x_range = [0, 1999]
        else:
            ic("Cs137 data")
            PF = PeakFinder(avg_array_bins, source="cs137")
            PF.source_peak_bins["cs137"] = 1395
            bin_peak = PF.find_max_bin()
            starting_x_range = [0, 1499]

        df["peak_count"] = (
            df["array_bins"]
            .apply(lambda x: calculate_peak_count(x, bin_peak))
            .astype(int)
        )

        df["non_peak_count"] = df["total_count"] - df["peak_count"]
        starting_y_range = [0, max_count_value]

    elif "Am241" in filename_no_ext:
        ic("Am241 data")
        PF = PeakFinder(avg_array_bins, source="am241")
        PF.source_peak_bins["am241"] = 75
        bin_peak = PF.find_max_bin()
        # bin_peak = 90
        df["peak_count"] = df["array_bins"].apply(
            lambda x: calculate_peak_count(x, bin_peak)
        )
        df["non_peak_count"] = df["total_count"] - df["peak_count"]
        starting_x_range = [0, 199]
        starting_y_range = [0, max_count_value]

    else:
        ic("contains neither Cs137 nor Am241 in filename")
        # use Cs137 as default
        PF = PeakFinder(avg_array_bins, source="cs137")
        PF.source_peak_bins["cs137"] = 1395
        bin_peak = PF.find_max_bin()
        df["peak_count"] = df["array_bins"].apply(
            lambda x: calculate_peak_count(x, bin_peak)
        )
        df["non_peak_count"] = df["total_count"] - df["peak_count"]
        starting_x_range = [0, 1499]
        starting_y_range = [0, max_count_value]

    return df, bin_peak, starting_x_range, starting_y_range


# Extract data from csv files and store in csv2df dictionary
csv2df = {}
for csv_file in csv_files:
    filename = os.path.basename(csv_file)
    # ic(filename)
    df, bin_peak, starting_x_range, starting_y_range = extract_csv2df(
        csv_file, module_number=0
    )
    csv2df[csv_file] = (df, bin_peak, starting_x_range, starting_y_range)


def update_heatmap(csv_file, count_type, normalization, color_scale, color_range):

    filename = os.path.basename(csv_file)
    filename_no_ext = os.path.splitext(filename)[0]

    df, bin_peak, _, _ = csv2df[csv_file]
    if count_type == "total_counts":
        heatmap_table = df.pivot_table(
            index="y_index", columns="x_index", values="total_count"
        )
    elif count_type == "peak_counts":
        heatmap_table = df.pivot_table(
            index="y_index", columns="x_index", values="peak_count"
        )
    elif count_type == "non_peak_counts":
        heatmap_table = df.pivot_table(
            index="y_index", columns="x_index", values="non_peak_count"
        )
    elif count_type == "pixel_id":
        heatmap_table = df.pivot_table(
            index="y_index", columns="x_index", values="pixel_id"
        )
    else:
        heatmap_table = df.pivot_table(
            index="y_index", columns="x_index", values="peak_count"
        )

    if normalization == "normalized":
        max_pixel_value = heatmap_table.values.max()
        heatmap_table = (heatmap_table / max_pixel_value).round(2)
    else:
        max_pixel_value = heatmap_table.values.max()

    # print(f"color_scale: {color_scale}")  # print color_s?cale value

    if color_range is None:
        color_range = [heatmap_table.values.min(), heatmap_table.values.max()]

    heatmap_fig = px.imshow(
        heatmap_table,
        color_continuous_scale=color_scale,  # use color_scale variable for colorscale
        range_color=color_range,
        text_auto=True,
        labels=dict(color="Value", x="X", y="Y"),
        title=f"Heatmap of {filename_no_ext}",
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
    avg_total_counts = np.sum(df["total_count"].values) / len(df)
    avg_peak_counts = calculate_peak_count(avg_array_bins, bin_peak)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(len(avg_array_bins)), y=avg_array_bins))

    fig = add_peak_lines(fig, bin_peak, max(avg_array_bins))
    fig = update_axis_range(fig, x_range, y_range)

    fig.update_layout(
        title=f"Average spectrum, Total count= {avg_total_counts:.1f}, Peak count= {avg_peak_counts:.1f} ",
        xaxis_title="Bin Index",
        yaxis_title="Average Counts",
        width=700,
        height=350,
    )

    return fig


# def update_spectrum_pixel(csv_file, x_index, y_index, x_range, y_range):
def update_spectrum_pixel(csv_file, x_range, y_range, *args):
    filename = os.path.basename(csv_file)
    filename_no_ext = os.path.splitext(filename)[0]
    df, bin_peak, _, _ = csv2df[csv_file]

    fig = go.Figure()

    ic(args)
    ic(len(args))
    for arg in args:
        if isinstance(arg, tuple):
            x_index, y_index = arg
            ic(x_index, y_index)

        if (x_index is not None) and (y_index is not None):
            pixel_df = df[(df["x_index"] == x_index) & (df["y_index"] == y_index)]
            # peak_count = pixel_df["peak_count"].values[0]
            array_bins = pixel_df["array_bins"].values[0]
            fig.add_trace(
                go.Scatter(
                    x=np.arange(1, len(array_bins) + 1),
                    y=array_bins,
                    name=f"Pixel ({x_index}, {y_index})",
                )
            )
            fig = add_peak_lines(fig, bin_peak, max(array_bins))

    fig = update_axis_range(fig, x_range, y_range)

    fig.update_layout(
        # title=f"Pixel ({x_index}, {y_index}), Peak count = {peak_count}",
        xaxis_title="Bin Index",
        yaxis_title="Counts",
        width=700,
        height=350,
    )
    total_count = pixel_df["total_count"].values[0]
    peak_count = pixel_df["peak_count"].values[0]
    if len(args) == 1:
        fig.update_layout(
            title=f"Pixel ({x_index}, {y_index}), Total count = {total_count}, Peak count = {peak_count}",
        )

    return fig


app_defaults = {
    "csv_index": 1,
    "count_type": "peak_counts",
    "normalization": "raw",
    "color_scale": "viridis",
    "x-click": 3,
    "y-click": 3,
    "x1-dropdown": 9,
    "y1-dropdown": 3,
    "x2-dropdown": 8,
    "y2-dropdown": 4,
    "x3-dropdown": 6,
    "y3-dropdown": 8,
}


def create_app():
    app = dash.Dash(__name__)

    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H2("Heatmap Dashboard"),
                    html.Label("Select a data file:"),
                    dcc.Dropdown(
                        id="csv-dropdown",
                        options=[
                            {"label": os.path.basename(csv_file), "value": csv_file}
                            for csv_file in csv_files
                        ],
                        value=csv_files[app_defaults["csv_index"]],
                        style={"width": "100%", "height": "50px", "font-size": "20px"},
                    ),
                    html.Div(  # Radio buttons for heatmap
                        [
                            dcc.RadioItems(
                                id="count-type",
                                options=[
                                    {"label": "Peak Counts", "value": "peak_counts"},
                                    {"label": "Total Counts", "value": "total_counts"},
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
                            html.Label("Colorscale Slider"),
                            dcc.RangeSlider(
                                id="color-range-slider",
                                min=0,
                                max=1200,
                                step=None,
                                value=[0, 1200],
                            ),
                        ]
                    ),
                    dcc.Graph(
                        id="heatmap-graph",
                        clickData=(
                            {"points": [{"x": 3, "y": 3}]}
                            if "clickData" not in locals()
                            else "clickData"
                        ),
                    ),
                    dcc.Graph(id="3d-surface-plot"),
                ],
                style={"display": "flex", "flex-direction": "column"},
            ),
            html.Div(
                [
                    html.H2("Spectrum Dashboard"),
                    dcc.Graph(id="spectrum-avg-graph"),
                    dcc.Graph(id="spectrum-pixel-graph-1"),
                    html.Div(  # container for dropdowns
                        [
                            html.Div(
                                [
                                    html.Label("X-1 = "),
                                    dcc.Dropdown(
                                        id="x-index-dropdown-1",
                                        options=[
                                            {"label": str(i), "value": i}
                                            for i in range(1, 12)
                                        ],
                                        value=9,
                                        style={"margin-right": "20px"},
                                    ),
                                    html.Label("Y-1 = "),
                                    dcc.Dropdown(
                                        id="y-index-dropdown-1",
                                        options=[
                                            {"label": str(i), "value": i}
                                            for i in range(1, 12)
                                        ],
                                        value=3,
                                        style={"margin-right": "20px"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "flex-direction": "column",
                                    "margin-left": "40px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Label("X-2 = "),
                                    dcc.Dropdown(
                                        id="x-index-dropdown-2",
                                        options=[
                                            {"label": str(i), "value": i}
                                            for i in range(1, 12)
                                        ],
                                        value=8,
                                        style={"margin-right": "20px"},
                                    ),
                                    html.Label("Y-2 = "),
                                    dcc.Dropdown(
                                        id="y-index-dropdown-2",
                                        options=[
                                            {"label": str(i), "value": i}
                                            for i in range(1, 12)
                                        ],
                                        value=4,
                                        style={"margin-right": "20px"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "flex-direction": "column",
                                    "margin-left": "40px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Label("X-3 = "),
                                    dcc.Dropdown(
                                        id="x-index-dropdown-3",
                                        options=[
                                            {"label": str(i), "value": i}
                                            for i in range(1, 12)
                                        ],
                                        value=6,
                                        style={"margin-right": "20px"},
                                    ),
                                    html.Label("Y-3 = "),
                                    dcc.Dropdown(
                                        id="y-index-dropdown-3",
                                        options=[
                                            {"label": str(i), "value": i}
                                            for i in range(1, 12)
                                        ],
                                        value=8,
                                        style={"margin-right": "20px"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "flex-direction": "column",
                                    "margin-left": "40px",
                                },
                            ),
                        ],
                        style={"display": "flex", "flex-direction": "row"},
                    ),  # end of container for dropdowns
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
        [
            Input("csv-dropdown", "value"),
            Input("count-type", "value"),
            Input("normalization-buttons", "value"),
            Input("color-scale", "value"),
            Input("color-range-slider", "value"),
        ],
    )
    def update_heatmap_graph(
        csv_file, count_type, normalization, color_scale, color_range
    ):
        # print(f"color_range: {color_range}")  # print color_range value
        ic(csv_file)
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]
        return update_heatmap(
            csv_file, count_type, normalization, color_scale, color_range
        )

    @app.callback(
        Output("3d-surface-plot", "figure"),
        [Input("heatmap-graph", "figure")],
        Input("color-scale", "value"),
        [Input("color-range-slider", "value")],
    )
    def update_3d_surface_plot(figure, color_scale, color_range):
        # Extract the data from the figure
        z_data = figure["data"][0]["z"]

        # Create x and y coordinates
        x_data = list(range(len(z_data[0])))
        y_data = list(range(len(z_data)))

        # Create a 3D surface plot with the selected colorscale
        plot_3d_fig = go.Figure(
            data=[go.Surface(x=x_data, y=y_data, z=z_data, colorscale=color_scale)]
        )

        # Update the color range of the 3D plot based on the color range
        plot_3d_fig.update_traces(cmin=color_range[0], cmax=color_range[1])
        # Update the layout
        plot_3d_fig.update_layout(
            title="3D Surface Plot",
            autosize=False,
            width=800,
            height=800,
            margin=dict(l=65, r=50, b=65, t=90),
        )

        return plot_3d_fig

    @app.callback(
        Output("spectrum-avg-graph", "figure"),
        [
            Input("csv-dropdown", "value"),
            Input("x-axis-slider", "value"),
            Input("y-axis-slider", "value"),
        ],
    )
    def update_spectrum_avg_graph(csv_file, x_range, y_range):
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]
        return update_spectrum_avg(csv_file, x_range, y_range)

    @app.callback(
        Output("spectrum-pixel-graph-1", "figure"),
        [
            Input("csv-dropdown", "value"),
            Input("x-axis-slider", "value"),
            Input("y-axis-slider", "value"),
            Input("heatmap-graph", "clickData"),
        ],
    )
    def update_spectrum_pixel_graph(csv_file, x_range, y_range, clickData):
        x_index_click = clickData["points"][0]["x"]
        y_index_click = clickData["points"][0]["y"]
        ic(x_index_click, y_index_click)
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]
        return update_spectrum_pixel(
            csv_file, x_range, y_range, (x_index_click, y_index_click)
        )

    @app.callback(
        Output("spectrum-pixel-graph-2", "figure"),
        [
            Input("csv-dropdown", "value"),
            Input("x-axis-slider", "value"),
            Input("y-axis-slider", "value"),
            Input("x-index-dropdown-1", "value"),
            Input("y-index-dropdown-1", "value"),
            Input("x-index-dropdown-2", "value"),
            Input("y-index-dropdown-2", "value"),
            Input("x-index-dropdown-3", "value"),
            Input("y-index-dropdown-3", "value"),
        ],
    )
    def update_spectrum_pixel_graph(
        csv_file,
        x_range,
        y_range,
        x_index_dropdown_1,
        y_index_dropdown_1,
        x_index_dropdown_2,
        y_index_dropdown_2,
        x_index_dropdown_3,
        y_index_dropdown_3,
    ):
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]
        return update_spectrum_pixel(
            csv_file,
            x_range,
            y_range,
            (x_index_dropdown_1, y_index_dropdown_1),
            (x_index_dropdown_2, y_index_dropdown_2),
            (x_index_dropdown_3, y_index_dropdown_3),
        )

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
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]
        _, _, x_range, y_range = csv2df[csv_file]
        return x_range, x_range[1], y_range, y_range[1]

    return app


if __name__ == "__main__":
    app = create_app()
    app.run_server(debug=True, port=8080, use_reloader=True)
