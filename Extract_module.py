import pandas as pd
import numpy as np
import os
import csv
from typing import List, Tuple
from icecream import ic


class ExtractModule:
    """
    A class for extracting and transforming data from a CSV file.

    Parameters:
    - csv_file (str): The file path of the CSV file from H3D software.

    Methods:
    - count_lines(csv_file): Counts the number of lines in the CSV file.
    - find_line_number(csv_file, target_string): Finds the line numbers where the target string is found.
    - find_start_end_lines(target_string, extra_lines, module_number): Finds the start and end lines for extraction.
    - extract_module2df(module_number): Extracts the module data as a DataFrame.
    - transform_df(df, bin_peak, bin_width, n_bins): Transforms the DataFrame by adding new columns and calculating counts.
    """

    def __init__(self, csv_file):
        if csv_file.endswith(".xlsx"):
            print("You entered a .xlsx file")
            alternate_csv_file = csv_file.replace(".xlsx", ".csv")
            if not os.path.exists(
                alternate_csv_file
            ):  # check if the file has been converted
                print(f"Converting {csv_file} to {alternate_csv_file}...")
                self.csv_file = self.convert_xlsx_to_csv(csv_file)
            else:
                print(f"Found {alternate_csv_file}, load that instead.")
                self.csv_file = alternate_csv_file
        else:
            self.csv_file = csv_file

        # self.csv_file = csv_file # file path of the csv file from H3D software
        self.target_string = "H3D_Pixel"  # string to search for in the csv file
        self.number_of_pixels = (
            121  # determines number of rows to extract from csv file
        )
        self.n_pixels_x = 11  # number of pixels in x direction
        self.n_pixels_y = 11  # number of pixels in y direction
        self.total_line_count = self.count_lines()  # this is not used, but nice to have
        self.line_numbers = []
        self.start_line = None  # output of find_start_end_lines
        self.end_line = None  # output of find_start_end_lines
        self.extra_lines = 0
        self.dataframe = None  # output of extract_module2df
        self.all_df = []  # output of extract_all_modules2df
        self.all_df_new = []  # output of transform_all_df
        self.N_DF = 0  # number of DataFrames in the list

    def convert_xlsx_to_csv(self, input_xlsx_file):
        df = pd.read_excel(input_xlsx_file)
        output_csv_file = input_xlsx_file.replace(".xlsx", ".csv")
        df.to_csv(output_csv_file, index=False)
        return output_csv_file

    def count_lines(self):
        """
        Counts the number of lines in the CSV file.
        """
        try:
            with open(self.csv_file, "r") as file:
                return sum(1 for line in file)
        except:
            print("File not found")
            return None

    def find_line_number(self, csv_file, target_string):
        """
        Finds the line numbers where the target string is found in the CSV file.

        Parameters:
        - csv_file (str): The file path of the CSV file.
        - target_string (str): The string to search for.

        Returns:
        - list: The line numbers where the target string is found.
        """
        # line_numbers = []
        with open(csv_file, "r") as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                for cell in row:
                    if target_string in cell:
                        line_number = i + 1
                        self.line_numbers.append(line_number)
                        # print(f"{target_string} found at line: {line_number}")
                        break
        # self.line_numbers = line_numbers
        return self.line_numbers

    def find_start_end_lines(
        self, target_string: str, extra_lines=0, module_number=3
    ) -> Tuple[int, int]:
        """
        Finds the start and end lines for extraction.

        Parameters:
        - target_string (str): The string to search for in the CSV file.
        - extra_lines (int): The number of extra lines to include before and after the module data.
        - module_number (int): The module number (1-4) to extract.

        Returns:
        - tuple: The start and end lines for extraction.
        """
        if self.line_numbers == []:
            _ = self.find_line_number(self.csv_file, target_string)

        if type(module_number) != int:
            print("Module number must be an integer")
            return None

        self.extra_lines = extra_lines
        start_line = self.line_numbers[module_number - 1] - extra_lines
        # + 1 to include the header line
        end_line = start_line + self.number_of_pixels + extra_lines + 1
        self.start_line, self.end_line = start_line, end_line
        return start_line, end_line

    def extract_module2df(self, module_number=3) -> pd.DataFrame:
        """
        Extracts the module data from the CSV file as a DataFrame.

        Parameters:
        - module_number (int): The module number (1-4) to extract.

        Returns:
        - pandas.DataFrame: The extracted module data.
        """
        start_line, end_line = self.find_start_end_lines(
            self.target_string, module_number=module_number
        )
        start_lines_to_skip = np.arange(0, start_line - 1)
        n_rows = (end_line - start_line) - 1

        self.dataframe = pd.read_csv(
            self.csv_file,
            skiprows=start_lines_to_skip,
            nrows=n_rows,
            index_col=self.target_string,
            header=0,
        )
        return self.dataframe

    def extract_all_modules2df(self) -> List[pd.DataFrame]:
        """
        Extracts all the module data from the CSV file as a DataFrame.

        Returns:
        - pandas.DataFrame: The extracted module data.
        """
        if self.line_numbers == []:
            self.find_line_number(self.csv_file, self.target_string)

        for i in range(len(self.line_numbers)):
            df_module = self.extract_module2df(
                module_number=i + 1
            )  # module_number is 1-based indexed
            self.all_df.append(df_module)
        self.N_DF = len(self.all_df)
        return self.all_df
    
    @property
    def number_of_modules(self):
        return len(self.all_df)


class TransformDf:
    def __init__(
        self,
        if_calculate_peak_count: bool = True,
    ):
        self.df_transformed_list = []
        self.N_DF = None
        self.if_calculate_peak_count = if_calculate_peak_count

    @staticmethod
    def calculate_peak_count(array: np.array, peak_bin: int, peak_halfwidth=25):
        """Calculate the counts in a peak given the array and the peak bin number."""
        peak_count = np.sum(
            array[peak_bin - peak_halfwidth : peak_bin + peak_halfwidth]
        )
        return peak_count

    @staticmethod
    def avg_neighbor_counts(df, x_index, y_index, count_type='peak_count'):
        sum_counts = 0
        neighbor_coords = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbor_counter = 0
        for dx, dy in neighbor_coords:
            nx, ny = x_index + dx, y_index + dy
            if (nx in df['x_index'].values) and (ny in df['y_index'].values):
                neighbor_counter += 1
                sum_counts += df.loc[(df['x_index']==nx) & (df['y_index']==ny), count_type].values[0]
        avg_counts = sum_counts / neighbor_counter
        return avg_counts
    
    @staticmethod
    def leaking_ratio(row, count_type='peak_count'):
        return row['peak_count'] / row['avg_neighbor_counts']

    def transform_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms a DataFrame by adding new columns and performing calculations.

        Args:
            df (pandas.DataFrame): The input DataFrame.
            bin_peak (int): The peak bin index, used to calculate the peak counts.
            bin_width (int, optional): The width of the bin range. Defaults to 25.
            n_bins (int, optional): The number of bin columns in the DataFrame. Defaults to 2000.

        Returns:
            pandas.DataFrame: The transformed DataFrame with additional columns.

        """
        # make new empty columns
        df["x_index"] = np.nan
        df["y_index"] = np.nan

        for xi in range(11):
            for yi in range(11):
                df.loc[xi * 11 + yi + 1, "x_index"] = xi + 1
                df.loc[xi * 11 + yi + 1, "y_index"] = yi + 1

        # change data type to save memory
        df["x_index"] = df["x_index"].astype(int)
        df["y_index"] = df["y_index"].astype(int)

        # slice the bin columns only
        df_bins = df.iloc[:, :]

        df_new = df[
            ["x_index", "y_index"]
        ].copy()  # must use .copy(), pandas will give a warning
        df_new["pixel_id"] = df_new.index
        df_new["array_bins"] = df_bins.apply(lambda row: np.array(row), axis=1)

        df_new["total_count"] = df_new["array_bins"].apply(sum)
        df_new["total_count"] = df_new["total_count"].astype(int)
        df_new["total_counts_norm"] = round(
            df_new["total_count"] / df_new["total_count"].max(), 3
        )
        df_new["is_edge"] = (
            (df_new["x_index"] == 1)
            | (df_new["x_index"] == 11)
            | (df_new["y_index"] == 1)
            | (df_new["y_index"] == 11)
        )

        return df_new

    def add_peak_counts(self, df_new: pd.DataFrame, bin_peak, bin_width) -> pd.DataFrame:
        """Add the peak_count and non_peak_count columns to the DataFrame."""
        df_new["peak_count"] = df_new["array_bins"].apply(
            lambda x: self.calculate_peak_count(x, bin_peak, bin_width)
        )
        df_new["non_peak_count"] = df_new["total_count"] - df_new["peak_count"]
        
        return df_new  

    def transform_all_df(self, extracted_df_list: List[pd.DataFrame]):
        """
        Transforms all the DataFrames in the list.

        Args:
            n_bins (int, optional): The number of bin columns in the DataFrame. Defaults to 2000.

        Returns:
        - list: The transformed DataFrames with additional columns.
        """
        if extracted_df_list == []:
            raise ValueError("The input list is empty.")

        self.df_transformed_list = []  # reset the list
        for df in extracted_df_list:
            df_new = self.transform_df(df)
            self.df_transformed_list.append(df_new)
        self.N_DF = len(self.df_transformed_list)
        return self.df_transformed_list
    
    def add_peak_counts_all(self, bin_peak, bin_width):
        """Add the peak counts to all the DataFrames in the list."""
        for df_new in self.df_transformed_list:
            df_new = self.add_peak_counts(df_new, bin_peak, bin_width)
        return self.df_transformed_list


# useful function not part of any class
def extract_metadata(file_path, search_pattern, occurrence):
    """
    Input:
    - file_path (str): The file path of the CSV file.
    - search_pattern (str): The string to search for in the CSV file.
    - occurrence (int): The desired occurrence of the search pattern.
    Output:
    - str: The value found in the cell to the right of the search pattern.

    Extracts specific metadata from a CSV file.
    1. Open the CSV file and iterate through each row and cell.
    2. Search for the target string in each cell.
    3. If the target string is found, get the value in the cell to the right.
    4. Return the value if the desired occurrence is found.
    """
    # open CSV file
    with open(file_path, "r") as csvfile:
        reader = csv.reader(csvfile)
        # track the number of occurrences found
        occurrences_found = 0
        # iterate the rows in the CSV
        for row in reader:
            # iterate the cells in the row
            for cell in range(3):
                # check if the stage coordinates string is in the cell
                if search_pattern in row[cell]:
                    occurrences_found += 1
                    # check if this is the desired occurrence
                    if (
                        occurrences_found == occurrence + 1
                    ):  # need +1 to get the correct occurrence
                        # get the number value in the cell to the right of the string
                        if cell < len(row) - 1:
                            return row[cell + 1]
                        else:
                            return None  # return none if there is no value to the right
    return None  # return None if occurrence is not found


def extract_metadata_list(file_path, search_pattern):
    """
    Input:
    - file_path (str): The file path of the CSV file.
    - search_pattern (str): The string to search for in the CSV file.
    Output:
    - list: A list of values found in the cells to the right of the search pattern.

    Extracts specific metadata from a CSV file.
    1. Open the CSV file and iterate through each row and cell.
    2. Search for the target string in each cell.
    3. If the target string is found, get the value in the cell to the right.
    4. Append the value to a list.
    5. Return the list of values.
    """
    # open CSV file
    with open(file_path, "r") as csvfile:
        reader = csv.reader(csvfile)
        # create an empty list to store the values
        values = []
        # iterate the rows in the CSV
        for row in reader:
            # iterate the cells in the row
            for cell in range(3):
                # check if the stage coordinates string is in the cell
                if search_pattern in row[cell]:
                    # get the number value in the cell to the right of the string
                    if cell < len(row) - 1:
                        values.append(row[cell + 1])
                    else:
                        values.append(
                            None
                        )  # append none if there is no value to the right
    return values  # return the list of values


class OrganizeData:
    """
    Input: df_transformed_list (list): A list of transformed DataFrames from the ExtractModule class.

    Output: all_data_dict (dict): A dictionary containing the following keys:
        - df (pandas.DataFrame): The original DataFrame.
        - heatmap_table (pandas.DataFrame): A pivot table for the heatmap.
        - edge_pixels_df (pandas.DataFrame): A DataFrame containing the edge pixels.
        - interior_pixels_df (pandas.DataFrame): A DataFrame containing the interior pixels.
        - max_total_counts (int): The maximum total counts.
        - sum_total_counts (int): The sum of total counts.
    """

    def __init__(self, df_transformed_list, csv_file, include_peak_count=False):
        self.df_transformed_list = df_transformed_list
        self.N_MODULES = len(df_transformed_list)
        self.csv_file = csv_file
        self.include_peak_count = include_peak_count
        self.x_positions = None
        self.y_positions = None
        self.all_data_dict = self.organize_all_data()
        self.df_plot = None

    def organize_all_data(self):
        """Main method to organize the data."""
        all_data_dict = {}

        for i, df in enumerate(self.df_transformed_list):
            heatmap_table = df.pivot_table(
                index="y_index", columns="x_index", values="total_count"
            )
            max_total_counts = df["total_count"].max()
            sum_total_counts = df["total_count"].sum()
            avg_total_counts = round(df["total_count"].mean(), 1)
            edge_pixels_df = df[df["is_edge"] == True]
            interior_pixels_df = df[df["is_edge"] == False]
            all_data_dict[i] = {
                "df": df,
                "heatmap_table": heatmap_table,
                "pixel_id_map": df.pivot_table(
                    index="y_index", columns="x_index", values="pixel_id"
                ),
                "edge_pixels_df": edge_pixels_df,
                "interior_pixels_df": interior_pixels_df,
                "max_total_counts": max_total_counts,
                "sum_total_counts": sum_total_counts,
                "avg_total_counts": avg_total_counts,
            }
            if self.include_peak_count:
                heatmap_peak_table = df.pivot_table(
                    index="y_index", columns="x_index", values="peak_count"
                )
                heatmap_non_peak_table = df.pivot_table(
                    index="y_index", columns="x_index", values="non_peak_count"
                )
                all_data_dict[i]["heatmap_peak"] = heatmap_peak_table
                all_data_dict[i]["heatmap_non_peak"] = heatmap_non_peak_table
                all_data_dict[i]["avg_peak_counts"] = round(df["peak_count"].mean(), 1)
                all_data_dict[i]["avg_non_peak_counts"] = round(df["non_peak_count"].mean(), 1)
            
        return all_data_dict

    def organize_line_plots(self):
        """
        Organizes the data for the line plots.
        Skips the first two x and y positions since they are background measurements.
        """
        self.x_positions = extract_metadata_list(
            self.csv_file, "Stage position x (in mm):"
        )
        x_positions = self.x_positions[2:]  # skip the first two
        self.y_positions = extract_metadata_list(
            self.csv_file, "Stage position y (in mm):"
        )
        y_positions = self.y_positions[2:]  # skip the first two

        df_plot_rows = []
        counter = 0
        for x_idx in range(1, 12):
            for y_idx in range(1, 12):
                counter += 1
                pixel_total_counts_list = []
                pixel_peak_counts_list = []
                pixel_non_peak_counts_list = []
                for i in range(2, self.N_MODULES):
                    df = self.all_data_dict[i]["df"]
                    pixel_df = df[(df["x_index"] == x_idx) & (df["y_index"] == y_idx)]
                    pixel_total_counts = pixel_df["total_count"].values[0]
                    pixel_total_counts_list.append(pixel_total_counts)
                    
                    if self.include_peak_count:
                        peak_count = pixel_df["peak_count"].max()
                        non_peak_count = pixel_df["non_peak_count"].max()
                        pixel_peak_counts_list.append(peak_count)
                        pixel_non_peak_counts_list.append(non_peak_count)
                        

                df_plot_rows.append(
                    {
                        "H3D_pixel": counter,  # 1 to 121
                        "x_index": x_idx,  # x_idx is an integer 1 to 11
                        "y_index": y_idx,  # y_idx is an integer 1 to 11
                        "x_position": x_positions,  # x_positions is a list
                        "y_position": y_positions,  # y_positions is a list
                        "total_counts": pixel_total_counts_list,  # also a list
                    }
                )
                if self.include_peak_count:
                    df_plot_rows[-1]["peak_counts"] = pixel_peak_counts_list
                    df_plot_rows[-1]["non_peak_counts"] = pixel_non_peak_counts_list
                    
                    
        self.df_plot = pd.DataFrame(df_plot_rows)
        return self.df_plot


# Example usage
if __name__ == "__main__":
    # xlsx_file = r"data_analysis\Co57_CsEval_2000V_2min_b.xlsx"
    csv_file = r"data\Co57_2mins_2000V_20cycles.csv"
    EM = ExtractModule(csv_file)
    all_df = EM.extract_all_modules2df()
    
    TD = TransformDf()
    # df_transformed_list = TD.transform_all_df(all_df)
    # df_transformed_list = TD.add_peak_counts_all(224, 25)
    TD.transform_all_df(all_df)
    TD.add_peak_counts_all(224, 25)
    
    ic(TD.df_transformed_list[0].head())
    ic(len(TD.df_transformed_list))
    
    OD = OrganizeData(TD.df_transformed_list, EM.csv_file, include_peak_count=True)
    all_data_dict = OD.all_data_dict
    N_DF = EM.number_of_modules  # number of dataframes
    ic(N_DF)
    df_plot = OD.organize_line_plots()
    print(type(df_plot))
    
    ic(df_plot.head())
    ic(df_plot.tail())
    ic(df_plot.info())
    
    del EM, TD, OD
    
    try:
        print(EM.number_of_modules)
    except Exception as e:
        print(e)