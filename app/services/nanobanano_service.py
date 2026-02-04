"""Nanobanano API Service for image generation (Chat Completions API)"""

import base64
import re
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

                images = self._parse_response(result)
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

                images = self._parse_response(result)
                return {"images": images, "raw_response": result}

            except httpx.TimeoutException:
                raise NanobananoError("Request timed out", status_code=504)
            except httpx.RequestError as e:
                raise NanobananoError(f"Request failed: {str(e)}", status_code=500)

    @staticmethod
    def _parse_response(result: dict) -> list:
        """
        Parse chat completion response and extract images.

        nano-banana-pro returns images in markdown format:
        ![image](data:image/jpeg;base64,/9j/4AAQ...)

        This method extracts the base64 data URI.
        """
        images = []
        if not result.get('choices') or len(result['choices']) == 0:
            return images

        content = result['choices'][0].get('message', {}).get('content', '')
        if not content:
            return images

        # Pattern 1: markdown image ![...](data:image/...;base64,...)
        md_pattern = r'!\[.*?\]\((data:image/[^)]+)\)'
        md_matches = re.findall(md_pattern, content)
        if md_matches:
            for data_uri in md_matches:
                images.append({"url": data_uri})
            return images

        # Pattern 2: raw data URI
        if content.strip().startswith('data:image/'):
            images.append({"url": content.strip()})
            return images

        # Pattern 3: HTTP URL
        if content.strip().startswith('http'):
            images.append({"url": content.strip()})
            return images

        # Pattern 4: URL inside text
        url_matches = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
        if url_matches:
            for url in url_matches:
                images.append({"url": url})
            return images

        # Fallback: return content as-is
        images.append({"content": content})
        return images

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
