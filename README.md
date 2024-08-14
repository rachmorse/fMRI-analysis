
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
    - **Purpose:** Scrubs fMRI BOLD images based on a Framewise Displacement (FWD) threshold to help mitigate motion artifacts. It either removes or interpolates timepoints where a subject has a high FWD (e.g. 0.5).
    - **Functions:**
        - `analyze_threshold`: Analyzes and visualizes subjects' movement above a given FWD threshold.
        - `scrub`: Scrubs the BOLD images based on the FWD threshold using specified methods ('cut' or 'interpolate').
        - `process_subject`: Processes an individual subject’s BOLD file and scrubs it.
        - `main`: Main function to initialize and process all subjects either sequentially or in parallel. Allows input of session timepoint, threshold, and directories for data input and output.
    - **Notes:**
        - Adjust paths for data input and output (including names for this data), session (`ses`), and threshold.
        - The script supports parallel processing to speed up execution.
    - **Key Terms:**
        - *Framewise Displacement (FWD)*
            - A measure in fMRI analysis to quantify the amount of head movement between consecutive scans. It captures both translational (linear) and rotational (angular) movements, providing a single value that indicates the total displacement of the head. FWD is calculated as the sum of the absolute differences in head position and rotation between successive frames.
        - *Scrubbing*
            - The process of removing or correcting fMRI data points that are affected by motion artifacts (as determined by FWD). Scrubbing aims to improve the quality of the data by mitigating the effects of head movement. It replaces timeseries values that are affected by significant movement with an estimated timeseries value using interpolation or extrapolation. 
        - *Interpolation*
            - The process of estimating unknown values (in this case, values removed due to high FWD values) that are within the range of known values.
                - *Example:*
                    Imagine you have data points for tp 1, 2, 4, and 5, but the value for timepoint 3 has been removed because of high movement at timepoint 3:
                    ```
                    Time:   1   2  3   4   5
                    Value: 10  20  ??  40  50
                    ```
                    Interpolation estimates the missing value at timepoint 3 based on known neighboring values. 
        - *Extrapolation*
            - The process of estimating unknown values that are outside the range of known values.
                - *Example:*
                    Imagine you have data points at timepoint 1, 2, 3, and 4, but you need to estimate the value at timepoint 5:
                    ```
                    Time:   1   2   3   4  5
                    Value: 10  20  30  40 ??
                    ```
                    Using extrapolation, you estimate the value at timepoint 5 based on the trend from the known values. 

2. **`transform_dk_atlas_native_space.py`**
    - **Purpose:** Resample the DK atlas from the subject's T1 space to the subject's native BOLD space using `mri_vol2vol` from FreeSurfer. The DK atlas requires resampling to ensures that the atlas is tailored to the individual's brain morphology, rather than a generalized MNI space. During FreeSurfer's `recon-all` (cortical reconstruction) process, a version of the DK atlas is created that is specific to each subject's T1-weighted anatomical space. To utilize this atlas for fMRI analysis, you need to resample the T1-specific DK atlas to the subject's native BOLD space. 
    - **Functions:**
        - `process_subject`: Creates DK atlas in an individual subject's BOLD image space.
        - `main`: Main function to initialize and process all subjects. Allows input of session timepoint and directories for data input and output.
    - **Notes:**
        - Adjust paths for data input and output and session (`ses`).
        - This script requires FreeSurfer to be set up on your system.
    - **Key Terms:**
        - *Nearest Neighbor Interpolation*
            - This script used Neareset Neighbor Interpolation to resample the data. It assigns the value of the closest known data point from the input atlas to each unknown data point in the output atlas. 

3. **`select_specific_rois.py`**
    - **Purpose:** Processes and saves specific ROIs from the DK atlases in the native BOLD space, zeroing out other regions not listed as selected. This script take a list of ROIs from the DK atlas that you are most interested in analyzing and removes the other ROIs from the DK atlases that were created for each subject in `transform_dk_atlas_native_space.py`.
    - **Functions:**
        - `main`: Main function to load subjects and chosen ROIs, then process and save the specified ROIs for each subject.
    - **Notes:**
        - Adjust paths for data input and output.

4. **`extract_timeseries.py`**
    - **Purpose:** Extracts timeseries data from fMRI BOLD images using the DK atlas in native BOLD space. This script defines the functions, which are utilized in the subsequent `extract_subjects_timeseries.py` script to extract, save, and visualize (if you want) timeseries data for the selected ROIs for each subject.
    - **Functions:** Each subsequent function is designed to call on the one before it, progressively processing the data step-by-step.
        - `extract_timeseries`: Extracts timeseries data using either a 3D or 4D atlas mask and logs any errors encountered during the process.
        - `visualize_data`: Visualizes the timeseries data for specified ROIs for a given subject. To enable this feature, uncomment the relevant code in `extract_subjects_timeseries.py`.

5. **`extract_subjects_timeseries.py`**
    - **Purpose:** Runs the timeseries extraction process for multiple subjects using the functions from `extract_timeseries.py` and using the DK atlas masks created in `select_specific_rois.py`.
    - **Functions:**
        - `process_subject_extract`: Processes a single subject by extracting timeseries data using the atlas mask, saving the timeseries to a file, and optionally visualizing the data if the corresponding code is uncommented.
        - `main`: Main function to initialize the extractor and process all subjects either sequentially or in parallel.
    - **Notes:**
        - Adjust paths for data input and output (including names for this data), session (`ses`), and threshold. Session and threshold are included to more automatically locate your scrubbed data. 
        - The script supports parallel processing to speed up execution.

6. **`compute_functional_connectivity.py`**
    - **Purpose:** Computes various functional connectivty metics for subjects from the timeseries data. This script defines functions, which are used in the subsequent `compute_subject_functional_connectivity.py` script to compute functional connectivity.
    - **Functions:** These functions are used for general FC analysis, and while not all are applied in `dk_atlas_fc_analysis.py`, they provide a comprehensive toolkit for FC calculations. 
        - `fisher_transform`: Applies Fisher z-transformation to the correlation coefficients.
        - `compute_functional_connectivity`: Computes all-to-all correlations for one or multiple subjects. For example, if you have `N` ROIs, this computes the correlation for each pair of ROIs, resulting in an `N x N` connectivity matrix. It then saves both the raw and Fisher Z-transformed matrices and group-level functional connectivity data.
        - `compute_one_to_all_connectivity`: Optionally computes one-to-all correlations, if you are interested in one ROI in particular. It then saves both the raw and Fisher Z-transformed matrices at the group-level.
        - `visualize_data`: Visualizes the functional connectivity data for a given subject. To enable this feature, uncomment the relevant code in `compute_subject_functional_connectivity.py`.

7. **`compute_subject_functional_connectivity.py`**
    - **Purpose:**  Runs the functions from `compute_functional_connectivity.py` to compute and save the FC matrix for a set of subjects using their timeseries data. The script processes timeseries data, computes FC with and without Fisher z-transformation, and saves the results to CSV files for further analysis.
    - **Functions:**
        - `process_subject_functional`: Processes a single subject by loading pre-extracted timeseries data, computing the functional connectivity matrix, saving the connectivity matrix, and optionally visualizing the data if the corresponding code is uncommented.
        - `main`: Main function to initialize paths and parameters, retrieve timeseries data, compute FC matrices, and save the results.
    - **Notes:**
        - Adjust paths for data input and output (including names for this data). 
        - Ensure the selected ROI names file path is correctly specified.

## Setup
- Ensure the requirements are installed
    ```bash
    pip install -r requirements.txt
    ```
- The script `transform_dk_atlas_native_space.py` require FreeSurfer to be correctly installed and configured on your system.
