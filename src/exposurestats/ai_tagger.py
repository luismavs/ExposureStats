import os
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Literal

from dotenv import load_dotenv
from loguru import logger
from openai import Client
from pydantic import BaseModel

from exposurestats.image import image_to_base64


class LLMResponse(BaseModel):
    explanation: str
    tags: list[str]
    additional_tags: list[str]


# templating with $
SYSTEM_PROMPT = """
        You are an agent specialized in tagging photographs.

        You will be provided with an image, and your goal is to tag the depicted scene with the provided keywords.
        You can give assign than one keyword to the photograph.
        Keywords should be concise and in lower case. 
        
        Allowed keywords are:
        $tags

        If no keywords describe the scene, you can return an empty list.

        Return:

        - List of found keywords
        - A short explanation of what you did
        - A list of additional keywords you may find relevant
        """


@dataclass
class AITaggerConfig:
    base_dir: Path
    system_prompt: str
    tags: list[str]
    openai_key: str
    openai_model: str = "gpt-4o-mini"

    def __post_init__(self):
        if isinstance(self.base_dir, str):
            self.base_dir = Path(self.base_dir)


class LLMTagger:
    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        """Initialize the LLM tagger.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            system_prompt: System prompt to guide model behavior. Will be used as a python string template
        """

        self.client = Client(api_key=api_key)
        self.model = model
        self.system_prompt = Template(system_prompt)

    def tag_image(self, image: bytes, tags: list[str], detail: Literal["high", "low", "auto"] = "low") -> str:
        """Tags an image using the OpenAI API.
        Args:
            image: Base64 encoded image data
            tags: List of allowed tags to use
            detail: Level of detail for image analysis. See OpenAI docs for options. https://platform.openai.com/docs/guides/vision#low-or-high-fidelity-image-understanding

        Returns:
            The model's response text

        """

        system_prompt = self.system_prompt.substitute(tags="\n - ".join(tags))
        logger.info(system_prompt)

        out = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image}",
                                "detail": detail,
                            },
                        },
                    ],
                },
            ],
            max_tokens=300,
            top_p=0.1,
        )
        return out.choices[0].message.content

    def tag_image_structured_output(
        self, image: bytes, tags: list[str], detail: Literal["high", "low", "auto"] = "low"
    ) -> LLMResponse:
        """Tags an image using the OpenAI API and returns structured output.
        Similar to tag_image() but returns a structured response object instead of raw text.

        Args:
            image: Base64 encoded image data
            tags: List of allowed tags to use
            detail: Level of detail for image analysis. See OpenAI docs for options. https://platform.openai.com/docs/guides/vision#low-or-high-fidelity-image-understanding

        Returns:
            Structured response containing the model's analysis
        """

        system_prompt = self.system_prompt.substitute(tags="\n - ".join(tags))
        logger.info(system_prompt)

        out = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image}",
                                "detail": detail,
                            },
                        },
                    ],
                },
            ],
            response_format=LLMResponse,
            max_tokens=300,
            top_p=0.1,
        )
        return out.choices[0].message.parsed


class AITaggerPipeline:
    def __init__(self, config: AITaggerConfig, llm: LLMTagger) -> None:
        """Initialize the AI tagger pipeline.

        Args:
            config: Configuration object containing settings for the pipeline
            llm: LLM tagger instance for making predictions. Instantiated outside to make it easier to swap later
        """
        self.config = config
        self.llm = llm

    def tag_image(self, image_path: str):
        """Tag an image using the AI pipeline.

        Args:
            image_path: Path to the image file relative to base_dir

        Returns:
            List of predicted tags for the image
        """

        base64_image = image_to_base64(self.config.base_dir / image_path, target_size=(512, 512))

        out = self.llm.tag_image_structured_output(image=base64_image, tags=self.config.tags)
        logger.success(out)

        return out.tags

    @classmethod
    def with_openAI(cls, config: AITaggerConfig):
        """Create from a config file, tied to specific LLMTagger"""
        return cls(
            config=config,
            llm=LLMTagger(api_key=config.openai_key, model=config.openai_model, system_prompt=config.system_prompt),
        )


if __name__ == "__main__":
    load_dotenv()

    tags = ["landscape", "BIF", "mountain", "city", "night", "stars", "golden-hour", "blue-hour"]
    cfg = AITaggerConfig(
        base_dir="data/images",
        tags=tags,
        openai_key=os.getenv("OPENAI_KEY"),
        system_prompt=SYSTEM_PROMPT,
    )

    pipe = AITaggerPipeline.with_openAI(cfg)

    pipe.tag_image(image_path="P7270969dxo.jpg")

    pipe.tag_image(image_path="P4240257.JPG")
