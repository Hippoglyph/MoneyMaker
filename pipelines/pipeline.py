from database.database import Database
from generate.modelslab.modelslab import ModelSlab
from prompt.prompt_generator import PromptGenerator


class Pipeline:

    def run() -> None:
        prompt = PromptGenerator.generate()
        file_name = ModelSlab.generate(prompt)
        Database.log_file_upload_info(prompt, file_name)
