import os
from pathlib import Path
import numpy as np
from nilearn.input_data import NiftiLabelsMasker
import nibabel as nib
from datetime import datetime
from typing import Optional


def extract_timeseries(
    atlas_file: str, fmri_file: str, mask_type: str, error_log_path: Path
) -> Optional[np.ndarray]:
    """
    Extracts timeseries data from an fMRI BOLD image using an atlas mask,
    considers both 3D and 4D masks, and logs errors to a file.

    Args:
        atlas_file (str): Path to the atlas file (mask).
        fmri_file (str): Path to the fMRI preprocessed BOLD image file.
        mask_type (str): Type of the mask ("3D" or "4D").
        error_log_path (Path): Path to the error log file.

    Returns:
        np.ndarray: Extracted timeseries data, or None if an error occurred.
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
