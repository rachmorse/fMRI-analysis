import os
import pandas as pd
import numpy as np
import nibabel as nib
import scipy.interpolate
import matplotlib.pyplot as plt
from multiprocessing import Pool

# Function to analyze threshold of movement
def analyze_threshold(df, threshold, total_scans=740, affected_percentage=0.5):
    """
    Analyze and visualize subjects with significant movement for a given FWD threshold (e.g. subjects with higher than X FWD in > Y% of scans)

    Args:
        df (pd.DataFrame): DataFrame containing FWD data.
        threshold (float): The FWD threshold to be compared with.
        total_scans (int, optional): The total number of scans per subject. Default is 740.
        affected_percentage (float, optional): The percentage of affected scans. Default is 50%.

    Returns:
        None
    """
    moved_subjects_count = (((df > threshold).sum(1) / total_scans) > affected_percentage).sum()
    print(f"{moved_subjects_count} subjects with more than {affected_percentage * 100}% of scans moved (threshold {threshold})")
    plt.hist((df > threshold).sum(1) / total_scans)
    plt.title(f"Distribution of Fraction of Moved Scans (Threshold: {threshold})")
    plt.xlabel("Fraction")
    plt.ylabel("Number of Subjects")
    plt.show()

# Function to scrub the BOLD images
def scrub(bold_file, fwd_file, scrubbed_file, th=0.5, method="interpolate"):
    """
    Scrub the BOLD MRI images by either removing or interpolating scans based on FWD threshold.

    Args:
        bold_file (str): Path to the BOLD image file (NIfTI format).
        fwd_file (str): Path to the FWD file (CSV format).
        scrubbed_file (str): Path to save the scrubbed BOLD image file (NIfTI format).
        th (float, optional): Threshold for FWD above by which scans are considered moved. Default is 0.5 FWD.
        method (str, optional): Method for handling moved scans. Either 'cut' to remove or 'interpolate' to replace. Default is 'interpolate'.

    Returns:
        int: 0 if the function executes successfully.
    """

    # Load BOLD image data
    print("Loading BOLD image from file:", bold_file)
    bold = nib.load(bold_file)
    bold_data = bold.get_fdata()
    bold_affine = bold.affine

    # Load FWD data
    print("Loading Framewise Displacement data from file:", fwd_file)
    fwd = np.array(pd.read_csv(fwd_file).FramewiseDisplacement)
    
    # Identify timepoints with excessive motion
    all_tps = np.arange(bold_data.shape[3]) 
    correct_tps = all_tps[[False] + list(fwd < th)]
    incorrect_tps = all_tps[[False] + list(fwd >= th)]
    correct_bold = bold_data[:, :, :, correct_tps] 
    
    print(f"{len(incorrect_tps)} out of {bold_data.shape[3]} scans ({round(len(incorrect_tps) * 100 / bold_data.shape[3], 2)}%) exceed the motion threshold (FWD > {th}).")
    
    # Start scrubbing based on the method
    if method == "cut":
        # If the method is 'cut', remove the tps with excessive motion. Save as scrubbed_data.
        scrubbed_data = correct_bold
        print(f"Removing {len(incorrect_tps)} scans due to excessive motion.")
    elif method == "interpolate":
        # If the method is 'interpolate', replace the tps with excessive motion through interpolation or extrapolation. 
        scrubbed_data = bold_data.copy()
        # Check if the first or last tps are incorrect because if they are, they should be extrapolated
        if not 1 in incorrect_tps and not bold_data.shape[3] - 1 in incorrect_tps:
            print(f"Interpolating {len(incorrect_tps)} scans due to excessive motion.")
            # Perform interpolation when neither the first nor last tps are incorrect
            interpolator = scipy.interpolate.interp1d(correct_tps, correct_bold, axis=3, fill_value="extrapolate") 
            scrubbed_data[:, :, :, incorrect_tps] = interpolator(incorrect_tps)
            print("No scans require extrapolation.")
        else:
            extrap_idx = []
            intrap_idx = list(incorrect_tps)
            extrap_text = []
            i = 1
            # Perform left extrapolation for incorrect first tp
            while i in incorrect_tps:
                extrap_idx.append(i)
                intrap_idx.remove(i)
                extrap_text.append("left")
                i += 1
            i = 1
            # Perform right extrapolation for incorrect last tp
            while bold_data.shape[3] - i in incorrect_tps:
                extrap_idx.append(bold_data.shape[3] - i)
                intrap_idx.remove(bold_data.shape[3] - i)
                extrap_text.append("right")
                i += 1
            
            print(f"Interpolating {len(intrap_idx)} scans due to excessive motion.")
            interpolator = scipy.interpolate.interp1d(correct_tps, correct_bold, axis=3)
            scrubbed_data[:, :, :, intrap_idx] = interpolator(intrap_idx)
            
            if extrap_text:
                print(f"Extrapolating {len(extrap_idx)} scans in the {', '.join(extrap_text)} direction(s) due to motion.")
                extrapolator = scipy.interpolate.interp1d(correct_tps, correct_bold, fill_value='extrapolate', axis=3)
                scrubbed_data[:, :, :, extrap_idx] = extrapolator(extrap_idx)

    else:
        print("Unknown method specified; returning the original BOLD file.")
        scrubbed_data = bold_data  # Unchanged; return original BOLD data

    scrubbed_image = nib.Nifti1Image(scrubbed_data, bold_affine)
    os.makedirs(os.path.dirname(scrubbed_file), exist_ok=True)
    nib.save(scrubbed_image, scrubbed_file)
    
    print(f"Scrubbing complete. Scrubbed image saved to: {scrubbed_file}")
    return 0

# Function to process each subject
def process_subject(subject, ses, root, th, output_data, error_log):
    """
    Process a single subject by scrubbing the BOLD MRI images based on the FWD.
    
    Args:
        subject (str): Subject ID used to process the BOLD and FWD files.
    
    Returns:
        None: Saves the scrubbed BOLD file for the subject and logs errors if any occur.
    """
    try:
        fwd_file = os.path.join(root, subject, "native_T1", "framewise_displ.txt")
        bold_file = os.path.join(root, subject, "native_T1", f"{subject}_ses-{ses}_run-01_rest_bold_ap_T1-space.nii.gz")
        scrubbed_file = os.path.join(output_data, subject, "native_T1", f"{subject}_ses-{ses}_run-01_rest_bold_ap_T1-space_scrubbed_{th}.nii.gz")

        print(f"Processing subject: {subject}")

        if not os.path.exists(scrubbed_file):
            scrub(bold_file, fwd_file, scrubbed_file, th=0.5, method="interpolate")
        else:
            print("Already scrubbed!")
    except Exception as e:
        print(f"Error processing subject {subject}: {e}")
        with open(error_log, "a") as f:
            f.write(f"Error processing subject {subject}: {e}\n")

# Main function to run the script
def main(multi=False):
    """
    Main function to run this script.

    This function performs the following steps:

    1. Defines session timepoint and directories for data input and output.
    2. Concatenates all `framewise_displ.txt` files from each subject into a single DataFrame.
    3. Saves the concatenated DataFrame to `all_fwd.csv`.
    4. Visualizes data thresholds using the `analyze_threshold` function.
    5. Scrubs the BOLD images by either serial or parallel processing of subjects.

    Args:
        multi (bool): If True, enables parallel processing using multiprocessing. Defaults to False.

    Outputs:
        - A concatenated DataFrame of framewise displacement (`all_fwd.csv`) 
        - A list of subjects to be processed (`todo.csv`)
        - Various error logs and outputs depending on the scrubbing process.

    Notes:
        - The default session timepoint is set to "01".
        - The root, output_data, and output_files directories are configurable; update these paths as needed.
        - Ensure that the required files (`framewise_displ.txt`, etc.) are present in the specified directories.

    Raises:
        Exception: If any required file or directory is not found.
    """
    # 1. Define the session timepoint and directories for data input. Change these as needed for the data being processed
    ses = "01"
    root = "/home/rachel/Desktop/fMRI Analysis/subjects"
    output_data = "/home/rachel/Desktop/fMRI Analysis/Scrubbed data"
    output_files = "/home/rachel/Desktop/fMRI Analysis"

    # Define data output
    error_log = os.path.join(output_files, "scrubbing_errors.txt")
    all_fwd_path = os.path.join(output_files, "all_fwd.csv")

    # 2. Concatenate all framewise_displ.txt files (per subject) into a single DataFrame so that there is one row per subject
    # Initialize an empty DataFrame to store results
    all_fwd_df = pd.DataFrame()

    # Iterate over all subjects in the root directory
    for subject in os.listdir(root):
        subject_dir = os.path.join(root, subject, "native_T1")
        fwd_file = os.path.join(subject_dir, "framewise_displ.txt")

        # Check if the framewise_displ.txt file exists for the subject
        if os.path.exists(fwd_file):
            
            # Read the framewise_displ.txt file
            fwd_data = pd.read_csv(fwd_file)
            
            # Convert each participant's column of data into a list to make it a single row of data instead
            fwd_series = pd.Series(fwd_data["FramewiseDisplacement"].tolist(), name=subject)
            fwd_row_df = fwd_series.to_frame().T
            
            # Append the row DataFrame to the main DataFrame
            all_fwd_df = pd.concat([all_fwd_df, fwd_row_df])
        
        else:
            print(f"No framewise_displ.txt found for {subject}")

    # 3. Save the concatenated DataFrame to all_fwd.csv
    all_fwd_df.to_csv(all_fwd_path, index=True, header=False)
    print(f"all_fwd.csv has been created at {all_fwd_path}")

    # 4. Visualize what different thresholds would look like in the data 
    analyze_threshold(all_fwd_df, 0.2)
    analyze_threshold(all_fwd_df, 0.5)

    # 5. Work on scrubbing the BOLD images

    # Define your threshold value here
    th = 0.5

    # Parallel processing of subjects
    todo = list(set(list(all_fwd_df.index)).difference(os.listdir(output_data)))

    # Convert the list to a df and save as a csv
    todo_df = pd.DataFrame(todo, columns=["todo"])
    todo_df.to_csv(os.path.join(output_files, "todo.csv"), index=False)

    if multi:
        with Pool(4) as pool:
            pool.starmap(process_subject, [(subject, ses, root, th, output_data, error_log) for subject in todo])
    else:
        for subject in todo:
            process_subject(subject, ses, root, th, output_data, error_log)

if __name__ == '__main__':
    main()
    # main(multi=True)  # Use this for parallel processing, default is set to not run any parallel processing
