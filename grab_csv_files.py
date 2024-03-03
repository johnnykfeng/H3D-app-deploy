""" grab_csv_files.py
This script is used to grab all the CSV files in a given directory 
and its subdirectories, and save them to a destination folder.
"""
import os
from icecream import ic
import shutil
    
def find_csv_files(directory: str) -> list[str]: 
    """Find all CSV files in the given directory and its subdirectories"""
    csv_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    return csv_files

def save_csv_files(directory: str, destination_dir: str):
    """Save all CSV files in the given directory and its subdirectories to the destination folder"""
    csv_files = find_csv_files(directory)
    for source_file in csv_files:
        ic(source_file)
        filename = os.path.basename(source_file)
        ic(filename)
        destination_file = os.path.join(destination_dir, os.path.basename(source_file))
        ic(destination_file)
        shutil.copy2(source_file, destination_file)

if __name__ == "__main__":
    source_directory = r"Y:\M2766\R&D\Jira-RD-748" # Yuxin's data
    csv_files = find_csv_files(source_directory)
    # ic(csv_files)
    # Destination folder in the local repository
    destination_dir = r"C:\Users\10552\OneDrive - Redlen Technologies\Code\H3D-app-deploy\data\leaky_pixel_data" 
    save_csv_files(source_directory, destination_dir)
    
    