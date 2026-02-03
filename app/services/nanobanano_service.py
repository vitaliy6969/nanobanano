"""Nanobanano API Service for image generation (OpenAI Images API compatible)"""

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
        Generate a new image from a text prompt.

        Args:
            prompt: The text prompt for image generation
            width: Image width in pixels
            height: Image height in pixels
            num_images: Number of images to generate
            style: Optional style preset (not used in this API)

        Returns:
            dict with 'images' list containing URLs

        Raises:
            NanobananoError: If API request fails
        """
        # nano-banana-pro supports only 1024x1024
        size = "1024x1024"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": num_images,
            "size": size,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    raise NanobananoError(
                        f"Generation failed: {response.text}",
                        status_code=response.status_code
                    )

                result = response.json()

                # Extract image URLs from OpenAI format response
                images = []
                if result.get('data'):
                    for item in result['data']:
                        if 'url' in item:
                            images.append({"url": item['url']})
                        elif 'b64_json' in item:
                            images.append({"b64_json": item['b64_json']})

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
        Note: This uses the edits endpoint if available.

        Args:
            image_url: URL of the image to edit
            image_base64: Base64-encoded image data (alternative to URL)
            prompt: Edit instructions/prompt
            mask_url: Optional mask URL for inpainting
            strength: How much to modify (0.0-1.0)

        Returns:
            dict with 'images' list containing edited image URLs

        Raises:
            NanobananoError: If API request fails
        """
        if not image_url and not image_base64:
            raise NanobananoError("Either image_url or image_base64 must be provided")

        # For now, use generations endpoint with modified prompt
        # since not all providers support edits
        edit_prompt = f"Edit the following image: {prompt}"

        payload = {
            "model": self.model,
            "prompt": edit_prompt,
            "n": 1,
            "size": "1024x1024",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/images/generations",
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
                if result.get('data'):
                    for item in result['data']:
                        if 'url' in item:
                            images.append({"url": item['url']})
                        elif 'b64_json' in item:
                            images.append({"b64_json": item['b64_json']})

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
