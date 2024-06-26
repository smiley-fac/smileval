from .base import ChatCompletionModel, ChatMessage, ChatCompletionOptions, EmbeddingModel, default_options
from ..utils import map_attribute

import os
import openai

class OpenAIChatCompletionModel(ChatCompletionModel):
    def __init__(self, name: str, api_key: str | None = None, base_url: str | None = None, spoof_api_name: str | None = None, extended = False):
        super().__init__(name)
        opts = {}
        if os.getenv("OPENAI_BASE_URL"):
            opts["base_url"] = os.getenv("OPENAI_BASE_URL")
        if base_url:
            opts["base_url"] = base_url


        if os.getenv("OPENAI_API_KEY"):
            opts["api_key"] = os.getenv("OPENAI_API_KEY")
        if api_key:
            opts["api_key"] = api_key
        
        self.client = openai.AsyncOpenAI(**opts)
        self.opts = opts
        self.model_name = name
        if spoof_api_name:
            self.model_name = spoof_api_name
        self.is_extended: bool = extended

    async def chat_complete(self, messages: list[ChatMessage], options: ChatCompletionOptions = default_options) -> ChatMessage:
        super().chat_complete_log_request(messages, options)
        messages, options = super().preprocess_inputs(messages, options)
        openai_kwargs = {}
        map_attribute(options, openai_kwargs, "temperature", "temperature")
        map_attribute(options, openai_kwargs, "top_p", "top_p")
        map_attribute(options, openai_kwargs, "stop_tokens", "stop")
        map_attribute(options, openai_kwargs, "seed", "seed") # important
        map_attribute(options, openai_kwargs, "max_tokens", "max_tokens")
        extra_args = {}
        if self.is_extended:
            # Mirostat
            map_attribute(options, extra_args, "mirostat", "mirostat")
            map_attribute(options, extra_args, "mirostat_eta", "mirostat_eta")
            map_attribute(options, extra_args, "mirostat_tau", "mirostat_tau")
            # Alt names
            map_attribute(options, extra_args, "max_tokens", "n_predict")
            # sampling
            map_attribute(options, extra_args, "top_k", "top_k")
            map_attribute(options, extra_args, "min_p", "min_p")
        completions = await self.client.chat.completions.create(messages = ChatMessage.to_api_format(messages), model = self.model_name,extra_body = extra_args, **openai_kwargs)
        # types get funky here for some reason
        completion_message = ChatMessage(completions.choices[0].message.content, role = completions.choices[0].message.role).mark_as_generated()
        super().chat_complete_log_response(completion_message.content)
        return completion_message

class OpenAIEmbeddingModel(EmbeddingModel):
    def __init__(self, name: str, api_key: str | None = "sk-placeholder", host: str | None = None, spoof_api_name: str | None = None):
        super().__init__(name)
        opts = {}
        if os.getenv("OPENAI_BASE_URL"):
            opts["base_url"] = os.getenv("OPENAI_BASE_URL")
        if host:
            opts["base_url"] = host


        if os.getenv("OPENAI_API_KEY"):
            opts["api_key"] = os.getenv("OPENAI_API_KEY")
        if api_key:
            opts["api_key"] = api_key
        
        self.client = openai.AsyncOpenAI(**opts)
        self.opts = opts
        self.model_name = name
        if spoof_api_name:
            self.model_name = spoof_api_name
    
    async def embed(self, messages: str | list[str]) -> list[list[float]]:
        raise NotImplemented("todo")