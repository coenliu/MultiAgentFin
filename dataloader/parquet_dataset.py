import pandas as pd

class ParquetDataset:
    def __init__(self, data_frame: pd.DataFrame):
        """
        Initializes the dataset for inference.

        Args:
            data_frame (pd.DataFrame): DataFrame containing the data.
        """
        self.data_frame = data_frame.reset_index(drop=True)
        self.data = data_frame

    def __len__(self):
        return len(self.data_frame)

    def __getitem__(self, idx):
        sample = self.data_frame.iloc[idx]
        return sample.to_dict()

    def filter_by_task(self, task_name):
        """
        Filters the dataset by task name.

        Args:
            task_name (str): The task name to filter by.

        Returns:
            ParquetDataset: A new ParquetDataset instance containing only samples with the specified task name.
        """
        if 'task' not in self.data_frame.columns:
            raise ValueError("The 'task' column is not present in the dataset.")

        filtered_df = self.data_frame[self.data_frame['task'] == task_name].reset_index(drop=True)
        return ParquetDataset(filtered_df)

    def sample(self, n):
        """
        Randomly samples n rows from the dataset.

        Args:
            n (int): The number of samples to return.

        Returns:
            pd.DataFrame: A DataFrame containing the sampled rows.
        """
        if n > len(self):
            raise ValueError(f"Cannot sample {n} items from a dataset with only {len(self)} items.")

        sampled_df = self.data_frame.sample(n=n, random_state=42).reset_index(drop=True)
        return sampled_df

    def select_top_n(self, n):
        """
        Selects the top n rows from the dataset.

        Args:
            n (int): The number of top rows to return.

        Returns:
            ParquetDataset: A new ParquetDataset instance containing only the top n rows.
        """
        if n > len(self):
            raise ValueError(f"Cannot select top {n} rows from a dataset with only {len(self)} items.")

        top_n_df = self.data_frame.head(n).reset_index(drop=True)
        return ParquetDataset(top_n_df)