import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def add_peak_lines(fig, bin_peak, bin_halfwidth, max_y):
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
            x0=bin_peak - bin_halfwidth,
            y0=0,
            x1=bin_peak - bin_halfwidth,
            y1=max_y,
            line=dict(color="red", width=1, dash="dash"),
            opacity=0.5,
        )
        fig.add_shape(
            type="line",
            x0=bin_peak + bin_halfwidth,
            y0=0,
            x1=bin_peak + bin_halfwidth,
            y1=max_y,
            line=dict(color="red", width=1, dash="dash"),
            opacity=0.5,
        )
        
        return fig


def update_heatmap(df, count_type, normalization="raw", color_scale="viridis"):

    count_table = df.pivot_table(index="y_index", columns="x_index", values=count_type)

    if normalization:
        max_pixel_value = count_table.values.max()
        count_table = (count_table / max_pixel_value).round(2)

    heatmap_fig = px.imshow(
        count_table,
        color_continuous_scale=color_scale,
        text_auto=".3g",
        labels=dict(color="Value", x="X", y="Y"),
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

    
def update_average_spectrum(df, bin_peak, peak_halfwidth, do_add_peak_lines=True):
    avg_array_bins = np.sum(df["array_bins"].values, axis=0) / len(df)
    avg_spectrum_figure = go.Figure()
    avg_spectrum_figure.add_trace(go.Scatter(x=np.arange(len(avg_array_bins)),
                                            y=avg_array_bins, mode='lines', 
                                            name='Average Spectrum'))

    if do_add_peak_lines:
        avg_spectrum_figure = add_peak_lines(avg_spectrum_figure, 
                                            bin_peak, 
                                            peak_halfwidth, 
                                            max_y=max(avg_array_bins))

    return avg_spectrum_figure

def update_pixel_spectrum(df, x_index, y_index, bin_peak, peak_halfwidth, do_add_peak_lines=True):
    pixel_df = df[(df["x_index"] == x_index) & (df["y_index"] == y_index)]
    array_bins = pixel_df["array_bins"].values[0]
    pixel_spectrum_figure = go.Figure()
    pixel_spectrum_figure.add_trace(go.Scatter(x=np.arange(len(array_bins)),
                                                y=array_bins, 
                                                mode='lines', 
                                                name=f'Pixel Spectrum at x={x_index}, y={y_index}'))
    if do_add_peak_lines:
        pixel_spectrum_figure = add_peak_lines(pixel_spectrum_figure, 
                                            bin_peak, 
                                            peak_halfwidth, 
                                            max_y=max(array_bins))
    return pixel_spectrum_figure
