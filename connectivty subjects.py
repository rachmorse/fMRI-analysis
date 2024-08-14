from pathlib import Path
import pandas as pd
from multiprocessing import Pool
from typing import List, Union
import numpy as np
from datetime import datetime
from functional_connectivity import compute_functional_connectivity, visualize_data


def process_subject_functional(args):
    """
    Processes a single subject: loads pre-extracted timeseries, computes connectivity, saves matrix, and visualizes results.

    Args:
        args (tuple): Contains subject information and configuration parameters.
    """
    (
        subject_id,
        output_dir,
        roi_indices,
        selected_rois_csv,
        roi_column_name,
        subjects,
        error_log_path,
    ) = args

    timeseries_file = output_dir / f"{subject_id}_timeseries.csv"

    # Load extracted timeseries
    print(f"--- Processing subject: {subject_id} ---")
    print("Reading extracted timeseries...")
    try:
        timeseries = np.loadtxt(timeseries_file, delimiter=",")
        print("Timeseries loaded")
    except FileNotFoundError:
        print(f"Timeseries file not found: {timeseries_file}")
        return
    except Exception as e: 
        print(f"Error loading timeseries: {e}")
        with open(error_log_path, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Error loading timeseries for subject {subject_id}:\n")
            f.write(f"{str(e)}\n\n")
        return

    if timeseries is None or timeseries.size == 0:
        print(f"No valid timeseries loaded for subject {subject_id}")

    if timeseries is None or timeseries.size == 0:
        print(f"No valid timeseries loaded for subject {subject_id}")
        return

    # Compute and fetch connectivity matrix
    connectivity_matrix = compute_functional_connectivity(
        subject_id,
        timeseries,
        output_dir,
        selected_rois_csv=selected_rois_csv,
        roi_column_name=roi_column_name,
        subjects=subjects,
    )

    # Visualize data
    visualize_data(subject_id, connectivity_matrix, timeseries, roi_indices)

    print(f"Processing completed for subject: {subject_id}")


def main(
    todo_path: Union[str, Path],
    output_dir: Union[str, Path],
    selected_rois_csv: Path,
    roi_column_name: str,
    roi_indices: List[int],
    multi: bool = False,
):
    """
    Main function to run the script.

    This function reads the pre-extracted timeseries data for each subject,
    computes the functional connectivity matrices for all subjects, either
    sequentially or in parallel based on the multi flag.

    Args:
        todo_path (Union[str, Path]): Path to the todo file with subject IDs to be processed.
        output_dir (Union[str, Path]): Path where processed data will be output.
        selected_rois_csv (Path): Path to the selected ROIs CSV.
        roi_column_name (str): Name of the column containing ROI names.
        roi_indices (List[int]): Indices of ROIs for timeseries visualization.
        multi (bool): If True, enables parallel processing using multiprocessing. Defaults to False.
    """
    output_dir = Path(output_dir)
    todo_path = Path(todo_path)
    error_log_path = output_dir / "error_log.txt"  # Define error log path

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        todo_df = pd.read_csv(todo_path)
        todo = todo_df["todo"].tolist()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    print(f"Number of subjects to process: {len(todo)}")

    subjects = todo  # Assign subjects list
    args = [
        (
            subject,
            output_dir,
            roi_indices,
            selected_rois_csv,
            roi_column_name,
            subjects,
            error_log_path,
        )
        for subject in todo
    ]

    if multi:
        with Pool(6) as pool:
            pool.map(process_subject_functional, args)
    else:
        for arg in args:
            process_subject_functional(arg)


if __name__ == "__main__":
    todo_file = Path("/home/rachel/Desktop/fMRI Analysis/todo.csv")
    output_directory = Path("/home/rachel/Desktop/fMRI Analysis/DK76/timeseries")
    selected_rois_csv = Path(
        "/pool/guttmann/laboratori/scripts/BOLD_connectivity/chosen_areas.csv"
    )
    roi_column_name = "LabelName"

    roi_indices = [0]  # ROIs to visualize

    main(
        todo_path=todo_file,
        output_dir=output_directory,
        selected_rois_csv=selected_rois_csv,
        roi_column_name=roi_column_name,
        roi_indices=roi_indices,
        multi=False,
    )

    # Uncomment this line to enable parallel processing
    # main(todo_path=todo_file, output_dir=output_directory, selected_rois_csv=selected_rois_csv, roi_column_name=roi_column_name, roi_indices=roi_indices, multi=True)
