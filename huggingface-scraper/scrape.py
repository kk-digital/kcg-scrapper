import json
import argparse
from typing import List
from huggingface_hub import HfApi

# Define models class
class FileInformation:
    def __init__(self, filename: str, file_hash: str, size: int):
        self.filename = filename
        self.file_hash = file_hash
        self.size = size

class ModelInformation:
    def __init__(self, name: str, model_hash: str, files: List[FileInformation]):
        self.name = name
        self.model_hash = model_hash
        self.files = files

class HuggingfaceModels:
    def __init__(self):
        self.models = []

    def register_model(self, model: ModelInformation):
        self.models.append(model)

    def __str__(self):
        return ",".join([model.name for model in self.models])
        
# Parse the arguments
parser = argparse.ArgumentParser(
    prog='huggingface-scrapper'
)
parser.add_argument('-o', '--output', default="./output.json", type=str)
parser.add_argument('-n', '--limit', default=3, type=int, help='Specifies the limit of models to fetch of all the models available in HF.')

args = parser.parse_args()

# Search all models in HF's api
api = HfApi()
response = api.list_models(
    full = True,
    fetch_config = False,
    limit = args.limit
)

HFModels = HuggingfaceModels()   
for model in response:
    files = api.list_repo_tree(model.id, recursive=True)
    final_files = []
    for file in files:
        final_files.append(FileInformation(file.path, file.blob_id, file.size))
        
    HFModels.register_model(ModelInformation(
        model.id,
        model.sha,
        final_files
    ))

with open(args.output, "w") as outfile:
    json.dump(HFModels, outfile,
               indent=1,
               default= lambda x: getattr(x, '__dict__', str(x)))