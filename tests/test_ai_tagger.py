from pathlib import Path
from typing import Literal
from unittest.mock import Mock, patch

import pytest

from exposurestats.ai_tagger import (
    AITaggerConfig,
    AITaggerPipeline,
    LLMResponse,
    get_system_prompt,
)


class MockLLMTagger:
    """
    A mock version of LLMTagger for testing purposes that returns predefined responses
    instead of calling OpenAI.
    """

    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        self.model = model
        self.system_prompt = system_prompt

        # Predefined mock responses
        self.mock_response = {
            "content": """
            {
                "explanation": "This is a mock explanation of the image analysis",
                "tags": ["landscape", "mountain", "night"],
                "additional_tags": ["scenic", "nature"]
            }
            """
        }

    def tag_image(self, image: bytes, detail: Literal["high", "low", "auto"] = "low") -> str:
        """Mock implementation of tag_image that returns a predefined response.

        Args:
            image: Base64 encoded image data
            detail: Level of detail for image analysis

        Returns:
            Predefined mock response text
        """
        return self.mock_response["content"]

    def tag_image_structured_output(self, image: bytes, detail: Literal["high", "low", "auto"] = "low") -> LLMResponse:
        """Mock implementation that returns a structured response.

        Args:
            image: Base64 encoded image data
            detail: Level of detail for image analysis

        Returns:
            Structured mock response
        """
        return LLMResponse(
            explanation="This is a mock explanation of the image analysis",
            tags=["landscape", "mountain", "night"],
            additional_tags=["scenic", "nature"],
        )


def test_get_system_prompt():
    """Test system prompt generation with sample labels"""
    labels = ["landscape", "mountain", "night"]
    prompt = get_system_prompt(labels)

    assert "landscape" in prompt
    assert "mountain" in prompt
    assert "night" in prompt
    assert "Keywords should be concise" in prompt


class TestAITaggerConfig:
    def test_init_with_string_path(self):
        """Test config initialization with string path"""
        config = AITaggerConfig(
            base_dir="test/path", system_prompt="test prompt", tags=["tag1", "tag2"], openai_key="test_key"
        )
        assert isinstance(config.base_dir, Path)
        assert str(config.base_dir) == "test/path"

    def test_init_with_path_object(self):
        """Test config initialization with Path object"""
        path = Path("test/path")
        config = AITaggerConfig(
            base_dir=path, system_prompt="test prompt", tags=["tag1", "tag2"], openai_key="test_key"
        )
        assert config.base_dir == path


# class TestLLMTagger:
#     @pytest.fixture
#     def llm_tagger(self):
#         """Create a basic LLMTagger instance"""
#         tagger = LLMTagger(api_key="test_key", model="test_model", system_prompt="test prompt")
#         tagger.client = Mock()
#         return tagger

#     def test_init(self, llm_tagger):
#         """Test LLMTagger initialization"""
#         assert llm_tagger.model == "test_model"
#         assert llm_tagger.system_prompt == "test prompt"

#     @patch("openai.Client")
#     def test_tag_image(self, mock_client, llm_tagger):
#         """Test basic image tagging"""
#         # Mock the OpenAI response
#         mock_response = ChatCompletion(
#             id="test_id",
#             model="test_model",
#             choices=[
#                 Choice(
#                     finish_reason="stop",
#                     index=0,
#                     message=ChatCompletionMessage(content="Test response", role="assistant"),
#                 )
#             ],
#             created=1234567890,
#             object="chat.completion",
#         )

#         mock_client.return_value.chat.completions.create.return_value = mock_response

#         result = llm_tagger.tag_image(image=b"test_image_bytes")
#         assert result == "Test response"

#     @patch("openai.Client")
#     def test_tag_image_structured_output(self, mock_client, llm_tagger):
#         """Test structured output image tagging"""
#         mock_response = Mock()
#         mock_response.choices = [Mock()]
#         mock_response.choices[0].message.parsed = LLMResponse(
#             explanation="Test explanation", tags=["tag1", "tag2"], additional_tags=["extra1"]
#         )

#         mock_client.return_value.beta.chat.completions.parse.return_value = mock_response

#         result = llm_tagger.tag_image_structured_output(image=b"test_image_bytes")
#         assert isinstance(result, LLMResponse)
#         assert result.tags == ["tag1", "tag2"]
#         assert result.explanation == "Test explanation"
#         assert result.additional_tags == ["extra1"]


class TestAITaggerPipeline:
    @pytest.fixture
    def pipeline(self):
        """Create a basic pipeline instance with mocked components"""
        config = AITaggerConfig(
            base_dir="test/path", system_prompt="test prompt", tags=["tag1", "tag2"], openai_key="test_key"
        )
        llm = Mock()
        return AITaggerPipeline(config=config, llm=llm)

    @patch("exposurestats.ai_tagger.image_to_base64")
    def test_tag_image(self, mock_to_base64, pipeline):
        """Test the complete pipeline tagging process"""
        # Mock the base64 conversion
        mock_to_base64.return_value = "base64_image_data"

        # Mock the LLM response
        pipeline.llm.tag_image_structured_output.return_value = LLMResponse(
            explanation="Test explanation", tags=["landscape", "night"], additional_tags=["sunset"]
        )

        result = pipeline.tag_image("test_image.jpg")

        # Verify the results
        assert result == ["landscape", "night"]
        mock_to_base64.assert_called_once()
        pipeline.llm.tag_image_structured_output.assert_called_once_with(image="base64_image_data")
