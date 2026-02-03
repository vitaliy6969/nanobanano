"""ChatGPT Service for prompt generation"""

from openai import AsyncOpenAI

from app.core.config import get_settings


class ChatGPTService:
    """Service for generating professional image prompts using ChatGPT"""

    SYSTEM_PROMPT = """You are an expert AI image prompt engineer specializing in creating detailed,
professional prompts for image generation systems like Nanobanano Pro.

Your task is to transform user descriptions (in any language) into detailed English prompts that include:
1. Main subject with specific details
2. Art style (photorealistic, digital art, oil painting, etc.)
3. Lighting conditions (soft lighting, dramatic shadows, golden hour, etc.)
4. Composition and camera angle
5. Color palette and mood
6. Technical quality keywords (4K, highly detailed, sharp focus, etc.)

Format your response as a single, coherent prompt paragraph without explanations.
Keep the prompt under 300 words but make it comprehensive."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.chatgpt_model
        self.max_tokens = settings.chatgpt_max_tokens

    async def generate_prompt(self, user_description: str) -> str:
        """
        Generate a professional image generation prompt from user description.

        Args:
            user_description: User's idea in any language

        Returns:
            Professional English prompt for image generation
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Create an image generation prompt for: {user_description}"}
            ],
            max_tokens=self.max_tokens,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    async def generate_edit_prompt(self, original_prompt: str, edit_request: str) -> str:
        """
        Generate a prompt for editing an existing image.

        Args:
            original_prompt: The original prompt used to create the image
            edit_request: What changes the user wants

        Returns:
            Modified prompt incorporating the edit request
        """
        edit_system_prompt = """You are an expert at modifying image generation prompts.
Given an original prompt and an edit request, create a new prompt that incorporates the requested changes
while maintaining the overall style and quality of the original.
Output only the new prompt, no explanations."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": edit_system_prompt},
                {"role": "user", "content": f"Original prompt: {original_prompt}\n\nEdit request: {edit_request}\n\nNew prompt:"}
            ],
            max_tokens=self.max_tokens,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()
