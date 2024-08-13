import os
import pandas as pd
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from nilearn.connectome import ConnectivityMeasure
from typing import List, Optional
from scipy.stats import pearsonr
from itertools import combinations


def fisher_transform(correlations: np.ndarray) -> np.ndarray:
    """
    Apply Fisher z-transformation to the correlation coefficients.
    
    Args:
        correlations (np.ndarray): Correlation coefficients.
    
    Returns:
        np.ndarray: Transformed correlation coefficients.
    """
    return np.arctanh(correlations)


def compute_functional_connectivity(subject_id: str, 
                                    timeseries: np.ndarray, 
                                    output_dir: Path, 
                                    one_timeseries_index: Optional[int] = None, 
                                    selected_rois_csv: Optional[Path] = None, 
                                    roi_column_name: Optional[str] = None, 
                                    subjects: Optional[List[str]] = None) -> np.ndarray:
    """
    Compute the connectivity matrix from the extracted timeseries data and save both
    the raw and Fisher z-transformed connectivity matrices. Optionally, compute and save one-to-all correlations.
    Additionally, save group CSV with FC data for all the ROIs with the ROI names.

    Args:
        subject_id (str): Identifier for the subject.
        timeseries (np.ndarray): Timeseries data extracted from the fMRI BOLD image.
        output_dir (Path): Directory where the connectivity matrices will be saved.
        one_timeseries_index (Optional[int], optional): Index of the timeseries for computing one-to-all correlations. Default is None.
        selected_rois_csv (Optional[Path], optional): Path to the selected ROIs CSV. Default is None.
        roi_column_name (Optional[str], optional): Name of the column containing ROI names. Default is None.
        subjects (Optional[List[str]], optional): List of subjects. Default is None.

    Returns:
        np.ndarray: The raw connectivity matrix.
    """
    print("Computing connectivity matrix...")
    correlation_measure = ConnectivityMeasure(kind='correlation')
    connectivity_matrix = correlation_measure.fit_transform([timeseries])[0]

    # Zero out diagonal elements
    np.fill_diagonal(connectivity_matrix, 0)

    # Compute Fisher z-transformed matrix
    fisher_z_matrix = fisher_transform(connectivity_matrix)

    # Define output files
    output_file_raw = output_dir / f"{subject_id}_connectivity.csv"
    output_file_fisher_z = output_dir / f"{subject_id}_connectivity_fisher_z.csv"

    # Save the raw connectivity matrix
    print(f"Saving raw connectivity matrix to {output_file_raw}")
    np.savetxt(output_file_raw, connectivity_matrix, delimiter=",")

    # Save the Fisher z-transformed connectivity matrix
    print(f"Saving Fisher z-transformed connectivity matrix to {output_file_fisher_z}")
    np.savetxt(output_file_fisher_z, fisher_z_matrix, delimiter=",")

    # If specified, compute and save one-to-all correlations
    if one_timeseries_index is not None:
        if 0 <= one_timeseries_index < connectivity_matrix.shape[0]:
            one_to_all_raw = connectivity_matrix[one_timeseries_index, :]
            one_to_all_fisher_z = fisher_z_matrix[one_timeseries_index, :]

            output_file_one_to_all_raw = output_dir / f"{subject_id}_one_to_all_connectivity.csv"
            output_file_one_to_all_fisher_z = output_dir / f"{subject_id}_one_to_all_connectivity_fisher_z.csv"

            print(f"Saving one-to-all raw connectivity matrix to {output_file_one_to_all_raw}")
            np.savetxt(output_file_one_to_all_raw, one_to_all_raw, delimiter=",")

            print(f"Saving one-to-all Fisher z-transformed connectivity matrix to {output_file_one_to_all_fisher_z}")
            np.savetxt(output_file_one_to_all_fisher_z, one_to_all_fisher_z, delimiter=",")
        else:
            print(f"Invalid one_timeseries_index: {one_timeseries_index} for subject {subject_id}")

    # Prepare and save group CSV with FC data for all ROIs with the ROI names
    if selected_rois_csv and roi_column_name and subjects:
        # Read the selected ROIs from CSV and convert the indices to a list
        try:
            selected_rois_df = pd.read_csv(selected_rois_csv, index_col=0)
            selected_rois = list(selected_rois_df.index)
            roi_names = selected_rois_df[roi_column_name].values
        except FileNotFoundError:
            raise FileNotFoundError(f"Selected ROIs file not found at: {selected_rois_csv}")
        except KeyError:
            raise KeyError(f"'{roi_column_name}' column not found in the selected ROIs file: {selected_rois_csv}")

        # Prepare a DataFrame for storing all subjects' FC values
        df_all_fc = pd.DataFrame(index=subjects, columns=[f"{roi1}-{roi2}" for roi1, roi2 in combinations(roi_names, 2)])

        # Insert the FC values into the DataFrame
        upper_tri_indices = np.triu_indices(connectivity_matrix.shape[0], k=1)
        upper_tri_values = connectivity_matrix[upper_tri_indices]
        df_all_fc.loc[subject_id, :] = upper_tri_values

        # Save the DataFrame to a CSV
        csv_output_path = output_dir / "group_fc_data.csv"
        df_all_fc.to_csv(csv_output_path, index_label="SubjectID")

        # Prepare DataFrame for fisher-z transformed scores
        df_all_fc_fisher_z = pd.DataFrame(index=subjects, columns=[f"{roi1}-{roi2}" for roi1, roi2 in combinations(roi_names, 2)])

        # Insert the Fisher Z-transformed FC values into the DataFrame
        upper_tri_values_fisher_z = fisher_z_matrix[upper_tri_indices]
        df_all_fc_fisher_z.loc[subject_id, :] = upper_tri_values_fisher_z

        # Save the DataFrame to a CSV
        fisher_z_csv_output_path = output_dir / "group_fc_data_fisher_z.csv"
        df_all_fc_fisher_z.to_csv(fisher_z_csv_output_path, index_label="SubjectID")

    return connectivity_matrix

def visualize_data(subject_id: str, connectivity_matrix: np.ndarray, timeseries: np.ndarray, roi_indices: List[int]):
    """
    Visualize the connectivity matrix and timeseries for specified ROIs.

    Args:
        subject_id (str): Identifier for the subject.
        connectivity_matrix (np.ndarray): The connectivity matrix to be visualized.
        timeseries (np.ndarray): The timeseries data to be visualized.
        roi_indices (List[int]): List of ROI indices to visualize.
    """
    # Visualize Connectivity Matrix
    plt.figure(figsize=(10, 8))
    plt.imshow(connectivity_matrix, vmin=-1, vmax=1, cmap='coolwarm')
    plt.colorbar(label='Correlation Coefficient')
    plt.title(f'Connectivity Matrix for Subject {subject_id}')
    plt.xlabel('Regions')
    plt.ylabel('Regions')
    plt.grid(False)
    plt.show()

    # Visualize Timeseries for specified ROIs
    for idx in roi_indices:
        plt.figure(figsize=(10, 4))
        plt.plot(timeseries[:, idx])
        plt.title(f'Timeseries for ROI {idx} - Subject {subject_id}')
        plt.xlabel('Time points')
        plt.ylabel('BOLD signal')
        plt.show()