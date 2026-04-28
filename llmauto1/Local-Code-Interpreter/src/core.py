import os
from typing import Dict, List, Tuple, Any
from bot_backend import BotBackend
from typing import Dict, List, Tuple, Optional, Any

def initialization(state_dict: Dict[str, Any]) -> None:
    if not os.path.exists('cache'):
        os.mkdir('cache')
    if state_dict["bot_backend"] is None:
        state_dict["bot_backend"] = BotBackend()
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

def get_bot_backend(state_dict: Dict[str, Any]) -> BotBackend:
    return state_dict["bot_backend"]

def switch_model(state_dict: Dict[str, Any], model: str) -> None:
    bot_backend = get_bot_backend(state_dict)
    bot_backend.update_gpt_model_choice(model)

def add_text(state_dict: Dict[str, Any], history: List[Tuple[str, Optional[str]]], text: str) -> Tuple[List[Tuple[str, Optional[str]]], Dict[str, Any]]:
    bot_backend = get_bot_backend(state_dict)
    bot_backend.add_text_message(user_text=text)
    history = history + [(text, None)]
    return history, state_dict

def bot(state_dict: Dict[str, Any], history: List[Tuple[str, Optional[str]]], progress: Any = None) -> List[Tuple[str, Optional[str]]]:
    bot_backend = get_bot_backend(state_dict)
    while bot_backend.finish_reason in ('new_input', 'function_call'):
        if history[-1][1]:
            history.append([None, ""])
        else:
            history[-1][1] = ""
        
        if progress:
            progress(0.5, desc="Generating response")
        
        response = chat_completion(bot_backend=bot_backend)
        
        if progress:
            progress(0.75, desc="Parsing response")
        
        history, _ = parse_response(
            chunk=response,
            history=history,
            bot_backend=bot_backend
        )
        
        if progress:
            progress(1.0, desc="Completed")
    
    return history