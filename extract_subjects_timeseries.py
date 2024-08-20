import os
from pathlib import Path
import pandas as pd
import numpy as np
from multiprocessing import Pool
from typing import Union, List
from extract_timeseries import extract_timeseries, visualize_timeseries


def process_subject_extract(args):
    """
    Processes a single subject: extracts timeseries and saves it.
    Optionally, visualizes the timeseries data.

    Args:
        args (tuple): See args in the `main` function, with the addition of:
        subject_id (str): Subject ID.
    
    Raises:
        Exception: If no valid timeseries is extracted for a subject.
    """
    (
        subject_id,
        ses,
        threshold,
        bold_template,
        mask_template,
        masks_root_path,
        roi_indices,
        output_dir,
        mask_type,
        error_log_path,
    ) = args

    bold_path_template = bold_template.format(
        subject=subject_id, ses=ses, threshold=threshold
    )
    mask_file_template = mask_template.format(subject_id=subject_id)

    fmri_file = Path(bold_path_template)
    atlas_file = masks_root_path / mask_file_template

    print(f"--- Processing subject: {subject_id} ---")

    # Process masks and extract timeseries
    timeseries = extract_timeseries(atlas_file, fmri_file, mask_type, error_log_path)

    if timeseries is None or timeseries.size == 0:
        print(f"No valid timeseries extracted for subject {subject_id}")
        return

    # Save the extracted timeseries
    timeseries_output_path = output_dir / f"{subject_id}_timeseries.csv"
    print(f"Saving extracted timeseries to {timeseries_output_path}")
    np.savetxt(timeseries_output_path, timeseries, delimiter=",")

    # Run this line if you want to visualize the data
    # visualize_timeseries(subject_id, timeseries, roi_indices)

    print(f"Processing completed for subject: {subject_id}")


def main(
    ses: str,
    threshold: float,
    todo_path: Union[str, Path],
    masks_root_path: Union[str, Path],
    output_dir: Union[str, Path],
    bold_template: str,
    mask_template: str,
    mask_type: str,
    roi_indices: List[int],
    multi: bool = False,
):
    """
    Main function to run the script.

    This function defines session timepoints, data directories, and processes subjects' timeseries
    data either sequentially or in parallel based on the multi flag.

    Args:
        ses (str): Session (timepoint).
        threshold (float): Threshold value for scrubbing.
        todo_path (Union[str, Path]): Path to the todo file with subject IDs to be processed.
        masks_root_path (Union[str, Path]): Path where DK select-ROI masks are stored.
        error_log_path (Union[str, Path]): Path to log the error file.
        output_dir (Union[str, Path]): Path where processed data will be output.
        bold_template (str): Path / template for the location of BOLD data.
        mask_template (str): Template for the name of mask files.
        roi_indices (List[int]): ROI indices for timeseries visualization (e.g. add the index for the ROI/s you want to visualize).
        mask_type (str): Type of the mask ("3D" or "4D").
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

    args = [
        (
            subject,
            ses,
            threshold,
            bold_template,
            mask_template,
            masks_root_path,
            roi_indices,
            output_dir,
            mask_type,
            error_log_path,
        )
        for subject in todo
    ]

    if multi:
        with Pool(6) as pool:
            pool.map(process_subject_extract, args)
    else:
        for arg in args:
            process_subject_extract(arg)


if __name__ == "__main__":
    ses = "01"
    threshold = "0.5"
    todo_file = Path("/home/rachel/Desktop/fMRI Analysis/todo.csv")
    masks_root_path = Path("/home/rachel/Desktop/fMRI Analysis/DK76")
    output_directory = Path("/home/rachel/Desktop/fMRI Analysis/DK76/timeseries")
    root_directory = Path("/home/rachel/Desktop/fMRI Analysis/Scrubbed data")

    roi_indices = [0]  # ROIs to visualize

    bold_template = os.path.join(
        root_directory,
        "{subject}",
        "native_T1",
        "{subject}_ses-{ses}_run-01_rest_bold_ap_T1-space_scrubbed_{threshold}.nii.gz",
    )
    mask_template = "{subject_id}_DK76_BOLD-nativespace_selected_ROIs.nii.gz"

    mask_type = "3D"  # or "4D"

    main(
        ses=ses,
        threshold=threshold,
        todo_path=todo_file,
        masks_root_path=masks_root_path,
        output_dir=output_directory,
        bold_template=bold_template,
        mask_template=mask_template,
        mask_type=mask_type,
        roi_indices=roi_indices,
        multi=False,
    )

    # Uncomment this line to enable parallel processing
    # main(ses=ses, threshold=threshold, todo_path=todo_file, masks_root_path=masks_root_path, output_dir=output_directory, bold_template=bold_template, mask_template=mask_template, mask_type=mask_type, roi_indices=roi_indices, multi=True)
