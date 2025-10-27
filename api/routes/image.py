from fastapi import APIRouter, Query, HTTPException, Path
from typing import Optional, List
from services.aws_service import AWSService

router = APIRouter(tags=["Images"])

aws_service = AWSService()

@router.get(
    "/images",
    summary="List all uploaded images with optional filters",
    description="""
    Retrieve a list of all uploaded images and their metadata stored in DynamoDB.
    Supports filtering by **user_id** and **tag** to refine search results.

    - **user_id**: Filter images uploaded by a specific user  
    - **tag**: Filter images containing a specific tag
    """,
    responses={
        200: {
            "description": "Images fetched successfully",
            "content": {
                "application/json": {
                    "example": {
                        "images": [
                            {
                                "image_id": "abc123",
                                "user_id": "user_001",
                                "s3_url": "https://bucket.s3.amazonaws.com/user_001/abc123.jpg",
                                "tags": ["travel", "sunset"],
                                "uploaded_at": "2025-10-22T09:00:00Z"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid filter values"},
        500: {"description": "Internal server error"}
    }
)
async def list_images(
    user_id: Optional[str] = Query(None, description="Filter images by user ID"),
    tag: Optional[str] = Query(None, description="Filter images by tag keyword")
):

    try:
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if tag:
            filters["tag"] = tag

        images = aws_service.query_images(filters)
        return {"images": images}

    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch images: {str(e)}"
        )


@router.get(
    "/images/{image_id}",
    summary="View or download an image",
    description="""
    Retrieve a single image and its metadata.  
    Returns a **presigned S3 URL** that allows temporary access to the image for viewing or downloading.
    """,
    responses={
        200: {
            "description": "Presigned URL generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "image_id": "abc123",
                        "user_id": "user_001",
                        "download_url": "https://s3.amazonaws.com/bucket/abc123.jpg?AWSAccessKeyId=...",
                        "expires_in": 3600
                    }
                }
            }
        },
        404: {"description": "Image not found"},
        500: {"description": "Failed to generate download URL"}
    }
)
async def get_image(
    image_id: str = Path(..., description="Unique ID of the image to view or download")
):

    try:

        metadata = aws_service.get_image_metadata(image_id)
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail="Image not found"
            )

        presigned_url = aws_service.generate_presigned_url(metadata["s3_key"])

        return {
            "image_id": image_id,
            "user_id": metadata.get("user_id"),
            "download_url": presigned_url,
            "expires_in": 3600
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching image: {str(e)}"
        )


@router.delete(
    "/images/{image_id}",
    summary="Delete an image",
    description="""
    Permanently delete an image and its metadata from the system.  
    This removes the image file from **S3** and the metadata record from **DynamoDB**.
    """,
    responses={
        200: {
            "description": "Image deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Image deleted successfully", "image_id": "abc123"}
                }
            },
        },
        404: {"description": "Image not found"},
        500: {"description": "Failed to delete image"},
    },
)
async def delete_image(
    image_id: str = Path(..., description="Unique ID of the image to delete")
):

    try:
        metadata = aws_service.get_image_metadata(image_id)
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail="Image not found"
            )

        s3_key = metadata.get("s3_key")
        if not s3_key:
            raise HTTPException(
                status_code=400,
                detail="S3 key not found in metadata"
            )

        aws_service.delete_image_from_s3(s3_key)
        aws_service.delete_metadata_from_dynamo(image_id)

        return {"message": "Image deleted successfully", "image_id": image_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete image: {str(e)}"
        )