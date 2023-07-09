"""Wrapper around Writer APIs."""
from typing import Any, Dict, List, Mapping, Optional

import requests
from pydantic import Extra, root_validator

from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens
from langchain.schema.callbacks.manager import CallbackManagerForLLMRun
from langchain.utils import get_from_dict_or_env


class Writer(LLM):
    """Wrapper around Writer large language models.

    To use, you should have the environment variable ``WRITER_API_KEY`` and
    ``WRITER_ORG_ID`` set with your API key and organization ID respectively.

    Example:
        .. code-block:: python

            from langchain import Writer
            writer = Writer(model_id="palmyra-base")
    """

    writer_org_id: Optional[str] = None
    """Writer organization ID."""

    model_id: str = "palmyra-instruct"
    """Model name to use."""

    min_tokens: Optional[int] = None
    """Minimum number of tokens to generate."""

    max_tokens: Optional[int] = None
    """Maximum number of tokens to generate."""

    temperature: Optional[float] = None
    """What sampling temperature to use."""

    top_p: Optional[float] = None
    """Total probability mass of tokens to consider at each step."""

    stop: Optional[List[str]] = None
    """Sequences when completion generation will stop."""

    presence_penalty: Optional[float] = None
    """Penalizes repeated tokens regardless of frequency."""

    repetition_penalty: Optional[float] = None
    """Penalizes repeated tokens according to frequency."""

    best_of: Optional[int] = None
    """Generates this many completions server-side and returns the "best"."""

    logprobs: bool = False
    """Whether to return log probabilities."""

    n: Optional[int] = None
    """How many completions to generate."""

    writer_api_key: Optional[str] = None
    """Writer API key."""

    base_url: Optional[str] = None
    """Base url to use, if None decides based on model name."""

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and organization id exist in environment."""

        writer_api_key = get_from_dict_or_env(
            values, "writer_api_key", "WRITER_API_KEY"
        )
        values["writer_api_key"] = writer_api_key

        writer_org_id = get_from_dict_or_env(values, "writer_org_id", "WRITER_ORG_ID")
        values["writer_org_id"] = writer_org_id

        return values

    @property
    def _default_params(self) -> Mapping[str, Any]:
        """Get the default parameters for calling Writer API."""
        return {
            "minTokens": self.min_tokens,
            "maxTokens": self.max_tokens,
            "temperature": self.temperature,
            "topP": self.top_p,
            "stop": self.stop,
            "presencePenalty": self.presence_penalty,
            "repetitionPenalty": self.repetition_penalty,
            "bestOf": self.best_of,
            "logprobs": self.logprobs,
            "n": self.n,
        }

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            **{"model_id": self.model_id, "writer_org_id": self.writer_org_id},
            **self._default_params,
        }

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "writer"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call out to Writer's completions endpoint.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.

        Example:
            .. code-block:: python

                response = Writer("Tell me a joke.")
        """
        if self.base_url is not None:
            base_url = self.base_url
        else:
            base_url = (
                "https://enterprise-api.writer.com/llm"
                f"/organization/{self.writer_org_id}"
                f"/model/{self.model_id}/completions"
            )
        params = {**self._default_params, **kwargs}
        response = requests.post(
            url=base_url,
            headers={
                "Authorization": f"{self.writer_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={"prompt": prompt, **params},
        )
        text = response.text
        if stop is not None:
            # I believe this is required since the stop tokens
            # are not enforced by the model parameters
            text = enforce_stop_tokens(text, stop)
        return text
