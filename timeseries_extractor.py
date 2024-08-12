import os
import nibabel as nib
import numpy as np
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TimeseriesExtractor:
    """
    Class to extract timeseries data from fMRI BOLD images using the DK atlas in native BOLD space.

    Args:
        masks_root_path (Path): Path where atlases (e.g. masks) are stored.
        unique_mask (bool): Flag to determine if masks are unique per subject.
        mask_filename_template (str): Pattern for the mask file names.
    """

    masks_root_path: Path
    unique_mask: bool
    mask_filename_template: str

    def extract_and_save_timeseries(self, subject_id, bold_file_path, output_file):
        """
        Extracts timeseries from a BOLD image for a given subject using their DK mask
        and saves the extracted timeseries to the output file.
        
        Args:
            subject_id (str): Subject ID.
            bold_file_path (str): Path to the BOLD image file resampled to the DK atlas.
            output_file (str): Path where the extracted timeseries will be saved.
        """
        print(f"--- Processing subject: {subject_id} ---")
        
        # Load BOLD image
        print("Reading BOLD image...")
        try:
            bold_img = nib.load(bold_file_path).get_fdata()
            print("BOLD image loaded")
        except FileNotFoundError:
            print(f"BOLD file not found: {bold_file_path}")
            return
        except Exception as e:
            print(f"Error loading BOLD image: {e}")
            return
        
        # Process masks and extract timeseries
        timeseries = self._process_masks_and_extract_timeseries(subject_id, bold_img, output_file)
        
        # Save timeseries if valid timeseries were extracted
        if timeseries.size > 0:
            np.savetxt(output_file, timeseries)
            print(f"Timeseries saved to {output_file}")
        else:
            print("No valid timeseries extracted")
    
    def _process_masks_and_extract_timeseries(self, subject_id, bold_img, output_file):
            """
            Processes the masks and extracts timeseries data from the BOLD image for a given subject.
            
            Args:
                subject_id (str): Subject ID.
                bold_img (numpy.ndarray): BOLD image data.
                output_file (str): Path where the extracted timeseries will be saved.

            Returns:
                numpy.ndarray: Extracted timeseries data from all applicable masks.
            """
            timeseries = []
            mask_filename = self.mask_filename_template.format(subject_id=subject_id)
            mask_path = os.path.join(self.masks_root_path, mask_filename)
            
            # Load mask
            try:
                print(f"Reading mask: {mask_path}")
                mask = nib.load(mask_path).get_fdata()
                print("Mask loaded")
            except FileNotFoundError:
                print(f"Mask file not found: {mask_path}")
                return np.array([])
            except Exception as e:
                print(f"Error loading mask: {e}")
                return np.array([])

            # Extract timeseries from the mask
            mask_timeseries = self._extract_timeseries_from_mask(mask, bold_img, subject_id, output_file)
            timeseries.append(mask_timeseries)

            return np.concatenate(timeseries, axis=0) if timeseries else np.array([])

    def _extract_timeseries_from_mask(self, mask, bold_img, subject_id, output_file):
        """
        Extracts the timeseries data from the BOLD image using the given mask.
        
        Args:
            mask (numpy.ndarray): Mask data.
            bold_img (numpy.ndarray): BOLD image data.
            subject_id (str): Subject ID.
            output_file (str): Path where the extracted timeseries will be saved.

        Returns:
            numpy.ndarray: Extracted timeseries data.
        """
        print("Extracting timeseries using mask...")
        if mask.ndim == 4:  # Each slice is a separate network in a 4D mask
            return self._extract_timeseries_from_4d_mask(mask, bold_img, subject_id, output_file)
        elif mask.ndim == 3:  # 3D mask with multiple networks encoded as unique values
            return self._extract_timeseries_from_3d_mask(mask, bold_img, subject_id, output_file)
        else:
            raise ValueError(f'Mask has an unexpected dimensionality: {mask.ndim}')

    def _extract_timeseries_from_4d_mask(self, mask, bold_img, subject_id, output_file):
        """
        Extracts timeseries from a 4D mask where each slice represents a network.
        
        Args:
            mask (numpy.ndarray): 4D mask data.
            bold_img (numpy.ndarray): BOLD image data.
            subject_id (str): Subject ID.
            output_file (str): Path where error logs are recorded (if necessary).

        Returns:
            numpy.ndarray: Extracted timeseries data.
        """
        timeseries = []
        n_networks = mask.shape[3]
        print(f"Extracting 4D timeseries (from 1 to {n_networks})")

        for i in range(n_networks):
            ROI_timeseries = self._compute_ROI_timeseries(mask[..., i], bold_img, subject_id, output_file, i)
            if len(timeseries) == 0:
                timeseries = ROI_timeseries
            else:
                timeseries = np.vstack((timeseries, ROI_timeseries))
        
        return timeseries

    def _extract_timeseries_from_3d_mask(self, mask, bold_img, subject_id, output_file):
        """
        Extracts timeseries from a 3D mask where unique values represent different networks.
        
        Args:
            mask (numpy.ndarray): 3D mask data.
            bold_img (numpy.ndarray): BOLD image data.
            subject_id (str): Subject ID.
            output_file (str): Path where error logs are recorded (if necessary).

        Returns:
            numpy.ndarray: Extracted timeseries data.
        """
        timeseries = []
        unique_ROIs = np.unique(mask)
        unique_ROIs = unique_ROIs[unique_ROIs != 0]  # Exclude background (0)
        n_networks = len(unique_ROIs)
    
        print(f"Extracting 3D timeseries (from 1 to {n_networks})")

        for roi_val in unique_ROIs:
            ROI_timeseries = self._compute_ROI_timeseries(mask == roi_val, bold_img, subject_id, output_file, roi_val)
            if len(timeseries) == 0:
                timeseries = ROI_timeseries
            else:
                timeseries = np.vstack((timeseries, ROI_timeseries))
        
        return timeseries

    def _compute_ROI_timeseries(self, mask_slice, bold_img, subject_id, output_file, roi_id):
        """
        Computes the timeseries for a given ROI mask slice.
        
        Args:
            mask_slice (numpy.ndarray): 3D mask slice data for a specific ROI.
            bold_img (numpy.ndarray): BOLD image data.
            subject_id (str): Subject ID.
            output_file (str): Path where error logs are recorded (if necessary).
            roi_id (int): ROI ID.

        Returns:
            numpy.ndarray: Computed ROI timeseries data.
        """
        ROI_timeseries = []
        coords = np.where(mask_slice)

        for t in range(bold_img.shape[3]):
            # Extract mean BOLD signal in mask region at time t
            ROI_timeseries.append(np.mean(bold_img[coords[0], coords[1], coords[2], t]))

        # Check if the extracted series are constant
        if np.all(np.array(ROI_timeseries) == np.array(ROI_timeseries)[0]):
            print(f"Constant timeseries detected for ROI {roi_id}")
            if output_file:
                with open(os.path.join(os.path.dirname(output_file), "errors_timeseries_extraction.txt"), "a") as f:
                    f.write(f"{subject_id}: constant timeseries at ROI {roi_id}\n")

        return np.array(ROI_timeseries)