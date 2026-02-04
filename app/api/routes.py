"""Main API routes for AI Image Hub"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_token
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.requests import GenerateRequest, EditRequest
from app.schemas.responses import (
    GenerateResponse,
    TransactionResponse,
    HistoryResponse,
    ErrorResponse,
)
from app.services.chatgpt_service import ChatGPTService
from app.services.nanobanano_service import NanobananoService, NanobananoError

router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Generate new image",
    description="Generate a new image from a text description. The description will be enhanced by ChatGPT.",
)
async def generate_image(
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_token),
):
    """
    Generate a new image from user description.

    1. Receives user description (any language)
    2. Sends to ChatGPT to create professional prompt
    3. Sends prompt to Nanobanano for image generation
    4. Logs everything to database
    5. Returns result
    """
    # Create transaction record
    transaction = Transaction(
        original_request=request.description,
        operation_type="generate",
        status=TransactionStatus.PENDING,
    )
    db.add(transaction)
    await db.flush()

    try:
        # Step 1: Generate prompt with ChatGPT
        transaction.status = TransactionStatus.PROCESSING
        await db.flush()

        chatgpt_service = ChatGPTService()
        generated_prompt = await chatgpt_service.generate_prompt(request.description)
        transaction.generated_prompt = generated_prompt
        await db.flush()

        # Step 2: Generate image with Nanobanano
        nanobanano_service = NanobananoService()
        result = await nanobanano_service.generate_image(
            prompt=generated_prompt,
            width=request.width,
            height=request.height,
            style=request.style,
        )

        # Extract image URL from result
        image_url = None
        if "images" in result and result["images"]:
            first_image = result["images"][0]
            image_url = first_image.get("url") or first_image.get("data") or first_image.get("content")
        elif "url" in result:
            image_url = result["url"]
        elif "image_url" in result:
            image_url = result["image_url"]

        # Update transaction with success
        transaction.status = TransactionStatus.SUCCESS
        transaction.result_image_url = image_url
        if "task_id" in result:
            transaction.task_id = result["task_id"]

        await db.commit()

        return GenerateResponse(
            success=True,
            transaction_id=transaction.id,
            message="Image generated successfully",
            original_request=request.description,
            generated_prompt=generated_prompt,
            image_url=image_url,
            status=TransactionStatus.SUCCESS.value,
        )

    except NanobananoError as e:
        transaction.status = TransactionStatus.ERROR
        transaction.error_message = e.message
        await db.commit()

        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message,
        )

    except Exception as e:
        transaction.status = TransactionStatus.ERROR
        transaction.error_message = str(e)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )


@router.post(
    "/edit",
    response_model=GenerateResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Edit existing image",
    description="Edit an existing image based on a text description of the changes.",
)
async def edit_image(
    request: EditRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_token),
):
    """
    Edit an existing image.

    1. Receives image URL/base64 and edit description
    2. Sends to ChatGPT to create edit prompt
    3. Sends to Nanobanano for image editing
    4. Logs everything to database
    5. Returns result
    """
    if not request.image_url and not request.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either image_url or image_base64 must be provided",
        )

    # Create transaction record
    transaction = Transaction(
        original_request=request.edit_description,
        operation_type="edit",
        source_image_url=request.image_url,
        status=TransactionStatus.PENDING,
    )
    db.add(transaction)
    await db.flush()

    try:
        # Step 1: Generate edit prompt with ChatGPT
        transaction.status = TransactionStatus.PROCESSING
        await db.flush()

        chatgpt_service = ChatGPTService()

        if request.original_prompt:
            generated_prompt = await chatgpt_service.generate_edit_prompt(
                request.original_prompt, request.edit_description
            )
        else:
            generated_prompt = await chatgpt_service.generate_prompt(
                f"Edit an image: {request.edit_description}"
            )

        transaction.generated_prompt = generated_prompt
        await db.flush()

        # Step 2: Edit image with Nanobanano
        nanobanano_service = NanobananoService()
        result = await nanobanano_service.edit_image(
            image_url=request.image_url,
            image_base64=request.image_base64,
            prompt=generated_prompt,
            width=request.width,
            height=request.height,
            strength=request.strength,
        )

        # Extract image URL from result
        image_url = None
        if "images" in result and result["images"]:
            first_image = result["images"][0]
            image_url = first_image.get("url") or first_image.get("data") or first_image.get("content")
        elif "url" in result:
            image_url = result["url"]
        elif "image_url" in result:
            image_url = result["image_url"]

        # Update transaction with success
        transaction.status = TransactionStatus.SUCCESS
        transaction.result_image_url = image_url
        if "task_id" in result:
            transaction.task_id = result["task_id"]

        await db.commit()

        return GenerateResponse(
            success=True,
            transaction_id=transaction.id,
            message="Image edited successfully",
            original_request=request.edit_description,
            generated_prompt=generated_prompt,
            image_url=image_url,
            status=TransactionStatus.SUCCESS.value,
        )

    except NanobananoError as e:
        transaction.status = TransactionStatus.ERROR
        transaction.error_message = e.message
        await db.commit()

        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message,
        )

    except Exception as e:
        transaction.status = TransactionStatus.ERROR
        transaction.error_message = str(e)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Edit failed: {str(e)}",
        )


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get transaction history",
    description="Retrieve history of all image generation/edit transactions.",
)
async def get_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(
        default=None,
        description="Filter by status (pending, processing, success, error)"
    ),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_token),
):
    """Get paginated transaction history"""

    # Build query
    query = select(Transaction).order_by(desc(Transaction.created_at))

    if status_filter:
        try:
            status_enum = TransactionStatus(status_filter)
            query = query.where(Transaction.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}",
            )

    # Count total
    count_query = select(Transaction)
    if status_filter:
        count_query = count_query.where(Transaction.status == TransactionStatus(status_filter))

    result = await db.execute(count_query)
    total = len(result.scalars().all())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return HistoryResponse(
        total=total,
        page=page,
        per_page=per_page,
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
    )


@router.get(
    "/transaction/{transaction_id}",
    response_model=TransactionResponse,
    responses={
        404: {"model": ErrorResponse},
    },
    summary="Get transaction by ID",
    description="Retrieve details of a specific transaction.",
)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_token),
):
    """Get a specific transaction by ID"""

    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    return TransactionResponse.model_validate(transaction)


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is running.",
)
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "AI Image Hub"}
