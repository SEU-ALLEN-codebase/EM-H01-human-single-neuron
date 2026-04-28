import unittest
from unittest.mock import patch
from parameterized import parameterized
from src.bot_backend import BotBackend

class TestBotBackend(unittest.TestCase):

    def setUp(self):
        self.bot_backend = BotBackend()

    def test_initialization(self):
        self.assertIsNotNone(self.bot_backend)
        self.assertEqual(self.bot_backend.gpt_model_choice, "GPT-4")

    @parameterized.expand([
        ("GPT-3.5", "GPT-3.5"),
        ("GPT-4", "GPT-4"),
    ])
    def test_update_gpt_model_choice(self, input_model, expected_model):
        self.bot_backend.update_gpt_model_choice(input_model)
        self.assertEqual(self.bot_backend.gpt_model_choice, expected_model)

    def test_update_invalid_gpt_model_choice(self):
        with self.assertRaises(ValueError):
            self.bot_backend.update_gpt_model_choice("Invalid-Model")

    @patch.object(BotBackend, 'execute_code')
    def test_execute_code(self, mock_execute):
        mock_execute.return_value = "Hello, World!"
        result = self.bot_backend.execute_code("print('Hello, World!')")
        self.assertEqual(result, "Hello, World!")
        mock_execute.assert_called_once_with("print('Hello, World!')")

    def test_add_text_message(self):
        initial_length = len(self.bot_backend.conversation)
        self.bot_backend.add_text_message("Test message")
        self.assertEqual(len(self.bot_backend.conversation), initial_length + 1)
        self.assertEqual(self.bot_backend.conversation[-1]["content"], "Test message")

    def test_add_empty_message(self):
        initial_length = len(self.bot_backend.conversation)
        self.bot_backend.add_text_message("")
        self.assertEqual(len(self.bot_backend.conversation), initial_length)

    def test_add_long_message(self):
        long_message = "a" * 10000
        self.bot_backend.add_text_message(long_message)
        self.assertEqual(self.bot_backend.conversation[-1]["content"], long_message)

if __name__ == '__main__':
    unittest.main()
