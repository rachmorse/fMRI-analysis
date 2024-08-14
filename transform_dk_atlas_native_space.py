import os
import subprocess
from typing import Union
from pathlib import Path


def process_subject(
    subject_id: str,
    freesurfer_folder: Path,
    fmri_folder: Path,
    output_folder: Path,
    mov_template: str,
    targ_template: str,
    output_template: str,
    session: str,
):
    """
    Process an individual subject to create DK atlas in their BOLD image space.

    Args:
        subject_id (str): Subject ID
        freesurfer_folder (Path): Path to the FreeSurfer recon-all folder.
        fmri_folder (Path): Path to the fMRI preprocessed folder.
        output_folder (Path): Path to the output folder.
        mov_template (str): Path / template for the input file (e.g. DK atlas).
        targ_template (str): Path / template for the output file (e.g. fMRI image).
        output_template (str): Path / template for the output file (e.g. DK atlas transformed to fMRI image).
        session (str): Timepoint.

    Raises:
        Exception: If any subprocess command fails or if required files for a subject are missing.
    """
    print(f"Processing {subject_id}...")

    mov_file = mov_template.format(subject_id=subject_id)
    targ_file = targ_template.format(subject_id=subject_id, session=session)
    output_file = output_template.format(subject_id=subject_id)

    # Check if the files exist before processing
    if not os.path.isfile(mov_file):
        print(f"Mov file {mov_file} does not exist. Skipping {subject_id}.")
        return

    if not os.path.isfile(targ_file):
        print(f"Targ file {targ_file} does not exist. Skipping {subject_id}.")
        return

    # Construct the mri_vol2vol command
    cmd = [
        "mri_vol2vol",
        "--mov",
        mov_file,
        "--targ",
        targ_file,
        "--o",
        output_file,
        "--regheader",
        "--interp",
        "nearest",
    ]

    # Execute the command
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully processed {subject_id}. Output saved to {output_file}.")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {subject_id}: {e}")


def main(
    freesurfer_folder: Union[str, Path],
    output_folder: Union[str, Path],
    fmri_folder: Union[str, Path],
    mov_template: str,
    targ_template: str,
    output_template: str,
    todo_file: Union[str, Path],
    session: str,
):
    """
    Main function to create a DK atlas in the BOLD image space for each subject.

    Args:
        freesurfer_folder (Path): Path to the FreeSurfer recon-all folder.
        output_folder (Path): Path to the output folder.
        fmri_folder (Path): Path to the fMRI preprocessed folder.
        mov_template (str): Path / template for the input file (e.g. DK atlas).
        targ_template (str): Path / template for the output file (e.g. fMRI image).
        output_template (str): Path / template for the output file (e.g. DK atlas transformed to fMRI image).
        todo_file (Path): Path to the todo file (created in scrubbing_fMRI.py) with subject IDs to be processed.
        session (str): Timepoint.

    Raises:
        FileNotFoundError: If the `todo_file` does not exist.
        Exception: If any subprocess command fails or if required files for a subject are missing.
    """

    # Read subject IDs from the file
    if not os.path.isfile(todo_file):
        print(f"Todo file {todo_file} does not exist. Exiting.")
        exit(1)

    with open(todo_file, "r") as file:
        subject_ids = file.read().splitlines()

    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)

    # Process each subject
    for subject_id in subject_ids:
        process_subject(
            subject_id,
            freesurfer_folder,
            fmri_folder,
            output_folder,
            mov_template,
            targ_template,
            output_template,
            session,
        )


if __name__ == "__main__":
    # Define paths and update as needed
    todo_file = Path("/home/rachel/Desktop/fMRI Analysis/todo.csv")
    freesurfer_path = Path(
        "/home/rachel/Desktop/fMRI Analysis/subjects/freesurfer-reconall"
    )
    fmri_folder = Path("/home/rachel/Desktop/fMRI Analysis/subjects/Preprocessed")
    output_directory = Path("/home/rachel/Desktop/fMRI Analysis/DK76")
    session = "01"

    # Define how your files are named
    mov_files = "aparc.DKTatlas+aseg.mgz"
    targ_files = "{subject_id}_ses-{session}_run-01_rest_bold_ap_T1-space.nii.gz"
    output_files = "{subject_id}_DK76_BOLD-nativespace.nii.gz"

    try:
        with open(todo_file, "r") as f:
            subjects_list = f.read().splitlines()

        subjects_list = [subject_id for subject_id in subjects_list if subject_id]

        # Construct full paths to the NIfTI files
        mov_template = freesurfer_path / "{subject_id}" / "mri" / mov_files
        targ_template = fmri_folder / targ_files.format(
            subject_id="{subject_id}", session=session
        )
        output_template = output_directory / output_files

        main(
            freesurfer_folder=freesurfer_path,
            output_folder=output_directory,
            fmri_folder=fmri_folder,
            mov_template=str(mov_template),
            targ_template=str(targ_template),
            output_template=str(output_template),
            todo_file=todo_file,
            session=session,
        )

    except FileNotFoundError:
        print(f"Todo file not found at: {todo_file}")
