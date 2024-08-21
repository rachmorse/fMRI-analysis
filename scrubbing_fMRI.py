import os
import pandas as pd
import numpy as np
import nibabel as nib
import scipy.interpolate
import matplotlib.pyplot as plt
from multiprocessing import Pool


def analyze_threshold(data, threshold, total_scans=740, affected_percentage=0.5):
    """
    Analyze and visualize subjects with a high amount of movement using a given FWD threshold (e.g. subjects with > X FWD in > Y% of scans).
    Note - this is to consider what your data look like to help determine the threshold and affected percentage to use for scrubbing.

    Args:
        data (pd.DataFrame): DataFrame containing FWD data.
        threshold (float): The FWD threshold to be compared with.
        total_scans (int, optional): The total number of scans per subject. Default is 740.
        affected_percentage (float, optional): The percentage of affected scans. Default is 50%.
    """
    moved_subjects_count = (
        ((data > threshold).sum(1) / total_scans) > affected_percentage
    ).sum()
    print(
        f"{moved_subjects_count} subjects with more than {affected_percentage * 100}% of scans moved (threshold {threshold})"
    )
    plt.hist((data > threshold).sum(1) / total_scans)
    plt.title(f"Distribution of Percentage of Moved Scans (Threshold: {threshold})")
    plt.xlabel("Percentage")
    plt.ylabel("Number of Subjects")
    plt.show()


def scrub(bold_file, fwd_file, scrubbed_file, threshold=0.5, method="interpolate"):
    """
    Scrub the BOLD fMRI images by either removing or interpolating scans based on FWD threshold.

    Args:
        bold_file (str): Path to the BOLD image file (NIfTI format).
        fwd_file (str): Path to the FWD file (CSV format).
        scrubbed_file (str): Path to save the scrubbed BOLD image file (NIfTI format).
        threshold (float, optional): Threshold for FWD above which scans are considered moved. Default is 0.5 FWD.
        method (str, optional): Method for handling moved scans. Either 'cut' to remove or 'interpolate' to replace. Default is 'interpolate'.

    Raises:
        Exception: If an unknown method is specified.
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
    correct_tps = all_tps[[False] + list(fwd < threshold)]
    incorrect_tps = all_tps[[False] + list(fwd >= threshold)]
    correct_bold = bold_data[:, :, :, correct_tps]

    print(
        f"{len(incorrect_tps)} out of {bold_data.shape[3]} scans ({round(len(incorrect_tps) * 100 / bold_data.shape[3], 2)}%) exceed the motion threshold (FWD > {threshold})."
    )

    # Start scrubbing based on the method
    if method == "cut":
        # If the method is 'cut', remove the timepoints with excessive motion. Save as scrubbed_data.
        scrubbed_data = correct_bold
        print(f"Removing {len(incorrect_tps)} scans due to excessive motion.")
    elif method == "interpolate":
        # If the method is 'interpolate', replace the timepoints with excessive motion through interpolation or extrapolation.
        scrubbed_data = bold_data.copy()
        # Check if the first or last timepoints are incorrect because if they are, they should be extrapolated
        if 1 not in incorrect_tps and bold_data.shape[3] - 1 not in incorrect_tps:
            print(f"Interpolating {len(incorrect_tps)} scans due to excessive motion.")
            # Perform interpolation when neither the first nor last timepoints are incorrect
            interpolator = scipy.interpolate.interp1d(
                correct_tps, correct_bold, axis=3, fill_value="extrapolate"
            )
            scrubbed_data[:, :, :, incorrect_tps] = interpolator(incorrect_tps)
            print("No scans require extrapolation.")
        else:
            extrap_idx = []
            intrap_idx = list(incorrect_tps)
            extrap_text = []
            i = 1
            # Perform left extrapolation for incorrect first timepoint
            while i in incorrect_tps:
                extrap_idx.append(i)
                intrap_idx.remove(i)
                extrap_text.append("left")
                i += 1
            i = 1
            # Perform right extrapolation for incorrect last timepoint
            while bold_data.shape[3] - i in incorrect_tps:
                extrap_idx.append(bold_data.shape[3] - i)
                intrap_idx.remove(bold_data.shape[3] - i)
                extrap_text.append("right")
                i += 1

            print(f"Interpolating {len(intrap_idx)} scans due to excessive motion.")
            interpolator = scipy.interpolate.interp1d(correct_tps, correct_bold, axis=3)
            scrubbed_data[:, :, :, intrap_idx] = interpolator(intrap_idx)

            if extrap_text:
                print(
                    f"Extrapolating {len(extrap_idx)} scans in the {', '.join(extrap_text)} direction(s) due to motion."
                )
                extrapolator = scipy.interpolate.interp1d(
                    correct_tps, correct_bold, fill_value="extrapolate", axis=3
                )
                scrubbed_data[:, :, :, extrap_idx] = extrapolator(extrap_idx)

    else:
        print("Unknown method specified; returning the original BOLD file.")
        scrubbed_data = bold_data  # Unchanged; return original BOLD data

    scrubbed_image = nib.Nifti1Image(scrubbed_data, bold_affine)
    os.makedirs(os.path.dirname(scrubbed_file), exist_ok=True)
    nib.save(scrubbed_image, scrubbed_file)

    print(f"Scrubbing complete. Scrubbed image saved to: {scrubbed_file}")


def process_subject(
    subject,
    ses,
    root,
    threshold,
    output_data,
    error_log,
    bold_pattern,
    scrubbed_pattern,
):
    """
    Processes a single subject by scrubbing the BOLD fMRI images based on the FWD.
    Saves the scrubbed BOLD file for the subject and logs errors if any occur.

    Args:
        subject (str): Subject ID used to process the BOLD and FWD files.
        ses (str): Session (timepoint).
        root (str): Root directory path.
        threshold (float): Threshold value for scrubbing.
        output_data (str): Output data directory path.
        error_log (str): Error log file path.
        bold_pattern (str): Pattern for the BOLD file names.
        scrubbed_pattern (str): Pattern for the scrubbed file names.

    Raises:
        Exception: If any error occurs during the processing of the subject.
    """
    try:
        fwd_file = os.path.join(root, subject, "native_T1", "framewise_displ.txt")
        bold_file = bold_pattern.format(subject=subject, ses=ses)
        scrubbed_file = scrubbed_pattern.format(
            subject=subject, ses=ses, threshold=threshold, output_data=output_data
        )

        print(f"Processing subject: {subject}")

        if not os.path.exists(scrubbed_file):
            scrub(
                bold_file,
                fwd_file,
                scrubbed_file,
                threshold=threshold,
                method="interpolate",
            )
        else:
            print("Already scrubbed!")
    except Exception as e:
        print(f"Error processing subject {subject}: {e}")
        with open(error_log, "a") as f:
            f.write(f"Error processing subject {subject}: {e}\n")


def main(
    ses,
    root,
    output_data,
    output_files,
    threshold,
    bold_pattern,
    scrubbed_pattern,
    multi=False,
):
    """
    Main function to run this script. This function performs the following steps:

    1. Defines session, threshold, and directories for data input and output.
    2. Iterates over all subjects in the root directory to concatenate their `framewise_displ.txt` files into a single DataFrame.
    3. Saves the concatenated DataFrame to `all_fwd.csv`.
    4. Visualizes data thresholds using the `analyze_threshold` function.
    5. Generates a list of subjects to be processed and saves it as `todo.csv`.
    6. Scrubs the BOLD images by either serial or parallel processing of subjects.
    7. Saves the scrubbed BOLD images to the output directory.
    8. Logs errors to `scrubbing_errors.txt`.

    Args:
        ses (str): Session (timepoint).
        root (str): Root directory path.
        output_data (str): Output data directory path (for MRI data).
        output_files (str): Output files directory path (for error, todo, and FWD CSVs).
        threshold (float): Threshold value for scrubbing.
        bold_pattern (str): Pattern for the BOLD file names.
        scrubbed_pattern (str): Pattern for the scrubbed file names.
        multi (bool): If True, enables parallel processing using multiprocessing. Defaults to False.

    Raises:
        Exception: If any required file or directory is not found.
    """
    error_log = os.path.join(output_files, "scrubbing_errors.txt")
    all_fwd_path = os.path.join(output_files, "all_fwd.csv")

    # Concatenate all framewise_displ.txt files (per subject) into a single DataFrame
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
            fwd_series = pd.Series(
                fwd_data["FramewiseDisplacement"].tolist(), name=subject
            )
            fwd_row_df = fwd_series.to_frame().T

            # Append the row DataFrame to the main DataFrame
            all_fwd_df = pd.concat([all_fwd_df, fwd_row_df])
        else:
            print(f"No framewise_displ.txt found for {subject}")

    # Save the concatenated DataFrame to all_fwd.csv
    all_fwd_df.to_csv(all_fwd_path, index=True, header=False)
    print(f"all_fwd.csv has been created at {all_fwd_path}")

    # Visualize what different thresholds would look like in the data
    analyze_threshold(all_fwd_df, 0.2)
    analyze_threshold(all_fwd_df, 0.5)

    # Work on scrubbing the BOLD images
    todo = list(set(list(all_fwd_df.index)).difference(os.listdir(output_data)))

    # Convert the list to a DataFrame and save as a CSV
    todo_df = pd.DataFrame(todo, columns=["todo"])
    todo_df.to_csv(os.path.join(output_files, "todo.csv"), index=False)

    # Parallel processing
    if multi:
        with Pool(4) as pool:
            pool.starmap(
                process_subject,
                [
                    (
                        subject,
                        ses,
                        root,
                        threshold,
                        output_data,
                        error_log,
                        bold_pattern,
                        scrubbed_pattern,
                    )
                    for subject in todo
                ],
            )
    else:
        for subject in todo:
            process_subject(
                subject,
                ses,
                root,
                threshold,
                output_data,
                error_log,
                bold_pattern,
                scrubbed_pattern,
            )


if __name__ == "__main__":
    # Change to your paths and settings
    ses = "01"
    threshold = 0.5
    root = "/home/rachel/Desktop/fMRI Analysis/subjects/processed data"
    output_data = "/home/rachel/Desktop/fMRI Analysis/Scrubbed data"
    output_files = "/home/rachel/Desktop/fMRI Analysis"

    # Define file patterns
    bold_pattern = os.path.join(
        root,
        "{subject}",
        "native_T1",
        "{subject}_ses-{ses}_run-01_rest_bold_ap_T1-space.nii.gz",
    )
    scrubbed_pattern = os.path.join(
        "{output_data}",
        "{subject}",
        "native_T1",
        "{subject}_ses-{ses}_run-01_rest_bold_ap_T1-space_scrubbed_{threshold}.nii.gz",
    )

    main(
        ses,
        root,
        output_data,
        output_files,
        threshold,
        bold_pattern,
        scrubbed_pattern,
        multi=False,
    )

    # Uncomment this line to enable parallel processing
    # main(ses, root, output_data, output_files, threshold, bold_pattern, scrubbed_pattern, multi=True)
