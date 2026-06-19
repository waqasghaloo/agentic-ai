"""
Visual Agent — generates images for each section of a YouTube script.

How it works:
    1. Claude reads the script and writes a detailed image prompt per section
    2. For each prompt, calls image_tool (Flux via fal.ai)
    3. Saves images via PipelineState so they're cached and never regenerated
"""

import json
from pathlib import Path
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.tools.image_tool import generate_image
from src.pipeline.state import PipelineState


SYSTEM_PROMPT = """
You are a visual director for YouTube educational videos.
Given a video script, write image generation prompts for each key section.

For each section write a prompt that:
- Describes a specific, concrete visual scene (not abstract)
- Includes style guidance: "photorealistic, cinematic lighting, high detail"
- Works as a 16:9 YouTube video frame
- Contains no text, logos, or watermarks

Return ONLY a JSON array. No explanation. No markdown. Format:
[
  {"section": "hook", "prompt": "..."},
  {"section": "point-one", "prompt": "..."},
  {"section": "point-two", "prompt": "..."},
  {"section": "point-three", "prompt": "..."},
  {"section": "point-four", "prompt": "..."},
  {"section": "conclusion", "prompt": "..."}
]

Always return exactly 6 prompts in this order.
"""


class VisualAgent:
    """
    Agent that generates a set of images for a YouTube video script.

    Uses Claude to create image prompts, then generates each image via fal.ai.
    Saves to PipelineState so images are cached per topic.
    """

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL

    def run(self, script: str, state: PipelineState) -> list[str]:
        """
        Generate images for each section of the script.

        Args:
            script: The full video script text.
            state:  PipelineState for this topic — used to save images.

        Returns:
            List of paths to saved image files.
        """
        print("  [Visual Agent] Generating image prompts from script...")

        # Step 1: Ask Claude to write image prompts for each section
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Write image prompts for this video script:\n\n{script}",
                }
            ],
        )

        prompts = json.loads(response.content[0].text.strip())
        print(f"  [Visual Agent] {len(prompts)} prompts ready. Generating images...")

        # Step 2: Generate each image and save to state's images directory
        state.images_dir.mkdir(parents=True, exist_ok=True)

        for i, item in enumerate(prompts):
            section = item["section"]
            prompt = item["prompt"]
            output_path = state.images_dir / f"{i + 1:02d}-{section}.png"

            print(f"  [Visual Agent] Image {i + 1}/{len(prompts)}: {section}...")
            generate_image(prompt=prompt, output_path=output_path)

        image_paths = state.get_image_paths()
        print(f"  [Visual Agent] {len(image_paths)} images saved to: {state.images_dir}")
        return image_paths
