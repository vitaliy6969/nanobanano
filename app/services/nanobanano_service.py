"""Nanobanano API Service for image generation and editing"""

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
    """Service for interacting with Nanobanano Pro API"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.nanobanano_api_key
        self.base_url = settings.nanobanano_api_url.rstrip("/")
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
            style: Optional style preset

        Returns:
            dict with 'images' list containing URLs or base64 data

        Raises:
            NanobananoError: If API request fails
        """
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": num_images,
        }

        if style:
            payload["style"] = style

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/generate",
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    raise NanobananoError(
                        f"Generation failed: {response.text}",
                        status_code=response.status_code
                    )

                return response.json()

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
            image_base64: Base64-encoded image data (alternative to URL)
            prompt: Edit instructions/prompt
            mask_url: Optional mask URL for inpainting
            strength: How much to modify (0.0-1.0)

        Returns:
            dict with 'images' list containing edited image URLs or base64 data

        Raises:
            NanobananoError: If API request fails
        """
        if not image_url and not image_base64:
            raise NanobananoError("Either image_url or image_base64 must be provided")

        payload = {
            "prompt": prompt,
            "strength": strength,
        }

        if image_url:
            payload["image_url"] = image_url
        else:
            payload["image"] = image_base64

        if mask_url:
            payload["mask_url"] = mask_url

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/edit",
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    raise NanobananoError(
                        f"Edit failed: {response.text}",
                        status_code=response.status_code
                    )

                return response.json()

            except httpx.TimeoutException:
                raise NanobananoError("Request timed out", status_code=504)
            except httpx.RequestError as e:
                raise NanobananoError(f"Request failed: {str(e)}", status_code=500)

    async def get_generation_status(self, task_id: str) -> dict:
        """
        Check the status of an async generation task.

        Args:
            task_id: The task ID returned from generate/edit

        Returns:
            dict with status and result if completed
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/status/{task_id}",
                    headers=self._get_headers(),
                )

                if response.status_code != 200:
                    raise NanobananoError(
                        f"Status check failed: {response.text}",
                        status_code=response.status_code
                    )

                return response.json()

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
