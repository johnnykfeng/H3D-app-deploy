import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os, sys
from icecream import ic

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(
    0, os.path.join(current_dir, "../")
)  # Add the parent directory to the path
from Extract_module import ExtractModule

# another approach is to create a peak finder class for each source

class PeakFinder:
    def __init__(self, array: np.array, source: str, threshold=0.2, prominence=0.5):
        if source.lower() not in ["am241", "co57", "cs137"]:
            raise ValueError("Invalid source")
        self.array = array
        self.source = source.lower()  # other sources: "co57", "cs137"
        self.threshold = threshold
        self.prominence = prominence
        # approximate conversion from keV to bin number
        self.source_peak_bins = {"am241": 90, "co57": 230, "cs137": 1492}
        self.source_peak_keV = {"am241": 60, "co57": 122, "cs137": 662}
        self.x_range = None
        self.peak_bins = None
        self.peak_properties = None
        self.peak_heights = None
        self.largest_peak_bin = None
        self.bin_max = None
        self.array_max = None

    def plot_calibrated_peaks(self, show=True):
        keV_list = []
        bin_list = []
        for keys in self.source_peak_bins.keys():
            keV_list.append(self.source_peak_keV[keys])
            bin_list.append(self.source_peak_bins[keys])   
            
        plt.figure("Calibrated peaks")
        i = 0
        for keV, bin in zip(keV_list, bin_list):
            if i == 0:
                plt.text(keV + 20, bin - 50, f"{keV=}, {bin=}")
                plt.plot(keV, bin, "s", markersize=5, label=f"{keV} keV - Am241")
            elif i == 1 or i == 2:
                plt.plot(keV, bin, "o", markersize=5, label=f"{keV} keV - Co57")
                plt.text(keV + 20, bin - 50, f"{keV=}, {bin=}")
            else:
                plt.plot(keV, bin, "x", markersize=5, label=f"{keV} keV - Cs137")
                plt.text(keV - 200, bin - 150, f"{keV=}, {bin=}")
            i += 1

        plt.plot(keV_list, bin_list, "--")
        plt.xlabel("Energy (keV)")
        plt.ylabel("Bin number")
        plt.legend()
        plt.grid(True, alpha=0.5)
        if show:
            plt.show()

    # def crop_array(self, peak_bin, halfwidth=25):
        # pass

    def crop_array(self, crop_width=40):
        ic(self.source)
        # ic(self.source_peak_bins)
        peak_bin_initial = self.source_peak_bins[self.source]
        self.x_range = [peak_bin_initial - crop_width, peak_bin_initial + crop_width]

        return self.array[self.x_range[0]: self.x_range[1]]

    def find_max_bin(self):
        cropped_array = self.crop_array()
        self.array_max = np.max(cropped_array)
        self.bin_max = np.argmax(cropped_array) + self.x_range[0]
        return self.bin_max
        
    def find_peaks_scipy(self):

        cropped_array = self.crop_array()
        
        cropped_peak_bin, self.properties = find_peaks(
            cropped_array, threshold=self.threshold,
            # prominence=self.prominence
        )
        
        self.array_max = np.max(cropped_array)
        self.bin_max = np.argmax(cropped_array) + self.x_range[0]
        
        self.peak_bins = cropped_peak_bin + self.x_range[0]
        self.peak_heights = [round(peak_height, 2) for peak_height in self.array[self.peak_bins]]
        ic(self.peak_bins, self.peak_heights, self.properties)
        # check if self.properties["left_bases"] and self.properties["right_bases"] exist
        if "left_bases" in self.properties and "right_bases" in self.properties:
            self.left_base = self.properties["left_bases"] + self.x_range[0]
            self.right_base = self.properties["right_bases"] + self.x_range[0]
        else:
            self.left_base = None
            self.right_base = None
        
        if len(self.peak_bins) == 0:
            return self.bin_max 
        elif len(self.peak_bins) == 1:
            self.largest_peak_bin = self.peak_bins[0]
            return self.largest_peak_bin
        else:
            self.largest_peak_bin = self.peak_bins[np.argmax(self.peak_heights)]
            return self.largest_peak_bin

    def find_largest_peak(self):
        if self.peak_bins is None:
            self.find_peaks()
        largest_peak_index = np.argmax(self.peak_heights)
        # print(f"Largest peak index: {largest_peak_index}")
        self.largest_peak_bin = self.peak_bins[largest_peak_index]
        return self.largest_peak_bin

    def plot_array(self, show=True):
        plt.figure()
        plt.title = "Raw spectrum"
        plt.plot(self.array, color = 'r')
        plt.grid(visible=True, which="both", alpha=0.5)
        if show:
            plt.show()

    def plot_peaks(self, show=True):
        if self.peak_bins is None:
            self.find_peaks()
        plt.figure("Peak finder")
        plt.plot(self.array, label="Raw spectrum averaged over all pixels")
        plt.plot(self.peak_bins, self.peak_heights, "s", label="Fitted peaks", alpha = 0.4)
        plt.plot(self.largest_peak_bin, max(self.peak_heights), "x", label="Fitted largest peak", alpha=0.5)
        plt.plot(self.bin_max, self.array_max, "o", label="Max bin", alpha=0.5)
        # plot vertical lines for the self.x_range[0] and self.x_range[1]
        plt.axvline(self.x_range[0], color="gray", linestyle="--", alpha=0.5)
        plt.axvline(self.x_range[1], color="gray", linestyle="--", alpha=0.5)
        plt.plot(np.zeros_like(self.array), "--", color="gray")
        plt.xlabel("Bin number")
        plt.ylabel("Counts")
        plt.grid(visible=True, which="both", alpha=0.5)
        plt.legend()
        if show:
            plt.show()

    @staticmethod
    def calculate_peak_count(array: np.array, peak_bin: int, peak_halfwidth=25):
        """Calculate the counts in a peak given the array and the peak bin number."""
        peak_count = np.sum(
            array[peak_bin - peak_halfwidth : peak_bin + peak_halfwidth]
        )
        return peak_count


if __name__ == "__main__":

    file_folder = r"data_analysis\\background_study\\"
    # filename = r"NoSourceB_5mins_Cs137.csv"
    filename = r"AmericiumB_5min_Cs137.csv"
    # filename = r"Cesium_5mins_Cs137.csv"
    # filename = r"Cobalt57_5mins_Cs137.csv"

    if os.path.exists(file_folder + filename):
        csv_file = file_folder + filename
        print(f"File found in folder: {csv_file}")
    else:
        csv_file = filename
        print(f"File found in root: {csv_file}")

    EM = ExtractModule(csv_file)
    df = EM.extract_module2df(module_number=3)
    df_new = EM.transform_df(df)

    avg_all_pixels = df_new["array_bins"].sum(axis=0) / 121

    # PF = PeakFinder(avg_all_pixels, source="co57")
    PF = PeakFinder(avg_all_pixels, source="am241")
    # PF = PeakFinder(avg_all_pixels, threshold=0.1, source="Cs137")
    
    # PF.plot_calibrated_peaks(show=False)
    # PF.plot_array(show=False)
    PF.find_peaks_scipy()
    ic(PF.peak_bins, PF.properties, PF.peak_heights)
    PF.find_largest_peak()
    PF.plot_peaks(show=True)

    ic(PF.largest_peak_bin)
    peak_count = PF.calculate_peak_count(
        avg_all_pixels, PF.largest_peak_bin, peak_halfwidth=25
    )
    print(f"Peak count: {peak_count:.2f}")
