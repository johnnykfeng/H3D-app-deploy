# %% Import necessary libraries
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import sys

# add the root directory to the path in order to import the ExtractModule class
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
from Extract_module import (
    ExtractModule,
    OrganizeData,
)

# %% Extract data and transform it
EM = ExtractModule(csv_file="data\Co57_2mins_2000V_20cycles.csv")
df_transformed_list = EM.transform_all_df()
organized_data = OrganizeData(df_transformed_list, EM.csv_file)
all_data_dict = organized_data.all_data_dict

def calculate_peak_count(array: np.array, peak_bin: int, peak_halfwidth=25):
    """Calculate the counts in a peak given the array and the peak bin number."""
    peak_count = np.sum(array[peak_bin - peak_halfwidth : peak_bin + peak_halfwidth])
    return peak_count

peak_bin = 224
peak_halfwidth = 25

# calculate the peak count for each pixel and create a heatmap
for keys, values in all_data_dict.items():
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

organized_data.all_data_dict = all_data_dict # update the all_data_dict in the OrganizeData object
N_MODULES = EM.number_of_modules  # number of dataframes
df_plot = organized_data.organize_line_plots(if_calculate_peak_count=True)

del df_transformed_list  # delete the list of dataframes to save memory
del organized_data  # delete the organized data object to save memory
del all_data_dict  # delete the all_data_dict to save memory
del EM  # delete the ExtractModule object to save memory


# %% set up Dash app
app = dash.Dash(__name__)

# layout/html
app.layout = html.Div(
    [
        # -- stage coordinate dropdown -- #
        html.Div(
            [
                html.Label(
                    "Select Stage Coordinate",
                    style={
                        "display": "flex",
                    },
                ),
                dcc.Dropdown(
                    id="stage-coordinate-dropdown",
                    options=[
                        {"label": "X", "value": "stage_x_list"},
                        {"label": "Y", "value": "stage_y_list"},
                    ],
                    value="stage_x_list",
                    style={"width": "30%", "display": "inline-block"},
                ),
            ],
        ),

        html.H3("Line Plot #1"),
        html.Div(  # container for X and Y labels + dropdowns for line plot 1
            [
                html.Div(  # container for X label and dropdown for line plot 1
                    [
                        html.Label("Select X index:", style={"display": "flex"}),
                        dcc.Dropdown(
                            id="x-index-dropdown-1",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=5,
                            style={
                                "width": "150%",
                                "display": "flex",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "margin-right": "60px",
                    },
                ),
                html.Div(  # container for Y label and dropdown for line plot 1
                    [
                        html.Label(
                            "Select Y index:",
                            style={
                                "display": "flex",
                            },
                        ),
                        dcc.Dropdown(
                            id="y-index-dropdown-1",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=6,
                            style={"width": "150%", "display": "flex"},
                        ),
                    ],
                    style={"display": "flex", "flex-direction": "column"},
                ),
            ],
            style={"display": "flex", "flex-direction": "row", "margin-bottom": "20px"},
            id="line-plot-1-pixel-selection",
        ),  # end of container for X and Y labels + dropdowns for line plot 1
        html.H3("Line Plot #2"),
        html.Div(  # container for X and Y labels + dropdowns for line plot 2
            [
                html.Div(  # container for X label and dropdown for line plot 2
                    [
                        html.Label("Select X index:", style={"display": "flex"}),
                        dcc.Dropdown(
                            id="x-index-dropdown-2",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=5,
                            style={
                                "width": "150%",
                                "display": "flex",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "margin-right": "60px",
                    },
                ),
                html.Div(  # container for Y label and dropdown for line plot 2
                    [
                        html.Label(
                            "Select Y index:",
                            style={
                                "display": "flex",
                            },
                        ),
                        dcc.Dropdown(
                            id="y-index-dropdown-2",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=7,
                            style={"width": "150%", "display": "flex"},
                        ),
                    ],
                    style={"display": "flex", "flex-direction": "column"},
                ),
            ],
            style={"display": "flex", "flex-direction": "row"},
            id="line-plot-1-pixel-selection",
        ),  # end of container for X and Y labels + dropdowns for line plot 2
        dcc.Graph(id="line-plot", style={"margin-top": "1%", "margin-bottom": "1%"}),
        html.H3("Line Plot #3"),
        html.Div(  # container for X and Y labels + dropdowns for line plot 3
            [
                html.Div(  # container for X label and dropdown for line plot 3
                    [
                        html.Label("Select X index:", style={"display": "flex"}),
                        dcc.Dropdown(
                            id="x-index-dropdown-3",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=5,
                            style={
                                "width": "150%",
                                "display": "flex",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "margin-right": "60px",
                    },
                ),
                html.Div(  # container for Y label and dropdown for line plot 3
                    [
                        html.Label(
                            "Select Y index:",
                            style={
                                "display": "flex",
                            },
                        ),
                        dcc.Dropdown(
                            id="y-index-dropdown-3",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=2,
                            style={"width": "150%", "display": "flex"},
                        ),
                    ],
                    style={"display": "flex", "flex-direction": "column"},
                ),
            ],
            style={"display": "flex", "flex-direction": "row", "margin-bottom": "20px"},
            id="line-plot-3-pixel-selection",
        ),  # end of container for X and Y labels + dropdowns for line plot 3
        html.H3("Line Plot #4"),
        html.Div(  # container for X and Y labels + dropdowns for line plot 4
            [
                html.Div(  # container for X label and dropdown for line plot 4
                    [
                        html.Label("Select X index:", style={"display": "flex"}),
                        dcc.Dropdown(
                            id="x-index-dropdown-4",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=5,
                            style={
                                "width": "150%",
                                "display": "flex",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "margin-right": "60px",
                    },
                ),
                html.Div(  # container for Y label and dropdown for line plot 4
                    [
                        html.Label(
                            "Select Y index:",
                            style={
                                "display": "flex",
                            },
                        ),
                        dcc.Dropdown(
                            id="y-index-dropdown-4",
                            options=[
                                {"label": str(i), "value": i} for i in range(1, 12)
                            ],
                            value=3,
                            style={"width": "150%", "display": "flex"},
                        ),
                    ],
                    style={"display": "flex", "flex-direction": "column"},
                ),
            ],
            style={"display": "flex", "flex-direction": "row"},
            id="line-plot-4-pixel-selection",
        ),  # end of container for X and Y labels + dropdowns for line plot 4
        dcc.Graph(
            id="line-plot-2",
            style={
                "margin-top": "1%",
            },
        ),

    ],
)


# callback function for plots 1/2
@app.callback(
    Output("line-plot", "figure"),
    [
        Input("x-index-dropdown-1", "value"),
        Input("y-index-dropdown-1", "value"),
        Input("x-index-dropdown-2", "value"),
        Input("y-index-dropdown-2", "value"),
        Input("stage-coordinate-dropdown", "value"),
    ],
)
# updates plot 1 and 2
def update_line_plot(x_index_1, y_index_1, x_index_2, y_index_2, stage_coordinate):
    position_values, pixel_total_counts = get_plot_data(
        x_index_1, y_index_1, stage_coordinate
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=position_values,
            y=pixel_total_counts,
            mode="lines+markers",
            name=f"Pixel ({x_index_1}, {y_index_1})",
            line=dict(color="blue"),
        )
    )

    position_values, pixel_total_counts = get_plot_data(
        x_index_2, y_index_2, stage_coordinate
    )

    fig.add_trace(
        go.Scatter(
            x=position_values,
            y=pixel_total_counts,
            mode="lines+markers",
            name=f"Pixel ({x_index_2}, {y_index_2})",
            line=dict(color="red"),
        )
    )

    fig.update_layout(
        xaxis_title="Stage position (mm)",
        yaxis_title="Peak counts",
        title=f"Peak Counts vs Stage Position",
        width=800,
        height=500,
    )

    return fig


# another callback for the second graph with line-plot 3 and 4
@app.callback(
    Output("line-plot-2", "figure"),
    [
        Input("x-index-dropdown-3", "value"),
        Input("y-index-dropdown-3", "value"),
        Input("x-index-dropdown-4", "value"),
        Input("y-index-dropdown-4", "value"),
        Input("stage-coordinate-dropdown", "value"),
    ],
)
# updates plots 3 and 4
def update_line_plot_2(x_index_3, y_index_3, x_index_4, y_index_4, stage_coordinate):
    stage_x_list_3, pixel_total_counts_list_3 = get_plot_data(
        x_index_3, y_index_3, stage_coordinate
    )
    stage_x_list_4, pixel_total_counts_list_4 = get_plot_data(
        x_index_4, y_index_4, stage_coordinate
    )

    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=stage_x_list_3,
            y=pixel_total_counts_list_3,
            mode="lines+markers",
            name=f"Pixel ({x_index_3}, {y_index_3})",
            line=dict(color="blue"),
        )
    )
    fig2.add_trace(
        go.Scatter(
            x=stage_x_list_4,
            y=pixel_total_counts_list_4,
            mode="lines+markers",
            name=f"Pixel ({x_index_4}, {y_index_4})",
            line=dict(color="red"),
        )
    )

    fig2.update_layout(
        xaxis_title="stage x position",
        yaxis_title="total pixel counts",
        title=f"Line Plots",
    )

    return fig2  # Return a single Figure object


def get_plot_data(selected_x_index, selected_y_index, stage_coordinate):
    df_plot_filtered = df_plot[
        (df_plot["x_index"] == selected_x_index)
        & (df_plot["y_index"] == selected_y_index)
    ]

    if stage_coordinate == "stage_x_list":
        stage_list = df_plot_filtered["x_position"].values[0]
    else:
        stage_list = df_plot_filtered["y_position"].values[0]

    # pixel_total_counts_list = df_plot_filtered["total_counts"].values[0]
    pixel_total_counts_list = df_plot_filtered["peak_counts"].values[0]

    return stage_list, pixel_total_counts_list


# run
if __name__ == "__main__":
    app.run_server(port=8052, debug=True)
