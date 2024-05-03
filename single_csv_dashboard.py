import os
import numpy as np
import markdown
from icecream import ic

from dash import dcc, html, Dash
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

from data_handling_modules import (
                                ExtractModule, 
                                TransformDf, 
                                PeakFinder)
from plotting_modules import (
    create_spectrum_average,
    create_spectrum_pixel,
    create_pixelized_heatmap,
    create_surface_plot_3d,
)

print("+++++++++++ START PROGRAM +++++++++++")


def find_csv_files(directory):
    """Find all CSV files in the given directory and its subdirectories"""
    csv_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    return csv_files


# directory = r"data/leaky_pixel_data"
directory = r"data/module_voltage_data"
csv_files = find_csv_files(directory)
# ic(csv_files)


def calculate_peak_count(array: np.array, peak_bin: int, peak_halfwidth=25):
    """Calculate the counts in a peak given the array and the peak bin number."""
    peak_count = np.sum(array[peak_bin - peak_halfwidth : peak_bin + peak_halfwidth])
    return peak_count


approximate_peak_bins = {"Am241": 57, "Cs137": 1578, "Co57": 244}


def source_from_filename(filename):
    if "Cs137" in filename:
        if "Co57" in filename:
            source = "Co57"
        else:
            source = "Cs137"
    else:
        source = "Am241"
    return source


def extract_csv2df(csv_file, module_number=0):
    """
    Extract and transform data from csv file to a pandas DataFrame.
    module_number=0 for data from production tester
    module_number=3 for data from quad-tester
    """
    filename = os.path.basename(csv_file)

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
    # max_count_value = df["array_bins"].apply(lambda x: max(x)).max()
    # avg spectrum use to determine the bin_peak
    avg_array_bins = df["array_bins"].sum(axis=0) / 121
    max_count_value = int(avg_array_bins.max() * 1.5)

    source = source_from_filename(filename)

    PF = PeakFinder()
    avg_peak_bin = PF.find_peak_bin(avg_array_bins, approximate_peak_bins[source])
    df = TD.add_peak_counts(df, bin_peak=avg_peak_bin, bin_width=25)

    number_of_bins = len(df["array_bins"].values[0])
    starting_x_range = [0, number_of_bins - 1]
    starting_y_range = [0, max_count_value]

    return df, avg_peak_bin, starting_x_range, starting_y_range


# Extract data from csv files and store in csv2df dictionary
csv2df = {}
for csv_file in csv_files:
    filename = os.path.basename(csv_file)
    # ic(filename)
    df, bin_peak, starting_x_range, starting_y_range = extract_csv2df(
        csv_file, module_number=0
    )
    csv2df[csv_file] = (df, bin_peak, starting_x_range, starting_y_range)


app_defaults = {
    "csv_index": 3,
    "count_type": "peak_count",
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

# Read the markdown file
with open("app_readme.md", "r") as markdown_file:
    readme_text = markdown_file.read()

# Convert the markdown to HTML
html_text = markdown.markdown(readme_text)


def create_app():
    app = Dash(__name__, suppress_callback_exceptions=True)
    app.layout = html.Div(
        [
            dcc.Tabs(
                id="tabs",
                value="tab-1",
                children=[
                    dcc.Tab(label="Heatmap and Spectrum Dashboard", value="tab-1"),
                    dcc.Tab(label="README", value="tab-2"),
                ],
            ),
            html.Div(id="tabs-content"),
        ]
    )

    @app.callback(Output("tabs-content", "children"), [Input("tabs", "value")])
    def render_content(tab):
        if tab == "tab-2":
            with open("app_readme.md", "r") as markdown_file:
                readme_text = markdown_file.read()
            return dcc.Markdown(children=readme_text)
        elif tab == "tab-1":
            return html.Div(
                [
                    html.Div(
                        [
                            html.H2("Heatmap Dashboard"),
                            html.Label("Select a data file:"),
                            dcc.Dropdown(
                                id="csv-dropdown",
                                options=[
                                    {
                                        "label": os.path.basename(csv_file),
                                        "value": csv_file,
                                    }
                                    for csv_file in csv_files
                                ],
                                value=csv_files[app_defaults["csv_index"]],
                                style={
                                    "width": "100%",
                                    "height": "50px",
                                    "font-size": "20px",
                                },
                            ),
                            html.Div(  # Radio buttons for heatmap
                                [
                                    dcc.RadioItems(
                                        id="count-type",
                                        options=[
                                            {
                                                "label": "Peak Counts",
                                                "value": "peak_count",
                                            },
                                            {
                                                "label": "Total Counts",
                                                "value": "total_count",
                                            },
                                            {
                                                "label": "Non-Peak Count",
                                                "value": "non_peak_count",
                                            },
                                            {"label": "Pixel ID", "value": "pixel_id"},
                                        ],
                                        value=app_defaults["count_type"],
                                        style={
                                            "display": "flex",
                                            "flex-direction": "column",
                                            "font-size": "20px",
                                            "margin-top": "20px",
                                            "margin-left": "20px",
                                            "margin-bottom": "20px",
                                        },
                                    ),
                                    dcc.RadioItems(
                                        id="normalization-buttons",
                                        options=[
                                            {"label": "Raw Counts", "value": "raw"},
                                            {
                                                "label": "Normalized",
                                                "value": "normalized",
                                            },
                                        ],
                                        value=app_defaults["normalization"],
                                        style={
                                            "display": "flex",
                                            "flex-direction": "column",
                                            "font-size": "20px",
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
                                            "font-size": "20px",
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
                                        # value=[0, 1200],
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
                            html.H3(
                                "Click on a pixel in the heatmap to view its spectrum."
                            ),
                            dcc.Graph(id="spectrum-pixel-graph-1"),
                            html.H3(
                                "Select pixels with dropdowns to compare their spectra."
                            ),
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
                            dcc.Graph(
                                id="spectrum-pixel-graph-2",
                            ),
                            # bins range slider (x-axis)
                            html.Div(
                                [
                                    html.Label("X-axis range"),
                                    dcc.RangeSlider(
                                        min=0,
                                        max=1999,
                                        value=[1, 200],
                                        id="x-axis-slider",
                                    ),
                                ],
                                style={
                                    "width": "90%",
                                    "margin": "0 auto",
                                },
                            ),
                            # counts range slider (y-axis)
                            html.Div(
                                [
                                    html.Label("Y-axis range"),
                                    dcc.RangeSlider(
                                        min=0,
                                        max=100,
                                        value=[0, 60],
                                        id="y-axis-slider",
                                    ),
                                ],
                                style={
                                    "width": "90%",
                                    "margin": "0 auto",
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

    # callback to dynamically update the maximum value of slider based on max heatmap value
    @app.callback(
        Output("color-range-slider", "max"), [Input("heatmap-graph", "figure")]
    )
    def update_color_slider_max(figure):
        # extract the data from the figure
        z_data = figure["data"][0]["z"]

        # calculate the max value
        max_value = np.max(z_data)

        return max_value

    # callback to dynamically update the min value of slider based on min heatmap value
    @app.callback(
        Output("color-range-slider", "min"), [Input("heatmap-graph", "figure")]
    )
    def update_color_slider_min(figure):
        # extract the data from the figure
        z_data = figure["data"][0]["z"]

        # calculate the min value
        min_value = np.min(z_data)

        return min_value

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
        ic(csv_file)
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]
        df, _, _, _ = csv2df[csv_file]
        return create_pixelized_heatmap(
            df, count_type, normalization, color_scale, color_range,
        )

    @app.callback(
        Output("3d-surface-plot", "figure"),
        [
            Input("heatmap-graph", "figure"),
            Input("color-scale", "value")
        ],
    )
    def update_3d_surface_graph(figure, color_scale):
        return create_surface_plot_3d(figure, color_scale)

    @app.callback(
        Output("spectrum-avg-graph", "figure"),
        [
            Input("csv-dropdown", "value"),
            Input("x-axis-slider", "value"),
            Input("y-axis-slider", "value"),
        ],
    )
    def update_spectrum_average_graph(csv_file, x_range, y_range):
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]
        df, bin_peak, _, _ = csv2df[csv_file]

        return create_spectrum_average(
            df, bin_peak=bin_peak, x_range=x_range, y_range=y_range
        )

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
        df, bin_peak, _, _ = csv2df[csv_file]

        return create_spectrum_pixel(
            df, bin_peak, x_range, y_range, (x_index_click, y_index_click)
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
        df, bin_peak, _, _ = csv2df[csv_file]
        return create_spectrum_pixel(
            df,
            bin_peak,
            x_range,
            y_range,
            (x_index_dropdown_1, y_index_dropdown_1),
            (x_index_dropdown_2, y_index_dropdown_2),
            (x_index_dropdown_3, y_index_dropdown_3),
        )

    @app.callback(
        [
            Output("x-axis-slider", "max"),
            Output("y-axis-slider", "max"),
            Output("x-axis-slider", "value"),
            Output("y-axis-slider", "value"),
        ],
        [Input("csv-dropdown", "value")],
    )
    def update_slider_max(csv_file):
        if csv_file is None:
            csv_file = csv_files[app_defaults["csv_index"]]

        filename = os.path.basename(csv_file)
        source = source_from_filename(filename)
        _, _, x_range, y_range = csv2df[csv_file]
        # return max(x_range), max(y_range)
        if source == "Am241":
            starting_x_range = [50, 150]
        elif source == "Co57":
            starting_x_range = [100, 350]
        else:  # source == Cs137
            starting_x_range = [1400, 1750]
        return max(x_range), max(y_range), starting_x_range, y_range

    return app


if __name__ == "__main__":
    app = create_app()
    app.run_server(debug=True, port=8080, use_reloader=True)
