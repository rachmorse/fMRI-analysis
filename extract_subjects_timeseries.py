
import os
import pandas as pd
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path
from typing import Union
from timeseries_extractor import TimeseriesExtractor  # Import the class from the timeseries_extractor.py file

def timeseries_extraction(args):
    """
    Extracts timeseries for the given subject and saves them to the output directory.
    Handles errors by logging them to an error file.

    Args:
        subject (str): subject ID.
    """
    subject, bold_path_template, output_path_template, extractor = args

    try:
        bold_path = Path(bold_path_template.format(subject=subject))
        output_path = Path(output_path_template.format(subject=subject))
        
        extractor.extract_and_save_timeseries(subject, bold_path, output_path)
    except Exception as e:
        with open(masks_root_path.parent / "error.txt", "a") as f:
            f.write(f"{datetime.now()}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Error: {str(e)}\n\n")

def main(todo_path: Union[str, Path], 
         masks_root_path: Union[str, Path], 
         output_dir: Union[str, Path], 
         bold_template: str, 
         output_template: str, 
         mask_filename_template: str, 
         multi: bool = False):
    """
    Main function to run the script
    
    This function defines session timepoints, data directories, and initializes
    the TimeseriesExtractor. It processes subjects' timeseries data either 
    sequentially or in parallel based on the multi flag.

        - todo: Path to the CSV file containing the list of subjects to be processed.
        - masks_root_path: Directory where masks are stored.
        - output_dir: The directory where processed data will be stored.
        - bold_template: Template for constructing BOLD file paths.
        - output_template: Template for naming output files.
        - mask_filename_template: Template for naming mask files.
    
    The function prints the number of subjects to process and then processes 
    the subjects either using single-threaded or multi-threaded approach.
    """
    output_dir = Path(output_dir)
    todo_path = Path(todo_path)
    masks_root_path = Path(masks_root_path)

    # Read the list of subjects from the CSV file
    try:
        todo_df = pd.read_csv(todo_path)
        todo = todo_df["todo"].tolist()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Initialize the TimeseriesExtractor
    extractor = TimeseriesExtractor(
        masks_root_path=masks_root_path,
        unique_mask=True,
        mask_filename_template=mask_filename_template
    )

    # Print the number of subjects to process
    print(f"Number of subjects to process: {len(todo)}")

    args = [(subject, 
             bold_template.format(subject=subject), 
             output_template.format(subject=subject), 
             extractor) for subject in todo]

    if multi:
        with Pool(6) as pool:
            pool.map(timeseries_extraction, args)
    else:
        for subject_args in args:
            timeseries_extraction(subject_args)

if __name__ == '__main__':
    # Change to your paths
    todo_file = Path("/home/rachel/Desktop/fMRI Analysis/todo.csv")
    masks_root_path = Path("/home/rachel/Desktop/fMRI Analysis/DK76")
    output_directory = Path("/home/rachel/Desktop/fMRI Analysis/DK76/timeseries")
    root_directory = Path("/home/rachel/Desktop/fMRI Analysis/Scrubbed data")
    
    bold_path_template = os.path.join(root_directory, "{subject}", "native_T1", "{subject}_ses-01_run-01_rest_bold_ap_T1-space_scrubbed_0.5.nii.gz")
    output_file_template = str(output_directory / "{subject}_native_timeseries.txt")
    mask_file_template = "{subject_id}_DK76_BOLD-nativespace_selected_ROIs.nii.gz"

    main(todo_path=todo_file, 
         masks_root_path=masks_root_path, 
         output_dir=output_directory, 
         bold_template=bold_path_template, 
         output_template=output_file_template,
         mask_filename_template=mask_file_template, 
         multi=False)
    # main(multi=True)  # Uncomment to enable multi-processing