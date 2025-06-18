from functools import cache
import json
import random


class PromptGenerator:

    @cache
    def _get_options(file_name :str) -> list[str]:
        with open("prompt/options/"+file_name) as f:
            return json.loads(f.read())
        
    def _get_objects_options() -> list[str]:
        return PromptGenerator._get_options("object_options")
    
    def _get_subject_options() -> list[str]:
        return PromptGenerator._get_options("subject_options")
    
    def _get_scen_options() -> list[str]:
        return PromptGenerator._get_options("scen_options")
    
    def generate() -> str:
        object_pick = random.choice(PromptGenerator._get_objects_options())
        subject_pick = random.choice(PromptGenerator._get_subject_options())
        scen_pick = random.choice(PromptGenerator._get_scen_options())
        return f"{object_pick} saves {subject_pick} from {scen_pick}"