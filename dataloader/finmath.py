import json
import random

class FinMathDataset:
    def __init__(self, file_path:str):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def __len__(self):

        return len(self.data)

    def __getitem__(self, idx):

        if 0 <= idx < len(self.data):
            return self.data[idx]
        else:
            raise IndexError("Index out of range")

    def sample(self, n):

        return random.sample(self.data, min(n, len(self.data)))

    def select_top_n(self, n):

        return self.data[:n]

    def get_dataset(self):
        return self.data