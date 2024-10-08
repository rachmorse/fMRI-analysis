import os
from pathlib import Path
import numpy as np
from nilearn.input_data import NiftiLabelsMasker
import nibabel as nib
from datetime import datetime
from typing import List, Optional
import matplotlib.pyplot as plt


def extract_timeseries(
    atlas_file: str, fmri_file: str, mask_type: str, error_log_path: Path
) -> Optional[np.ndarray]:
    """
    Extracts timeseries data from a BOLD image using an atlas mask,
    considers both 3D and 4D atlases, and logs errors to a file.

    Args:
        atlas_file (str): Path to the atlas file (mask).
        fmri_file (str): Path to the fMRI preprocessed BOLD image file.
        mask_type (str): Type of the mask ("3D" or "4D").
        error_log_path (Path): Path to the error log file.

    Returns:
        np.ndarray: Extracted timeseries data, or None if an error occurred.

    Raises:
        FileNotFoundError: If the fMRI or atlas file is not found.
        ValueError: If the mask type is not recognized.
    """
    try:
        if not os.path.exists(fmri_file):
            raise FileNotFoundError(f"fMRI file {fmri_file} not found.")

        if not os.path.exists(atlas_file):
            raise FileNotFoundError(f"DK atlas file {atlas_file} not found.")

        # Load the atlas file
        atlas_img = nib.load(atlas_file)

        if mask_type == "3D":
            masker = NiftiLabelsMasker(labels_img=atlas_img, standardize=False)
            print("Extracting timeseries...")
            timeseries = masker.fit_transform(fmri_file)

        elif mask_type == "4D":
            print("Extracting timeseries...")
            timeseries_list = []
            for i in range(atlas_img.shape[-1]):  # Iterate over the 4th dimension
                masker = NiftiLabelsMasker(
                    labels_img=nib.Nifti1Image(
                        atlas_img.dataobj[..., i], atlas_img.affine
                    ),
                    standardize=False,
                )
                timeseries = masker.fit_transform(fmri_file)
                timeseries_list.append(timeseries)

            # Concatenate the timeseries from each mask volume
            timeseries = np.concatenate(timeseries_list, axis=1)

        else:
            raise ValueError(
                f"Unrecognized mask type {mask_type}. Should be '3D' or '4D'."
            )

        return timeseries

    except Exception as e:
        with open(error_log_path, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Error processing atlas {atlas_file} and fMRI {fmri_file}:\n")
            f.write(f"{str(e)}\n\n")
        return None


def visualize_timeseries(
    subject_id: str,
    timeseries: np.ndarray,
    roi_indices: List[int],
):
    """
    Visualize the timeseries for specified ROIs.

    Args:
        subject_id (str): Subject ID.
        timeseries (np.ndarray): The timeseries data to be visualized.
        roi_indices (List[int]): List of ROI indices to visualize.
    """
    # Visualize Timeseries for specified ROIs
    for idx in roi_indices:
        plt.figure(figsize=(10, 4))
        plt.plot(timeseries[:, idx])
        plt.title(f"Timeseries for ROI {idx} - Subject {subject_id}")
        plt.xlabel("Time points")
        plt.ylabel("BOLD signal")
        plt.show()
