from pathlib import Path
from typing import Literal
from unittest.mock import Mock, patch

import pytest

from exposurestats.ai_tagger import (
    AITaggerConfig,
    AITaggerPipeline,
    LLMResponse,
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

    def tag_image(self, image: bytes, tags: list[str], detail: Literal["high", "low", "auto"] = "low") -> str:
        """Mock implementation of tag_image that returns a predefined response.

        Args:
            image: Base64 encoded image data
            tags: List of allowed tags to use
            detail: Level of detail for image analysis

        Returns:
            Predefined mock response text
        """
        return self.mock_response["content"]

    def tag_image_structured_output(
        self, image: bytes, tags: list[str], detail: Literal["high", "low", "auto"] = "low"
    ) -> LLMResponse:
        """Mock implementation that returns a structured response.

        Args:
            image: Base64 encoded image data
            tags: List of allowed tags to use
            detail: Level of detail for image analysis

        Returns:
            Structured mock response
        """
        return LLMResponse(
            explanation="This is a mock explanation of the image analysis",
            tags=["landscape", "mountain", "night"],
            additional_tags=["scenic", "nature"],
        )


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
        pipeline.llm.tag_image_structured_output.assert_called_once_with(
            image="base64_image_data", tags=pipeline.config.tags
        )
