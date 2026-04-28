from typing import Literal
class ModelManager:
    def __init__(self, default_model="GPT-4"):
        self.current_model = default_model

    def get_current_model(self):
        return self.current_model

    def switch_model(self, model_choice):
        self.current_model = model_choice
