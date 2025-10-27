from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from services.aws_service import AWSService
from utils.common import current_timestamp

router = APIRouter(tags=["Upload"])

aws_service = AWSService()


@router.post(
    "/upload",
    summary="Upload an image with metadata",
    description="""
        This endpoint allows users to upload an image along with optional metadata such as description and tags.  
        The image is stored in **AWS S3**, and metadata is persisted in **DynamoDB**.  
    
        **Workflow:**
        1. The image is uploaded to S3.
        2. A public image URL is generated.
        3. Metadata (user_id, description, tags, uploaded_at, etc.) is stored in DynamoDB.
        4. A success response is returned with image details.
        """,
    responses={
        201: {
            "description": "Image uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Image uploaded successfully",
                        "image_id": "a37c3b58-8a11-47a4-a098-c5f0918b42b7",
                        "image_url": "https://my-instagram-images.s3.ap-south-1.amazonaws.com/uploads/12345/a37c3b58-8a11-47a4-a098-c5f0918b42b7.jpg",
                        "metadata": {
                            "image_id": "a37c3b58-8a11-47a4-a098-c5f0918b42b7",
                            "user_id": "12345",
                            "description": "Sunset view",
                            "tags": ["travel", "nature", "evening"],
                            "image_url": "https://my-instagram-images.s3.ap-south-1.amazonaws.com/uploads/12345/a37c3b58-8a11-47a4-a098-c5f0918b42b7.jpg",
                            "uploaded_at": "2025-10-22T09:32:11.123456"
                        }
                    }
                }
            },
        },
        400: {"description": "Bad Request — Invalid input data"},
        500: {"description": "Internal Server Error — Upload or DB operation failed"},
    },
)
async def upload_image(
    user_id: str = Form(..., description="Unique ID of the user uploading the image"),
    description: str = Form(None, description="Optional description of the image"),
    tags: str = Form(None, description="Comma-separated list of tags for the image"),
    image: UploadFile = File(..., description="Image file to upload (JPEG, PNG, etc.)"),
):
    """
    Upload image and persist metadata.
    """

    try:
        # Generate S3 key and unique image_id
        s3_key, image_id = aws_service.generate_image_key(user_id, image.filename)

        # Upload image to S3
        aws_service.upload_image_to_s3(
            file_obj=image.file,
            key=s3_key,
            content_type=image.content_type
        )

        # Generate image URL
        image_url = aws_service.get_image_url(s3_key)

        # Prepare metadata
        metadata = {
            "image_id": image_id,
            "user_id": user_id,
            "description": description or "",
            "tags": tags.split(",") if tags else [],
            "image_url": image_url,
            "uploaded_at": current_timestamp(),
        }

        # Save metadata in DynamoDB
        aws_service.save_image_metadata(metadata)

        return JSONResponse(
            content={
                "message": "Image uploaded successfully",
                "image_id": image_id,
                "image_url": image_url,
                "metadata": metadata,
            },
            status_code=201,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
