import numpy as np
from scipy.stats import pearsonr
from itertools import combinations
from typing import List, Dict, Union
from dataclasses import dataclass

@dataclass
class FC:
    """
    Class to compute various functional connectivity (FC) metrics.
    
    Attributes:
        fisher_ztrans (bool): Flag to determine if Fisher z-transformation should be applied.
    """
    fisher_ztrans: bool

    def fisher_transform(self, correlations: np.ndarray) -> np.ndarray:
        """
        Apply Fisher z-transformation if required.
        
        Args:
            correlations (np.ndarray): Correlation coefficients.
        
        Returns:
            np.ndarray: Transformed correlation coefficients.
        """
        return np.arctanh(correlations) if self.fisher_ztrans else correlations

    def load_timeseries(self, filepath: str, index: int = None) -> np.ndarray:
        """
        Load timeseries data from a file.
        
        Args:
            filepath (str): Path to the timeseries file.
            index (int): Specific index if file contains multiple timeseries.
        
        Returns:
            np.ndarray: Loaded timeseries data.
        """
        data = np.genfromtxt(filepath, delimiter=' ')
        return data if index is None else data[index]

    def compute_one_to_all(self, subjects: Union[str, List[str]], 
                           one_timeseries_files: Union[str, List[str]], 
                           all_timeseries_files: Union[str, List[str]], 
                           one_timeseries_index: int = 0) -> List[Dict[str, Union[str, np.ndarray]]]:
        """
        Compute Pearson correlations between one timeseries and all other timeseries for given subjects.

        Args:
            subjects (Union[str, List[str]]): Single subject ID or list of subject IDs.
            one_timeseries_files (Union[str, List[str]]): Path or list of paths to the files containing the single timeseries data.
            all_timeseries_files (Union[str, List[str]]): Path or list of paths to the files containing all timeseries data.
            one_timeseries_index (int): The index of the specific timeseries in the file to compare against all timeseries. Default is 0.
        
        Returns:
            List[Dict[str, Union[str, np.ndarray]]]: A list of dictionaries containing the FC results and p-values for each subject.
        """
        if isinstance(subjects, str):
            subjects = [subjects]
        if isinstance(one_timeseries_files, str):
            one_timeseries_files = [one_timeseries_files]
        if isinstance(all_timeseries_files, str):
            all_timeseries_files = [all_timeseries_files]

        results = []
        for subject_id, one_ts_file, all_ts_file in zip(subjects, one_timeseries_files, all_timeseries_files):
            print(f"Loading timeseries for {subject_id}...")
            one_timeseries = self.load_timeseries(one_ts_file, one_timeseries_index)
            all_timeseries = self.load_timeseries(all_ts_file)

            print("Computing Pearson correlations...")
            fc_values, p_values = zip(*[pearsonr(one_timeseries, ts) for ts in all_timeseries])

            fc_array = self.fisher_transform(np.array(fc_values))
            results.append({"subject": subject_id, "FC": fc_array, "p": np.array(p_values)})

        return results

    def compute_all_to_all(self, subjects: Union[str, List[str]], timeseries_files: Union[str, List[str]]) -> List[Dict[str, Union[str, np.ndarray]]]:
        """
        Compute all-to-all Pearson correlations for one or multiple timeseries matrices.

        Args:
            subjects (Union[str, List[str]]): Single subject ID or list of subject IDs.
            timeseries_files (Union[str, List[str]]): Path or list of paths to the files containing timeseries data.
        
        Returns:
            list: A list of dictionaries containing the FC results for each subject.
        """
        if isinstance(subjects, str):
            subjects = [subjects]
        if isinstance(timeseries_files, str):
            timeseries_files = [timeseries_files]

        results = []
        for subject_id, timeseries_path in zip(subjects, timeseries_files):
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
            results.append({"subject": subject_id, "FC": fc_matrix, "p": p_matrix})

        return results

    def all_to_all_from_img(self, subject_id: str, bold_img: np.ndarray, mask_img: np.ndarray) -> Dict[str, Union[str, np.ndarray]]:
        """
        Compute all-to-all Pearson correlations from BOLD image and mask image.
        Calculates connectivity between every voxel that is in the altas mask.

        Args:
            subject_id (str): Subject ID.
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