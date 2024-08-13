import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from nilearn.connectome import ConnectivityMeasure
from typing import List
from scipy.stats import pearsonr


def fisher_transform(correlations: np.ndarray) -> np.ndarray:
    """
    Apply Fisher z-transformation to the correlation coefficients.
    
    Args:
        correlations (np.ndarray): Correlation coefficients.
    
    Returns:
        np.ndarray: Transformed correlation coefficients.
    """
    return np.arctanh(correlations)


def compute_functional_connectivity(subject_id: str, timeseries: np.ndarray, output_dir: Path, one_timeseries_index: int = None) -> np.ndarray:
    """
    Compute the connectivity matrix from the extracted timeseries data and save both
    the raw and Fisher z-transformed connectivity matrices. Optionally, compute and save one-to-all correlations.

    Args:
        subject_id (str): Identifier for the subject.
        timeseries (np.ndarray): Timeseries data extracted from the fMRI BOLD image.
        output_dir (Path): Directory where the connectivity matrices will be saved.
        one_timeseries_index (int, optional): Index of the timeseries for computing one-to-all correlations. Default is None.

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