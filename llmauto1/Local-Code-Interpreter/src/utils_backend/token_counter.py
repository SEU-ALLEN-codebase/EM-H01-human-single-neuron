import tiktoken

class TokenCounter:
    def __init__(self, model):
        self.model = model
        self.total_tokens = 0
        self.encoding = self._get_encoding()

    def _get_encoding(self):
        if self.model == "GPT-4":
            return tiktoken.encoding_for_model("gpt-4")
        elif self.model == "GPT-3.5":
            return tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def count_tokens(self, text):
        return len(self.encoding.encode(text))

    def add_to_total(self, count):
        self.total_tokens += count

    def get_total_tokens(self):
        return self.total_tokens

    def reset_total(self):
        self.total_tokens = 0

    def clear_cache(self):
        # If there's any caching mechanism, clear it here
        pass