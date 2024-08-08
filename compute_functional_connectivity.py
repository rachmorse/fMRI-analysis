
import numpy as np
from scipy.stats import pearsonr
from itertools import combinations
from typing import List, Dict, Union

class FC:
    """
    Class to compute various functional connectivity (FC) metrics.
    
    Attributes:
    fisher_ztrans (bool): Flag to determine if Fisher z-transformation should be applied.
    """

    def __init__(self, fisher_ztrans: bool = True):
        """
        Initialize the FC class with an optional Fisher z-transformation.
        
        Parameters:
        fisher_ztrans (bool): Whether to apply Fisher z-transformation.
        """
        self.fisher_ztrans = fisher_ztrans

    def fisher_transform(self, correlations: np.ndarray) -> np.ndarray:
        """
        Apply Fisher z-transformation if required.
        
        Parameters:
        correlations (np.ndarray): Correlation coefficients.
        
        Returns:
        np.ndarray: Transformed correlation coefficients.
        """
        return np.arctanh(correlations) if self.fisher_ztrans else correlations

    def load_timeseries(self, filepath: str, index: int = None) -> np.ndarray:
        """
        Load timeseries data from a file.
        
        Parameters:
        filepath (str): Path to the timeseries file.
        index (int): Specific index if file contains multiple timeseries.
        
        Returns:
        np.ndarray: Loaded timeseries data.
        """
        data = np.genfromtxt(filepath, delimiter=' ')
        return data if index is None else data[index]

    def one_to_all(
        self, 
        subject_id: str, 
        one_timeseries_path: str, 
        all_timeseries_path: str, 
        one_timeseries_index: int = 0
    ) -> Dict[str, Union[str, np.ndarray]]:
        """
        Compute Pearson correlations between one ROI's timeseries and all other ROIs timeseries.
        
        Parameters:
        subject_id (str): Subject ID.
        one_timeseries_path (str): Path to the single timeseries file.
        all_timeseries_path (str): Path to the file containing all timeseries.
        one_timeseries_index (int): Index of the timeseries to be used from the one timeseries file.
        
        Returns:
        dict: A dictionary containing the subject identifier, FC, and p-values.
        """
        print("Loading timeseries...")
        one_timeseries = self.load_timeseries(one_timeseries_path, one_timeseries_index)
        all_timeseries = self.load_timeseries(all_timeseries_path)

        print("Computing Pearson correlations...")
        fc_values, p_values = zip(*[pearsonr(one_timeseries, ts) for ts in all_timeseries])

        fc_array = self.fisher_transform(np.array(fc_values))
        return {"subject": subject_id, "FC": fc_array, "p": np.array(p_values)}

    def multiple_one_to_all(
        self, 
        subjects: List[str], 
        one_timeseries_files: List[str], 
        all_timeseries_files: List[str], 
        one_timeseries_index: int = 0
    ) -> List[Dict[str, Union[str, np.ndarray]]]:
        """
        Compute one-to-all correlations for multiple subjects.
        
        Parameters:
        subjects (list): List of subject IDs.
        one_timeseries_files (list): List of paths to the single timeseries files.
        all_timeseries_files (list): List of paths to the files containing all timeseries.
        one_timeseries_index (int): Index of the timeseries to be used from the one timeseries file.
        
        Returns:
        list: A list of dictionaries containing the FC results for each subject.
        """
        return [
            self.one_to_all(subject_id, one_ts, all_ts, one_timeseries_index)
            for subject_id, one_ts, all_ts in zip(subjects, one_timeseries_files, all_timeseries_files)
        ]

    def all_to_all(self, subject_id: str, timeseries_path: str) -> Dict[str, Union[str, np.ndarray]]:
        """
        Compute all-to-all Pearson correlations for a given timeseries matrix.
        For example, if you have `N` ROIs, this computes the correlation for each pair of ROIs, 
        resulting in an `N x N` connectivity matrix. 
        
        Parameters:
        subject_id (str): Subject identifier.
        timeseries_path (str): Path to the file containing timeseries data.
        
        Returns:
        dict: A dictionary containing the subject identifier, FC, and p-values.
        """
        print(f"Loading timeseries for {subject_id}...")
        timeseries_data = self.load_timeseries(timeseries_path)

        num_timeseries = timeseries_data.shape[0]
        print("Computing Pearson correlations...")
        print(f"\t{num_timeseries}x{num_timeseries} matrix of connectivity")

        # Prepare matrices for FC and p-values
        fc_matrix = np.zeros((num_timeseries, num_timeseries))
        p_matrix = np.ones((num_timeseries, num_timeseries))

        # Iterate over all pairs of timeseries and compute correlations
        for i, j in combinations(range(num_timeseries), 2):
            correlation, p_value = pearsonr(timeseries_data[i], timeseries_data[j])
            fc_matrix[i, j] = fc_matrix[j, i] = correlation
            p_matrix[i, j] = p_matrix[j, i] = p_value

        fc_matrix = self.fisher_transform(fc_matrix)
        return {"subject": subject_id, "FC": fc_matrix, "p": p_matrix}

    def multiple_all_to_all(self, subjects: List[str], timeseries_files: List[str]) -> List[Dict[str, Union[str, np.ndarray]]]:
        """
        Compute all-to-all correlations for multiple subjects.
        
        Parameters:
        subjects (list): List of subject identifiers.
        timeseries_files (list): List of paths to the files containing timeseries data.
        
        Returns:
        list: A list of dictionaries containing the FC results for each subject.
        """
        return [self.all_to_all(subject_id, ts) for subject_id, ts in zip(subjects, timeseries_files)]

    def all_to_all_from_img(self, subject_id: str, bold_img: np.ndarray, mask_img: np.ndarray) -> Dict[str, Union[str, np.ndarray]]:
        """
        Compute all-to-all Pearson correlations from BOLD image and mask image.
        Calculates connectivity between every voxel that is in the altas mask.
        
        Parameters:
        subject_id (str): Subject identifier.
        bold_img (np.ndarray): BOLD image data.
        mask_img (np.ndarray): Mask image data.
        
        Returns:
        dict: A dictionary containing the subject identifier, and FC results.
        """
        num_voxels = np.sum(mask_img > 0)
        print("Computing Pearson correlations...")
        print(f"\t{num_voxels}x{num_voxels} matrix of connectivities")

        voxels_of_interest = (
            np.array([np.where(mask_img == i)[0][0] for i in range(1, num_voxels + 1)]),
            np.array([np.where(mask_img == i)[1][0] for i in range(1, num_voxels + 1)]),
            np.array([np.where(mask_img == i)[2][0] for i in range(1, num_voxels + 1)])
        )

        matrix = bold_img[voxels_of_interest]
        fc_matrix = np.corrcoef(matrix)
        
        print("\tDiagonal set to zero")
        np.fill_diagonal(fc_matrix, 0)
        
        fc_matrix = self.fisher_transform(fc_matrix)
        return {"subject": subject_id, "FC": fc_matrix}