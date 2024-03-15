# Instructions on using single_csv_dashboard.py

This dashboard is designed to assist in visualizing the data obtained from the H3D Mapper experiments.

Usage:

1. Ensure that you have Python installed on your system.
2. Install the required dependencies by running the command: pip install -r requirements.txt
3. Place the CSV file you want to visualize in the same directory as this script.
4. Run the script using the command: python single_csv_dashboard.py
5. The dashboard will be generated and saved as an HTML file in the current directory.

Note: Make sure that the CSV file follows the required format for the dashboard to work properly.

## Heatmap Dashboard
The left portion of the dashboard is dedicated to the heatmap and its features.

The dropdown at the top left of the page allows the user to specify which .csv file they would like to use. There are also several options to customize the data:

1. Count Type
    * Peak Counts: Calculated by finding the peaks of the average spectrum and summing the 25 bins left and right of peak
    * Total Counts: All counts for each pixel 
    * Non-Peak Counts: Counts that are not peak counts
    * Pixel ID: Orientation of pixels

2. Normalization
    * Raw Counts: Integer values of obtained counts for each pixel
    * Normalized: Divides each pixel on the heatmap by the largest pixel on the heatmap

There are also four different themes to choose from: 

1. Viridis
2. Plasma
3. Inferno
4. Jet. 

These themes modify the color scheme of the heatmap and the 3D surface plot.

### Heatmap
The heatmap provides a visualization of the 121 anode pixels on the sensor inside the quad tester. Using the data from the third-party H3D Software, it shows the number of counts each pixel on the sensor experiences, helping us better understand and further study pixel behavior.

![Heatmap](/assets/heatmap.png)

### 3D Surface Plot
The Surface Plot is a 3D model of the heatmap. Its x and y axes correspond to the x and y axes of the heatmap. The third axis, or z-axis, corresponds to the value of each cell in the heatmap. This 3D plot is useful because it helps us see how neighbouring pixels react in response to a high count pixel. 

![3D Surface Plot](/assets/surface_plot.png)

### Color-Scale Slider
The Color-Scale slider impacts both the heatmap and the 3D Surface Plot. Its maximum and minimum values are dynamically set based on the highest and lowest counts on the heatmap. This range slider allows the user to specify upper and lower limits to the color scale. This results in counts greater than the upper limit being showin in one color, and counts below the lower limit being showin in another color. This is helpful because when using the 3D plot, it is clear to see the color differences between a high count pixel and its neighbours.

![Colorscale Slider](/assets/colorscale_slider.png)

## Spectrum Dashboard
The right portion of the dashboard is dedicated to plots of the pixels. 

### Average Spectrum Plot
The average spectrum graph plots the average counts (of all 121 pixels) vs the bin index from the .csv file. There are 200 bins for Americium-241 and 2000 bins for Cobalt-57. This graph gives us a general idea of how all pixels are behaving. 

![Average Pixel Spectrum](/assets/avg_spectrum.png)

### Single Pixel Spectrum Plots
There are two Single Pixel Spectrum plots: 

1. Heatmap Click
    * Click on any pixel/cell of the heatmap and this spectrum plot will update to show the spectrum of the selected pixel.

![Single Spectrum - Heatmap Click Control](/assets/single_spectrum_click.png)

2. Dropdown Menus
    * Specify the single pixels by using the 3 sets of x and y indices dropdown menus and the spectrum plot will update to show the pixel spectrums. This graph can plot 3 pixels at once, and each pixel is indicated with a different color. 

![Single Spectrum - Dropdown Control](/assets/single_spectrum_dropdown_plot.png)

It is important to note that the last two spectrum plots have the same functionality -- plotting the counts vs bins for a single pixel. They differ in how the pixel to be plotted is selected (Heatmap Click vs Dropdown Menu), and the number of pixels whose spectrum can be plotted on one graph.

### X-Y Range Sliders
All three spectrum plots can be controlled by range sliders: one for the bins (x-axis) and one for the counts (y-axis). This makes it easier to study a particular range since the peak for each RI source occurs at a different bin location. 

![X-Y Range Sliders](/assets/xy_range_sliders.png)
