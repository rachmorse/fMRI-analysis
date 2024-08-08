import os
import pandas as pd
from timeseries_extractor import TimeseriesExtractor  # Import the class from the timeseries_extractor.py file
from datetime import datetime
from multiprocessing import Pool

def timeseries_extraction(args):
    subject, root, ses, th, output_dir, extractor = args

    """
    Extracts timeseries for the given subject and saves them to the output directory.
    Handles errors by logging them to an error file.

    Parameters:
    subject (str): subject ID.
    """

    try:
        # Define paths to the BOLD image and output file for the current subject
        bold = os.path.join(
            root, subject, "native_T1", 
            f"{subject}_ses-{ses}_run-01_rest_bold_ap_T1-space_scrubbed_{th}.nii.gz"
        )
        output = os.path.join(output_dir, f"{subject}_native_timeseries.txt")

        # Extract timeseries using the TimeseriesExtractor instance
        extractor.extract_and_save_timeseries(subject, bold, output)
    except Exception as e:
        # Log errors to a central error log file
        with open(os.path.join(output_dir, "error.txt"), "a") as f:
            f.write(f"{datetime.now()}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Error: {str(e)}\n\n")


# Main function to run the script
def main(multi=False):
    """
    Main function to run the script
    
    This function defines session timepoints, data directories, and initializes
    the TimeseriesExtractor. It processes subjects' timeseries data either 
    sequentially or in parallel based on the multi flag.

    - ses: The session timepoint.
    - th: The threshold for FWD that was used for scrubbing.
    - root: The root directory containing the data to be processed.
    - output_dir: The directory where processed data will be stored.
    - todo: List of subjects to be processed, read from a CSV file.
    - extractor: TimeseriesExtractor instance to handle the extraction process.
    
    The function prints the number of subjects to process and then processes 
    the subjects either using single-threaded or multi-threaded approach.
    """
    ses = "01"
    th = "0.5"  # Threshold for FWD that was used for scrubbing.
    root = "/home/rachel/Desktop/fMRI Analysis/Scrubbed data"
    output_dir = "/home/rachel/Desktop/fMRI Analysis/DK76/timeseries"
    todo_path = "/home/rachel/Desktop/fMRI Analysis/todo.csv" # Path to the CSV file

    # Read the list of subjects from the CSV file
    try:
        todo_df = pd.read_csv(todo_path)
        todo = todo_df["todo"].tolist()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Initialize the TimeseriesExtractor
    extractor = TimeseriesExtractor(
        masks_root_path="/home/rachel/Desktop/fMRI Analysis/DK76",
        unique_mask=True
    )

    # Print the number of subjects to process
    print(f"Number of subjects to process: {len(todo)}")

    if multi:
        with Pool(6) as pool:
            pool.map(timeseries_extraction, [(subject, root, ses, th, output_dir, extractor) for subject in todo])
    else:
        for subject in todo:
            timeseries_extraction((subject, root, ses, th, output_dir, extractor))

if __name__ == '__main__':
    main()
    # main(multi=True)  # Use this for parallel processing, default is set to not run any parallel processing