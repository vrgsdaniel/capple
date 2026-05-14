from src.settings import get_llm_settings
from langchain_core.language_models.chat_models import BaseChatModel


class Chatbot:
    def __init__(self):
        self._settings = get_llm_settings()
        self.stream = self._settings.stream
        self.llm = self._build_llm()

    def _build_llm(self) -> BaseChatModel:
        """
        Intended to be overridden by subclasses to construct the appropriate LLM instance based on settings.
        """
        raise NotImplementedError("Subclasses must implement _build_llm() to return an LLM instance.")

    def invoke(self, messages):
        return self.llm.invoke(messages)

    def stream(self, messages):
        return self.llm.stream(messages)


class OpenAIChatbot(Chatbot):
    def _build_llm(self) -> BaseChatModel:
        """
        Construct a ``ChatOpenAI`` instance from the current settings.
        """
        from langchain_openai import ChatOpenAI

        extra_body: dict[str, bool] = {}
        if self._settings.open_ai_free_models_only:
            extra_body["free_models_only"] = True

        chat_kwargs = {
            "model": self._settings.open_ai_model,
            "base_url": self._settings.open_ai_base_url,
            "api_key": self._settings.open_ai_api_key.get_secret_value(),
            "temperature": self._settings.temperature,
            "max_retries": self._settings.max_retries,
        }
        if extra_body:
            chat_kwargs["extra_body"] = extra_body

        return ChatOpenAI(
            **chat_kwargs,
        )


class AzureChatbot(Chatbot):
    def _build_llm(self) -> BaseChatModel:
        """
        Construct an ``AzureChatOpenAI`` instance from the current settings.
        """
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=self._settings.azure_openai_endpoint,
            azure_deployment=self._settings.azure_deployment,
            openai_api_version=self._settings.open_ai_version,
            api_key=self._settings.azure_openai_api_key.get_secret_value(),
            temperature=self._settings.temperature,
            max_retries=self._settings.max_retries,
        )


class AnthropicChatbot(Chatbot):
    def _build_llm(self) -> BaseChatModel:
        """
        Construct an ``ChatAnthropic`` instance from the current settings.
        """
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=self._settings.anthropic_model,
            api_key=self._settings.anthropic_api_key.get_secret_value(),
            temperature=self._settings.temperature,
            max_retries=self._settings.max_retries,
        )


class ChatbotFactory:
    @staticmethod
    def create_chatbot(vendor: str | None = None) -> Chatbot:
        selected_vendor = vendor or get_llm_settings().provider

        if selected_vendor == "azure":
            return AzureChatbot()
        if selected_vendor == "openai":
            return OpenAIChatbot()
        # Add more vendors here as needed
        raise ValueError(f"Unsupported vendor: {selected_vendor}")
