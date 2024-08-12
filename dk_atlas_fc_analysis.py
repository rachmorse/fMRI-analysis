import os
import pickle
import numpy as np
import pandas as pd
from compute_functional_connectivity import FC  # Import the class from the compute_functional_connectivity.py file
from typing import Union
from pathlib import Path


def compute_and_save_fc(fisher_ztrans, output_path_base, csv_output_name, subjects, roi_pairs, timeseries_files):
    """
    Compute and save the functional connectivity matrix.

    Args:
        fisher_ztrans (bool): Whether to apply Fisher z-transformation.
        output_path_base (str): Base path to save the pickle files.
        csv_output_name (str): Name of the CSV file to save.
        subjects (list): List of subject IDs.
        roi_pairs (list): List of ROI pairs.
        timeseries_files (list): List of timeseries files.
    """
    transformation_type = "Fisher z-transformed" if fisher_ztrans else "non-Fisher z-transformed"
    print(f"Starting computation for {transformation_type} connectivity...")

    # Initialize the Functional Connectivity instance
    fc_instance = FC(fisher_ztrans=fisher_ztrans)
    
    # Compute the functional connectivity for all subjects
    functional_connectivity = fc_instance.compute_all_to_all(subjects, timeseries_files)

    # Save the functional connectivity matrix in a pickle file
    pkl_output_path = f"{output_path_base}.pkl"
    with open(pkl_output_path, 'wb') as f:
        pickle.dump(functional_connectivity, f)
    
    # Prepare a DataFrame for storing all subjects' FC values
    df_all_fc = pd.DataFrame(index=subjects, columns=roi_pairs)

    # Flatten the FC matrix for each subject and insert into the DataFrame
    for result in functional_connectivity:
        subject_id = result["subject"]
        fc_matrix = result["FC"]

        # Get the upper triangular indices of the FC matrix
        upper_tri_indices = np.triu_indices(fc_matrix.shape[0], k=1)
        upper_tri_values = fc_matrix[upper_tri_indices]

        # Insert into DataFrame
        df_all_fc.loc[subject_id, :] = upper_tri_values

    # Save the DataFrame to a CSV
    csv_output_path = f"{output_path_base}_{csv_output_name}.csv"
    df_all_fc.to_csv(csv_output_path, index_label="SubjectID")
    
    print(f"Successfully computed and saved {transformation_type} functional connectivity to {pkl_output_path} and CSV file {csv_output_path}.")


def main(selected_rois_path: Union[str, Path], timeseries_root: Union[str, Path], output_folder: Union[str, Path], roi_column_name: str, csv_output_name: str):
    """
    Main function to compute and save the functional connectivity matrix.
    
    This function initializes the paths and parameters, processes the timeseries
    data, computes the functional connectivity with and without Fisher z-transformation,
    and saves the results to pickle and CSV files.

    Args:
        selected_rois_path (Union[str, Path]): Path to the selected ROIs CSV file.
        timeseries_root (Union[str, Path]): Path to the directory containing timeseries files.
        output_folder (Union[str, Path]): Path to save outputs.
        roi_column_name (str): Name of the ROI names column in the CSV file.
        csv_output_name (str): Name of the CSV file to save.
    """
    output_folder = Path(output_folder)

    # Ensure output directory exists
    output_folder.mkdir(parents=True, exist_ok=True)

    # Read selected ROIs from CSV and convert the indices to a list
    try:
        selected_rois_df = pd.read_csv(selected_rois_path, index_col=0)
        selected_rois = list(selected_rois_df.index)
        roi_names = selected_rois_df[roi_column_name].values
    except FileNotFoundError:
        raise FileNotFoundError(f"Selected ROIs file not found at: {selected_rois_path}")
    except KeyError:
        raise KeyError(f"'{roi_column_name}' column not found in the selected ROIs file: {selected_rois_path}")

    # Get the list of timeseries files
    timeseries_files = [os.path.join(timeseries_root, ts_file) for ts_file in os.listdir(timeseries_root)]
    
    # Extract subject IDs from the timeseries file names
    subjects = [os.path.basename(ts_file).split("_")[0] for ts_file in timeseries_files]
    
    print(f"Number of subjects: {len(subjects)}")

    # Create pairs for the columns
    roi_pairs = [f"{roi1}-{roi2}" for i, roi1 in enumerate(roi_names) for j, roi2 in enumerate(roi_names) if j > i]

    compute_and_save_fc(fisher_ztrans=False, output_path_base=output_folder / "FC", csv_output_name=csv_output_name, subjects=subjects, roi_pairs=roi_pairs, timeseries_files=timeseries_files)
    compute_and_save_fc(fisher_ztrans=True, output_path_base=output_folder / "FC_Fisher-z-trans", csv_output_name=csv_output_name, subjects=subjects, roi_pairs=roi_pairs, timeseries_files=timeseries_files)


if __name__ == '__main__':
    # Change to your paths
    selected_rois_csv = Path("/pool/guttmann/laboratori/scripts/BOLD_connectivity/chosen_areas.csv") 
    timeseries_root = Path("/home/rachel/Desktop/fMRI Analysis/DK76/timeseries")
    output_directory = Path("/home/rachel/Desktop/fMRI Analysis/DK76/FC")

    # Change to the name of the ROI name column in your CSV file
    roi_column_name_in_csv = 'LabelName' 

    # Change to the desired CSV output name
    csv_output_name = 'all_subjects_FC'  
        
    main(selected_rois_path=selected_rois_csv, timeseries_root=timeseries_root, output_folder=output_directory, roi_column_name=roi_column_name_in_csv, csv_output_name=csv_output_name)