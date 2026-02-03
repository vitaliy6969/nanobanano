"""Nanobanano API Service for image generation (Chat Completions API)"""

import base64
from typing import Optional
from pathlib import Path

import httpx

from app.core.config import get_settings


class NanobananoError(Exception):
    """Custom exception for Nanobanano API errors"""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NanobananoService:
    """Service for interacting with Nanobanano/APIyi image generation API"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.nanobanano_api_key
        self.base_url = settings.nanobanano_api_url.rstrip("/")
        self.model = settings.nanobanano_model
        self.timeout = 120.0  # Image generation can take time

    def _get_headers(self) -> dict:
        """Get authorization headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        style: Optional[str] = None,
    ) -> dict:
        """
        Generate a new image from a text prompt using Chat Completions API.

        Args:
            prompt: The text prompt for image generation
            width: Image width (not used - model decides)
            height: Image height (not used - model decides)
            num_images: Number of images to generate
            style: Optional style preset

        Returns:
            dict with 'images' list containing URLs

        Raises:
            NanobananoError: If API request fails
        """
        # Build the image generation prompt
        image_prompt = f"Generate an image: {prompt}"
        if style:
            image_prompt += f" Style: {style}"

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": image_prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    raise NanobananoError(
                        f"Generation failed: {response.text}",
                        status_code=response.status_code
                    )

                result = response.json()

                # Extract image URL from chat response
                # The model returns image URL in the message content
                images = []
                if result.get('choices') and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    # Try to find URL in the response
                    if content:
                        # Check if content is a URL or contains URL
                        if content.startswith('http'):
                            images.append({"url": content.strip()})
                        elif 'http' in content:
                            # Extract URL from text
                            import re
                            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
                            for url in urls:
                                images.append({"url": url})
                        else:
                            # Content might be base64 or just text
                            images.append({"content": content})

                return {"images": images, "raw_response": result}

            except httpx.TimeoutException:
                raise NanobananoError("Request timed out", status_code=504)
            except httpx.RequestError as e:
                raise NanobananoError(f"Request failed: {str(e)}", status_code=500)

    async def edit_image(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        prompt: str = "",
        mask_url: Optional[str] = None,
        strength: float = 0.8,
    ) -> dict:
        """
        Edit an existing image based on a prompt.

        Args:
            image_url: URL of the image to edit
            image_base64: Base64-encoded image data
            prompt: Edit instructions/prompt
            mask_url: Optional mask URL
            strength: How much to modify

        Returns:
            dict with 'images' list containing edited image URLs

        Raises:
            NanobananoError: If API request fails
        """
        if not image_url and not image_base64:
            raise NanobananoError("Either image_url or image_base64 must be provided")

        # Build edit prompt with image reference
        edit_prompt = f"Edit this image: {prompt}"
        if image_url:
            edit_prompt = f"Based on the image at {image_url}, {prompt}"

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": edit_prompt
                }
            ]
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    raise NanobananoError(
                        f"Edit failed: {response.text}",
                        status_code=response.status_code
                    )

                result = response.json()

                images = []
                if result.get('choices') and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    if content:
                        if content.startswith('http'):
                            images.append({"url": content.strip()})
                        elif 'http' in content:
                            import re
                            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
                            for url in urls:
                                images.append({"url": url})
                        else:
                            images.append({"content": content})

                return {"images": images, "raw_response": result}

            except httpx.TimeoutException:
                raise NanobananoError("Request timed out", status_code=504)
            except httpx.RequestError as e:
                raise NanobananoError(f"Request failed: {str(e)}", status_code=500)

    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """
        Convert a local image file to base64 string.

        Args:
            image_path: Path to the image file

        Returns:
            Base64-encoded string of the image
        """
        path = Path(image_path)
        if not path.exists():
            raise NanobananoError(f"Image file not found: {image_path}")

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
