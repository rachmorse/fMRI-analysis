import pandas as pd
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from nilearn.connectome import ConnectivityMeasure
from typing import List, Optional
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


def compute_functional_connectivity(
    subject_id: str,
    timeseries: np.ndarray,
    output_dir: Path,
    selected_rois_csv: Optional[Path] = None,
    roi_column_name: Optional[str] = None,
    subjects: Optional[List[str]] = None,
) -> np.ndarray:
    """
    Compute the connectivity matrix from the extracted timeseries data and save both
    the raw and Fisher z-transformed connectivity matrices. 
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
    correlation_measure = ConnectivityMeasure(kind="correlation", standardize=False)
    connectivity_matrix = correlation_measure.fit_transform([timeseries])[0]

    np.fill_diagonal(connectivity_matrix, 0)

    fisher_z_matrix = fisher_transform(connectivity_matrix)

    # Save indivudual connectivity matrices
    # output_file_raw = output_dir / f"{subject_id}_connectivity.csv"
    # output_file_fisher_z = output_dir / f"{subject_id}_connectivity_fisher_z.csv"

    # print(f"Saving raw connectivity matrix to {output_file_raw}")
    # np.savetxt(output_file_raw, connectivity_matrix, delimiter=",")

    # print(f"Saving Fisher z-transformed connectivity matrix to {output_file_fisher_z}")
    # np.savetxt(output_file_fisher_z, fisher_z_matrix, delimiter=",")

    if selected_rois_csv and roi_column_name and subjects:
        try:
            selected_rois_df = pd.read_csv(selected_rois_csv, index_col=0)
            roi_names = selected_rois_df[roi_column_name].values
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Selected ROIs file not found at: {selected_rois_csv}"
            )
        except KeyError:
            raise KeyError(
                f"'{roi_column_name}' column not found in the selected ROIs file: {selected_rois_csv}"
            )
        
        columns = [f"{roi1}-{roi2}" for roi1, roi2 in combinations(roi_names, 2)]

        # Initialize a DataFrame to store the FC data
        df_all_fc = pd.DataFrame(
            index=[subject_id],
            columns=columns,
        )

        upper_tri_indices = np.triu_indices(connectivity_matrix.shape[0], k=1)
        upper_tri_values = connectivity_matrix[upper_tri_indices]
        df_all_fc.loc[subject_id, :] = upper_tri_values

        csv_output_path = output_dir / "all_fc_data.csv"

        df_all_fc.to_csv(
            csv_output_path, 
            mode="a",
            header=not csv_output_path.exists(),
            index_label="SubjectID",
        )

        # Initialize a DataFrame to store the fisher z-transformed FC data      
        df_all_fc_fisher_z = pd.DataFrame(
            index=[subject_id],
            columns=columns,
        )

        upper_tri_values_fisher_z = fisher_z_matrix[upper_tri_indices]
        df_all_fc_fisher_z.loc[subject_id, :] = upper_tri_values_fisher_z

        fisher_z_csv_output_path = output_dir / "all_fc_data_fisher_z.csv"
        df_all_fc_fisher_z.to_csv(
            fisher_z_csv_output_path, 
            mode="a",
            header=not fisher_z_csv_output_path.exists(),
            index_label="SubjectID"
        )

    return connectivity_matrix, fisher_z_matrix


def compute_one_to_all_connectivity(
    subject_id: str,
    connectivity_matrix: np.ndarray,
    fisher_z_matrix: np.ndarray,
    output_dir: Path,
    one_timeseries_index: int,
    roi_names: List[str],
    subjects: List[str],
):
    """
    Compute and save the one-to-all connectivity for a specified ROI.

    Args:
        subject_id (str): Identifier for the subject.
        connectivity_matrix (np.ndarray): The raw connectivity matrix.
        fisher_z_matrix (np.ndarray): The Fisher z-transformed connectivity matrix.
        output_dir (Path): Directory where the connectivity matrices will be saved.
        one_timeseries_index (int): Index of the timeseries for computing one-to-all correlations.
        roi_names (List[str]): List of ROI names.
        subjects (List[str]): List of all subjects for grouping.
    """
    if (
        isinstance(one_timeseries_index, int)
        and 0 <= one_timeseries_index < connectivity_matrix.shape[0]
    ):
        one_to_all_raw_no_mask = connectivity_matrix[one_timeseries_index, :]
        one_to_all_fisher_z_no_mask = fisher_z_matrix[one_timeseries_index, :]

        # Create a mask to exclude when the ROI connects to itself (diagonal) which is manually set to 0
        mask = np.arange(connectivity_matrix.shape[0]) != one_timeseries_index
        mask_fisher_z = np.arange(fisher_z_matrix.shape[0]) != one_timeseries_index

        # Apply the mask to filter out self-connectivity
        one_to_all_raw = one_to_all_raw_no_mask[mask]
        one_to_all_fisher_z = one_to_all_fisher_z_no_mask[mask_fisher_z]

        columns = [
            f"{roi_names[one_timeseries_index]}-{roi}" 
            for roi in roi_names 
            if roi != roi_names[one_timeseries_index] # Exclude self-connectivity 
        ]
    
        # Prepare the one-to-all DataFrame
        one_to_all_df = pd.DataFrame(
            index=[subject_id],
            columns=columns,
        )

        # Insert the one-to-all values for the current subject
        one_to_all_df.loc[subject_id] = one_to_all_raw

        # Save the one-to-all DataFrame for all subjects in append mode
        one_to_all_csv_output_path = (
            output_dir / f"{roi_names[one_timeseries_index]}_fc_data.csv"
        )
        one_to_all_df.to_csv(
            one_to_all_csv_output_path,
            mode="a",
            header=not one_to_all_csv_output_path.exists(),
            index_label="SubjectID",
        )

        # Prepare the one-to-all Fisher z DataFrame
        one_to_all_fisher_z_df = pd.DataFrame(
            index=[subject_id],
            columns=columns,
        )

        # Insert the one-to-all Fisher z values for the current subject
        one_to_all_fisher_z_df.loc[subject_id] = one_to_all_fisher_z

        # Save the one-to-all Fisher z DataFrame for all subjects in append mode
        one_to_all_fisher_z_csv_output_path = (
            output_dir
            / f"{roi_names[one_timeseries_index]}_fc_data_fisher_z.csv"
        )
        one_to_all_fisher_z_df.to_csv(
            one_to_all_fisher_z_csv_output_path,
            mode="a",
            header=not one_to_all_fisher_z_csv_output_path.exists(),
            index_label="SubjectID",
        )
    else:
        print(
            f"Invalid one_timeseries_index: {one_timeseries_index} for subject {subject_id}"
        )


def visualize_fc_data(
    subject_id: str,
    connectivity_matrix: np.ndarray,
):
    """
    Visualize the connectivity matrix.

    Args:
        subject_id (str): Identifier for the subject.
        connectivity_matrix (np.ndarray): The connectivity matrix to be visualized.
    """
    # Visualize connectivity matrix
    plt.figure(figsize=(10, 8))
    plt.imshow(connectivity_matrix, vmin=-1, vmax=1, cmap="coolwarm")
    plt.colorbar(label="Correlation Coefficient")
    plt.title(f"Connectivity Matrix for Subject {subject_id}")
    plt.xlabel("Regions")
    plt.ylabel("Regions")
    plt.grid(False)
    plt.show()