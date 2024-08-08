
# fMRI Analysis

For functional connectivity analysis with the [Desikan-Killiany (DK) Atlas](https://surfer.nmr.mgh.harvard.edu/fswiki/CorticalParcellation). 

## Table of Contents

- [Overview](#overview)
- [Scripts](#scripts)
- [Setup](#setup)

## Overview

This repository contains several Python scripts designed for fMRI scrubbing, DK atlas registration, ROI selection, timeseries extraction, and functional connectivity calculation. 

Below is the description and the usage of each script included in this repository.

## Scripts

1. **`scrubbing_fMRI.py`**
    - **Purpose:** Scrubs fMRI BOLD images by either cutting or interpolating scans based on Framewise Displacement (FWD) thresholds to mitigate motion artifacts.
    - **Functions:**
        - `analyze_threshold(df, threshold, total_scans, affected_percentage)`: Analyzes and visualizes subjects' significant movement above a given FWD threshold.
        - `scrub(bold_file, fwd_file, scrubbed_file, th, method)`: Scrubs the BOLD images based on the FWD threshold using specified methods ('cut' or 'interpolate').
        - `process_subject(subject, ses, root, th, output_data, error_log)`: Processes an individual subject’s BOLD files and scrubs them.
    - **Notes:**
        - Adjust paths for root, output and session (`ses`) as necessary.
        - The script supports parallel processing to speed up execution.
    - **Key Terms:**
        - *Framewise Displacement (FWD)*
            - A measure in fMRI analysis to quantify the amount of head movement between consecutive scans. It captures both translational (linear) and rotational (angular) movements, providing a single value that indicates the total displacement of the head. FWD is calculated as the sum of the absolute differences in head position and rotation between successive frames.
        - *Scrubbing*
            - The process of removing or correcting fMRI data points that are affected by motion artifacts. Scrubbing aims to improve the quality of the data by mitigating the effects of head movement. It replaces timeseries values that are affected by significant movement with an estimated timeseries value using interpolation or extrapolation. 
        - *Interpolation*
            - The process of estimating unknown values (in this case, values removed due to high FWD values) that are within the range of known values.
                - *Example:*
                    Imagine you have data points for tp 1, 2, 4, and 5, but the value for tp 3 has been removed because of high movement at tp 3:
                    ```
                    Time:   1   2  3   4   5
                    Value: 10  20  ??  40  50
                    ```
                    Interpolation estimates the missing value at tp 3 based on known neighboring values. 
        - *Extrapolation*
            - The process of estimating unknown values (in this case, values removed due to high FWD values) that are outside the range of known values.
                - *Example:*
                    Imagine you have data points at tp 1, 2, 3, and 4, but you need to estimate the value at tp 5:
                    ```
                    Time:   1   2   3   4  5
                    Value: 10  20  30  40 ??
                    ```
                    Using extrapolation, you estimate the value at tp 5 based on the trend from the known values. 

2. **`transform_dk_atlas_native_space.py`**
    - **Purpose:** Transform the DK atlas from standard space to the subject's native BOLD space using `mri_vol2vol` from FreeSurfer.
    - **Functions:**
        - `main()`: Main function to process each subject by ensuring that necessary files exist and then executing the transformation command.
    - **Notes:**
        - Adjust paths such as `freesurfer_folder`, `bids_folder`, `output_folder`, and `todo_file` to match your data structure.
        - This script relies on FreeSurfer tools and environment setup.
    - **Key Terms:**
        - *Nearest Neighbor Interpolation*
            - A type of interpolation that assigns the value of the nearest known data point to the unknown data point. This method is often used in image processing to maintain discrete labels, like in ROIs.


3. **`select_specific_rois.py`**
    - **Purpose:** Processes and saves specific ROIs from the DK atlas in the native BOLD space, zeroing out other regions not listed as chosen.
    - **Functions:**
        - `main()`: Main function to load subjects and chosen ROIs, then process and save the specified ROIs for each subject.
    - **Notes:**
        - Adjust paths for the `output_folder` and change the file paths for chosen areas and subjects list.

4. **`timeseries_extractor.py`**
    - **Purpose:** Defines a class for extracting timeseries data from fMRI BOLD images using the DK mask in native BOLD space.
    - **Class:** `TimeseriesExtractor`
        - **Attributes:**
            - `masks_root_path`: Path where mask files are stored.
            - `unique_mask`: Boolean flag indicating if masks are unique per subject.
        - **Methods:**
            - `extract_and_save_timeseries(subject_id, bold_file_path, output_file)`: Extracts timeseries and saves to output file.
            - `multiple internal methods`: Supporting methods for mask processing and timeseries extraction.

5. **`extract_subjects_timeseries.py`**
    - **Purpose:** Runs the timeseries extraction process for multiple subjects using `TimeseriesExtractor`.
    - **Functions:**
        - `timeseries_extraction(args)`: Extracts timeseries for an individual subject.
        - `main(multi)`: Main function to initialize the extractor and process all subjects either sequentially or in parallel.
    - **Notes:**
        - Adjust paths such as `root`, `output_dir`, and `todo_path`.

6. **`compute_functional_connectivity.py`**
    - **Purpose:** Defines a class to compute various functional connectivity metrics from timeseries data.
    - **Class:** `FC`
        - **Attributes:**
            - `fisher_ztrans`: Flag for applying Fisher z-transformation.
        - **Methods:**
            - `load_timeseries(filepath, index)`: Loads timeseries data from a file.
            - `one_to_all(subject_id, one_timeseries_path, all_timeseries_path, one_timeseries_index)`: Computes one-to-all FC.
            - `multiple_one_to_all(subjects, one_timeseries_files, all_timeseries_files, one_timeseries_index)`: Computes one-to-all FC for multiple subjects.
            - `all_to_all(subject_id, timeseries_path)`: Computes all-to-all Pearson correlations.
            - `multiple_all_to_all(subjects, timeseries_files)`: Computes all-to-all correlations for multiple subjects.
            - `all_to_all_from_img(subject_id, bold_img, mask_img)`: Computes all-to-all correlations from BOLD and mask images.

7. **`dk_atlas_fc_analysis.py`**
    - **Purpose:** Compute and save the FC matrix for a set of subjects using their timeseries data. The script processes timeseries data, computes FC with and without Fisher z-transformation, and saves the results to both pickle and CSV files for further analysis.
    - **Functions:**
        - `main()`: Main function to initialize paths and parameters, retrieve timeseries data, compute FC matrices, and save the results.
        - `compute_and_save_fc(fisher_ztrans, output_path_base)`: Helper function within `main` to compute and save FC matrices, both Fisher z-transformed and non-Fisher z-transformed.
    - **Notes:**
        - Adjust paths for `timeseries_root` and `output_dir` to match your data structure.
        - Ensure the chosen ROI names file path is correctly specified.
        - The script leverages the `FC` class from the `compute_functional_connectivity.py` file.

## Setup
- Ensure that all necessary Python packages are installed. You may use `pip` to install them:
    ```bash
    pip install os pandas numpy nibabel scipy matplotlib
    ```
- Some scripts, such as `transform_dk_atlas_native_space.py`, require FreeSurfer to be correctly installed and configured on your system.
`