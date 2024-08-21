import pandas as pd
import numpy as np
import nibabel as nib
from typing import Union, List
from pathlib import Path


def main(
    selected_rois_path: Union[str, Path],
    nifti_paths: List[str],
    output_folder: Union[str, Path] = None,
):
    """
    Main function to process and save ROI-specific NIfTI images for each subject.

    This function reads a list of selected ROIs from a CSV file, then processes the
    corresponding NIfTI files to zero out ROIs that are not in the list.

    Args:
        selected_rois_path (Path): Path to the CSV file containing selected ROIs.
        nifti_paths (Path): List of NIfTI file paths to be processed (e.g. where the subject-specfic BOLD DK atlas masks are)
        output_folder (Path): Directory to save the processed NIfTI files. Default is to create a folder called 'data'.

    Raises:
        FileNotFoundError: If the `selected_rois_csv` does not exist.
        Exception: If any required file or directory is not found.
    """
    # Define output folder path
    if not output_folder:
        output_folder = Path("./data")
    else:
        output_folder = Path(output_folder)

    # Ensure output directory exists
    output_folder.mkdir(parents=True, exist_ok=True)

    # Read selected ROIs from CSV and convert the indices to a list
    try:
        selected_rois_df = pd.read_csv(selected_rois_path, index_col=0)
        selected_rois = list(selected_rois_df.index)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Selected ROIs file not found at: {selected_rois_path}"
        )

    # Process each subject's NIfTI file
    for nifti_file in nifti_paths:
        print(f"Processing NIfTI file: {nifti_file}")

        try:
            # Load the NIfTI image
            aparcaseg_image = nib.load(nifti_file)
        except FileNotFoundError:
            print(f"NIfTI file {nifti_file} does not exist. Skipping this file.")
            continue
        
        aparcaseg_data = aparcaseg_image.get_fdata()
        aparcaseg_affine = aparcaseg_image.affine

        aparcaseg_data = aparcaseg_image.get_fdata()
        aparcaseg_affine = aparcaseg_image.affine

        # Zero out regions not in the selected ROIs list
        aparcaseg_data[~np.isin(aparcaseg_data, selected_rois)] = 0

        # Create a new NIfTI image with the modified data
        rois_image = nib.Nifti1Image(aparcaseg_data, aparcaseg_affine)

        # Extract filename without any suffixes
        base_file_name = Path(nifti_file).with_suffix("").with_suffix("").name
        new_nifti_file_path = (
            output_folder / f"{base_file_name}_selected_ROIs.nii.gz"
        )

        # Save the new NIfTI image
        nib.save(rois_image, str(new_nifti_file_path))

        # Output indicating successful processing
        print(
            f"Successfully processed and saved {nifti_file} to {new_nifti_file_path}."
        )


if __name__ == "__main__":
    # Change to your paths
    todo_file = Path(
        "/home/rachel/Desktop/fMRI Analysis/todo.csv"
    )  # Path to the todo file (created in scrubbing_fMRI.py) with subject IDs to be processed.
    selected_rois_csv = Path(
        "/pool/guttmann/laboratori/scripts/BOLD_connectivity/chosen_areas.csv"
    )
    nifti_file_path = Path("/home/rachel/Desktop/fMRI Analysis/DK76")
    output_directory = Path("/home/rachel/Desktop/fMRI Analysis/DK76")

    # Define how your NIfTI files are named
    nifti_file_format = "{subject_id}_DK76_BOLD-nativespace.nii.gz"

    try:
        with open(todo_file, "r") as f:
            subjects_list = f.read().splitlines()
        subjects_list = [s for s in subjects_list if s]

        # Construct full paths to the NIfTI files
        nifti_files = [
            nifti_file_path / nifti_file_format.format(subject_id=subject_id)
            for subject_id in subjects_list
        ]

        main(
            selected_rois_path=selected_rois_csv,
            nifti_paths=nifti_files,
            output_folder=output_directory,
        )
    except FileNotFoundError:
        print(f"Todo file not found at: {todo_file}")
