
import os
import pickle
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind, pearsonr
from compute_functional_connectivity import FC # Import the class from the compute_functional_connectivity.py file

def main():
    """
    Main function to compute and save the functional connectivity matrix.
    
    This function initializes the paths and parameters, processes the timeseries
    data, computes the functional connectivity with and without Fisher z-transformation,
    and saves the results to pickle files.
    """
    # Define root directory containing timeseries data
    timeseries_root = "/home/rachel/Desktop/fMRI Analysis/DK76/timeseries"
    output_dir = "/home/rachel/Desktop/fMRI Analysis/DK76/FC"
    
    # Get the list of timeseries files
    timeseries_files = [os.path.join(timeseries_root, ts_file) for ts_file in os.listdir(timeseries_root)]
    
    # Extract subject IDs from the timeseries file names
    subjects = [os.path.basename(ts_file).split("_")[0] for ts_file in timeseries_files]
    
    # Print the number of subjects to process
    print(f"Number of subjects: {len(subjects)}")
    
    # Load chosen ROI names
    chosen_areas_df = pd.read_csv("/pool/guttmann/laboratori/scripts/BOLD_connectivity/chosen_areas.csv", index_col=0)
    roi_names = chosen_areas_df['LabelName'].values 

    # Create pairs for the columns
    roi_pairs = [f"{roi1}-{roi2}" for i, roi1 in enumerate(roi_names) for j, roi2 in enumerate(roi_names) if j > i]

    # Function to compute and save functional connectivity
    def compute_and_save_fc(fisher_ztrans, output_path_base):
        """
        Compute and save the functional connectivity matrix.

        Parameters:
        fisher_ztrans (bool): Whether to apply Fisher z-transformation.
        output_path_base (str): Base path to save the pickle and CSV files.
        """
        transformation_type = "Fisher z-transformed" if fisher_ztrans else "non-Fisher z-transformed"
        print(f"Starting computation for {transformation_type} connectivity...")

        # Initialize the Functional Connectivity instance
        fc_instance = FC(fisher_ztrans=fisher_ztrans)
        
        # Compute the functional connectivity for all subjects
        functional_connectivity = fc_instance.multiple_all_to_all(subjects, timeseries_files)

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
        csv_output_path = f"{output_path_base}_all_subjects_FC.csv"
        df_all_fc.to_csv(csv_output_path, index_label="SubjectID")
        
        # Output indicating successful save
        print(f"Successfully computed and saved {transformation_type} functional connectivity to {pkl_output_path} and CSV file {csv_output_path}.")

    # Compute and save functional connectivity without Fisher z-transformation
    compute_and_save_fc(
        fisher_ztrans=False, 
        output_path_base=os.path.join(output_dir, "FC")
    )
    
    # Compute and save functional connectivity with Fisher z-transformation
    compute_and_save_fc(
        fisher_ztrans=True, 
        output_path_base=os.path.join(output_dir, "FC_Fisher-z-trans")
    )
    
if __name__ == '__main__':
    main()