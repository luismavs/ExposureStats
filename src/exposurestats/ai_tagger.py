from dataclasses import dataclass
from pathlib import Path
from openai import Client
from dotenv import load_dotenv
import os
from typing import Literal
from exposurestats.image import image_to_base64
from loguru import logger
from pydantic import BaseModel


class LLMResponse(BaseModel):
    explanation: str
    tags: list[str]
    additional_tags: list[str]


def get_system_prompt(labels: list[str]):
    lbls = "\n - ".join(labels)

    system_prompt = f"""
        You are an agent specialized in tagging photographs.

        You will be provided with an image, and your goal is to tag the depicted scene with keywords.
        You can give more than one keyword to the photograph.
        
        Keywords should be concise and in lower case. 
        
        Possible keywords are:
        {lbls}

        Return:

        - List of found keywords
        - An explanation of what you did
        - A list of additional keywords you may find relevant
        """
    return system_prompt


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
        self.client = Client(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt

    def tag_image(self, image: bytes, detail: Literal["high", "low", "auto"] = "low") -> str:
        """Tags an image using the OpenAI API.

        Args:
            system_prompt: The system prompt to guide the model's behavior
            user_prompt: The prompt to send to the model
            image: Base64 encoded image data
            detail: https://platform.openai.com/docs/guides/vision#low-or-high-fidelity-image-understanding

        Returns:
            The model's response text

        """

        logger.info(self.system_prompt)

        out = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
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

    def tag_image_structured_output(self, image: bytes, detail: Literal["high", "low", "auto"] = "low") -> LLMResponse:
        """Tags an image using the OpenAI API and returns structured output.

        Args:
            image: Base64 encoded image data
            detail: Level of detail for image analysis. See OpenAI docs for options

        Returns:
            Structured response containing the model's analysis
        """

        logger.info(self.system_prompt)

        out = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
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

        out = self.llm.tag_image_structured_output(image=base64_image)
        logger.success(out)

        return out.tags


if __name__ == "__main__":
    load_dotenv()

    tags = ["landscape", "BIF", "mountain", "city", "night", "stars", "golden-hour", "blue-hour"]
    cfg = AITaggerConfig(
        base_dir="data/images",
        tags=tags,
        openai_key=os.getenv("OPENAI_KEY"),
        system_prompt="",  # Added missing required parameter
    )

    pipe = AITaggerPipeline(
        config=cfg,
        llm=LLMTagger(api_key=cfg.openai_key, model=cfg.openai_model, system_prompt=get_system_prompt(labels=tags)),
    )

    pipe.tag_image(image_path="P7270969dxo.jpg")
