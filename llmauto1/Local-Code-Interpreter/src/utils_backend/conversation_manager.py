from typing import List, Dict
class ConversationManager:
    def __init__(self):
        self.conversation = []

    def add_message(self, role, content):
        self.conversation.append({"role": role, "content": content})

    def get_conversation(self):
        return self.conversation

    def clear_conversation(self):
        self.conversation.clear()
