import os
import pandas as pd
import numpy as np
import nibabel as nib

def main():
    """
    Main function to process and save ROI-specific NIfTI images for each subject.
    
    This function reads a list of subjects and a list of chosen ROIs, then processes the 
    corresponding NIfTI files to zero out ROIs that are not in the list.
    """
    # Define output folder path
    output_folder = "/home/rachel/Desktop/fMRI Analysis/DK76"

    # Read chosen areas from CSV and convert the indices to a list
    chosen_areas_df = pd.read_csv("/pool/guttmann/laboratori/scripts/BOLD_connectivity/chosen_areas.csv", index_col=0)
    chosen_areas = list(chosen_areas_df.index)

    # Read the list of subjects from a text file
    with open("/home/rachel/Desktop/fMRI Analysis/todo.csv", "r") as f:
        subjects_list = f.read().splitlines()
    subjects_list = [s for s in subjects_list if s]  # Filter out empty strings

    # Process each subject
    for subject_id in subjects_list:
        print(f"Processing subject: {subject_id}")
        nifti_file = os.path.join(output_folder, f"{subject_id}_DK76_BOLD-nativespace.nii.gz")

        if os.path.exists(nifti_file):
            # Load the NIfTI image
            aparcaseg_image = nib.load(nifti_file)
            aparcaseg_data = aparcaseg_image.get_fdata()
            aparcaseg_affine = aparcaseg_image.affine

            # Zero out regions not in the chosen areas list
            aparcaseg_data[~np.isin(aparcaseg_data, chosen_areas)] = 0

            # Create a new NIfTI image with the modified data
            rois_image = nib.Nifti1Image(aparcaseg_data, aparcaseg_affine)

            # Define new file name to avoid overwriting
            new_nifti_file = os.path.join(output_folder, f"{subject_id}_DK76_BOLD-nativespace_selected_ROIs.nii.gz")

            # Save the new NIfTI image
            nib.save(rois_image, new_nifti_file)

            # Output indicating successful processing
            print(f"Successfully processed and saved {subject_id}.")
        else:
            # Output if the NIfTI file doesn't exist
            print(f"NIfTI file for {subject_id} does not exist. Skipping subject.")

if __name__ == '__main__':
    main()