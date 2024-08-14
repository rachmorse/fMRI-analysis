import os
from pathlib import Path
import pandas as pd
from multiprocessing import Pool
from typing import List, Union
import nibabel as nib
from datetime import datetime
from extract_timeseries import *  # Import the functions from the other scripts
from functional_connectivity import *


def process_subject(args):
    """
    Processes a single subject: extracts timeseries, computes connectivity, saves matrix, and visualizes results.

    Args:
        args (tuple): Contains subject information and configuration parameters.
    """
    (
        subject_id,
        ses,
        threshold,
        bold_template,
        mask_template,
        masks_root_path,
        output_dir,
        roi_indices,
        mask_type,
        error_log_path,
        selected_rois_csv,
        roi_column_name,
        subjects,
    ) = args

    bold_path_template = bold_template.format(
        subject=subject_id, ses=ses, threshold=threshold
    )
    mask_file_template = mask_template.format(subject_id=subject_id)

    fmri_file = Path(bold_path_template)
    atlas_file = masks_root_path / mask_file_template

    # Load BOLD image
    print(f"--- Processing subject: {subject_id} ---")
    print("Reading BOLD image...")
    try:
        bold_img = nib.load(fmri_file).get_fdata()
        print("BOLD image loaded")
    except FileNotFoundError:
        print(f"BOLD file not found: {fmri_file}")
        return
    except Exception as e:
        print(f"Error loading BOLD image: {e}")
        with open(error_log_path, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Error loading BOLD image for subject {subject_id}:\n")
            f.write(f"{str(e)}\n\n")
        return

    # Process masks and extract timeseries
    timeseries = extract_timeseries(atlas_file, fmri_file, mask_type, error_log_path)

    if timeseries is None or timeseries.size == 0:
        print(f"No valid timeseries extracted for subject {subject_id}")
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
    ses: str,
    threshold: float,
    todo_path: Union[str, Path],
    masks_root_path: Union[str, Path],
    output_dir: Union[str, Path],
    bold_template: str,
    mask_template: str,
    roi_indices: List[int],
    mask_type: str,
    selected_rois_csv: Path,
    roi_column_name: str,
    multi: bool = False,
):
    """
    Main function to run the script.

    This function defines session timepoints, data directories, and processes subjects' timeseries
    data either sequentially or in parallel based on the multi flag.

    Args:
        ses (str): Session timepoint.
        threshold (float): Threshold value for scrubbing.
        todo_path (Union[str, Path]): Path to the todo file with subject IDs to be processed.
        masks_root_path (Union[str, Path]): Path where DK select-ROI masks are stored.
        output_dir (Union[str, Path]): Path where processed data will be output.
        bold_template (str): Path / template for the location of BOLD data.
        mask_template (str): Template for the name of mask files.
        roi_indices (List[int]): Indices of ROIs for timeseries visualization.
        mask_type (str): Type of the mask ("3D" or "4D").
        selected_rois_csv (Path): Path to the selected ROIs CSV.
        roi_column_name (str): Name of the column containing ROI names.
        multi (bool): If True, enables parallel processing using multiprocessing. Defaults to False.
    """
    output_dir = Path(output_dir)
    todo_path = Path(todo_path)
    masks_root_path = Path(masks_root_path)
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
            ses,
            threshold,
            bold_template,
            mask_template,
            masks_root_path,
            output_dir,
            roi_indices,
            mask_type,
            error_log_path,
            selected_rois_csv,
            roi_column_name,
            subjects,
        )
        for subject in todo
    ]

    if multi:
        with Pool(6) as pool:
            pool.map(process_subject, args)
    else:
        for arg in args:
            process_subject(arg)


if __name__ == "__main__":
    ses = "01"
    threshold = "0.5"
    todo_file = Path("/home/rachel/Desktop/fMRI Analysis/todo.csv")
    masks_root_path = Path("/home/rachel/Desktop/fMRI Analysis/DK76")
    output_directory = Path(
        "/home/rachel/Desktop/fMRI Analysis/DK76/connectivity_matrices"
    )
    root_directory = Path("/home/rachel/Desktop/fMRI Analysis/Scrubbed data")
    selected_rois_csv = Path(
        "/pool/guttmann/laboratori/scripts/BOLD_connectivity/chosen_areas.csv"
    )
    roi_column_name = "LabelName"

    bold_template = os.path.join(
        root_directory,
        "{subject}",
        "native_T1",
        "{subject}_ses-{ses}_run-01_rest_bold_ap_T1-space_scrubbed_{threshold}.nii.gz",
    )
    mask_template = "{subject_id}_DK76_BOLD-nativespace_selected_ROIs.nii.gz"

    roi_indices = [0]  # ROIs to visualize
    mask_type = "3D"  # or "4D"

    main(
        ses=ses,
        threshold=threshold,
        todo_path=todo_file,
        masks_root_path=masks_root_path,
        output_dir=output_directory,
        bold_template=bold_template,
        mask_template=mask_template,
        roi_indices=roi_indices,
        mask_type=mask_type,
        selected_rois_csv=selected_rois_csv,
        roi_column_name=roi_column_name,
        multi=False,
    )

    # Uncomment this line to enable parallel processing
    # main(ses=ses, threshold=threshold, todo_path=todo_file, masks_root_path=masks_root_path, output_dir=output_directory, bold_template=bold_template, mask_template=mask_template, roi_indices=roi_indices, mask_type=mask_type, selected_rois_csv=selected_rois_csv, roi_column_name=roi_column_name, multi=True)