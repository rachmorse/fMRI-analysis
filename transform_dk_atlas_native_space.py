
# To run this file, run this in terminal because FreeSurfer needs to be called first:
# source /home/rachel/freesurfer/freesurfer/SetUpFreeSurfer.sh
# /home/rachel/Desktop/fMRI\ Analysis/venv/bin/python /home/rachel/Desktop/fMRI\ Analysis/DK76\ atlas\ to\ native\ space.py

import os
import subprocess

# # Function to source the FreeSurfer environment
# def source_freesurfer():
#     """
#     This function locates the FreeSurfer setup script (`SetUpFreeSurfer.sh`) in the FreeSurfer home directory,
#     executes it in a new shell, and updates the current environment with any variables defined in the script.

#     Note:
#         This function uses `/bin/bash` to source the script and capture the environment variables.

#     Raises:
#         Exception: If the FreeSurfer setup script cannot be found or executed.
#     """
#     freesurfer_home = "/home/rachel/freesurfer/freesurfer"
#     setup_script = os.path.join(freesurfer_home, 'SetUpFreeSurfer.sh')
#     command = f"source {setup_script} && env"
#     process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, executable="/bin/bash")
    
#     # Update the environment variables
#     for line in process.stdout:
#         key, _, value = line.decode().partition("=")
#         os.environ[key.strip()] = value.strip()
#     process.communicate()

# # Source FreeSurfer environment
# source_freesurfer()

# Main function for script
def main():
    """
    Main function to create a DK atlas in the BOLD image space for each subject.

    This function performs the following tasks:

    1. Defines and updates necessary paths for input and output directories.
    2. Reads list of subject IDs to process from a specified file (todo_file).
    3. Ensures the output directory exists.
    4. For each subject, constructs and executes the `mri_vol2vol` command to register the DK altas segmentation (that is in T1 from reconall process) to the subject BOLD image.
    5. Checks for the existence of necessary files before processing each subject.
    6. Handles any errors that occur during the execution of the command.

    Notes:
        - Paths such as `freesurfer_home`, `freesurfer_folder`, `bids_folder`, `output_folder`, and `todo_file` should be updated to reflect the correct locations on your system.
        - The session timepoint `ses` is set to "01" by default; modify as needed.
        - The `mri_vol2vol` command uses Nearest Neighbor interpolation and performs registration using the header.

    Outputs:
        - Native space DK atlas BOLD images per subject saved in the specified `output_folder` with filenames in the format `{subject_id}_DK76_BOLD-nativespace.nii.gz`.
        - Console messages indicating the progress and status of each subject's processing.

    Raises:
        SystemExit: If the todo_file does not exist.
        Exception: If any subprocess command fails or if required files for a subject are missing.
    """
    
    # Define paths and update as needed
    freesurfer_folder = "/home/rachel/Desktop/fMRI Analysis/subjects/freesurfer-reconall"
    bids_folder = "/home/rachel/Desktop/fMRI Analysis/subjects/BIDS"
    output_folder = "/home/rachel/Desktop/fMRI Analysis/DK76"
    todo_file = "/home/rachel/Desktop/fMRI Analysis/todo.csv"
    ses = "01"

    # Read subject IDs from the file
    if not os.path.isfile(todo_file):
        print(f"Todo file {todo_file} does not exist. Exiting.")
        exit(1)

    with open(todo_file, 'r') as file:
        subject_ids = file.read().splitlines()

    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)

    # Process each subject
    for subject_id in subject_ids:
        print(f"Processing {subject_id}...")
        
        # Define file paths
        mov_file = os.path.join(freesurfer_folder, subject_id, "mri", "aparc.DKTatlas+aseg.mgz")
        targ_file = os.path.join(bids_folder, subject_id, f"ses-{ses}", "func", f"{subject_id}_ses-{ses}_run-01_rest_bold_ap.nii.gz")
        output_file = os.path.join(output_folder, f"{subject_id}_DK76_BOLD-nativespace.nii.gz")

        # Check if the files exist before processing
        if not os.path.isfile(mov_file):
            print(f"Mov file {mov_file} does not exist. Skipping {subject_id}.")
            continue

        if not os.path.isfile(targ_file):
            print(f"Targ file {targ_file} does not exist. Skipping {subject_id}.")
            continue

        # Construct the mri_vol2vol command
        cmd = [
            "mri_vol2vol",
            "--mov", mov_file,
            "--targ", targ_file,
            "--o", output_file,
            "--regheader",
            "--interp", "nearest"
        ]

        # Execute the command
        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully processed {subject_id}. Output saved to {output_file}.")
        except subprocess.CalledProcessError as e:
            print(f"Error processing {subject_id}: {e}")

if __name__ == '__main__':
    main()