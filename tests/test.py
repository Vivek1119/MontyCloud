import io
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)


@patch("services.aws_service.AWSService.upload_image_to_s3")
@patch("services.aws_service.AWSService.save_image_metadata")
def test_upload_image(mock_save_metadata, mock_upload_image):
    mock_upload_image.return_value = "test_key"
    mock_save_metadata.return_value = True

    files = {"image": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")}
    data = {"user_id": "user_001", "tags": "travel,sunset"}

    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 201
    assert response.json()["message"] == "Image uploaded successfully"


@patch("services.aws_service.AWSService.get_image_metadata")
@patch("services.aws_service.AWSService.generate_presigned_url")
def test_get_image_success(mock_presigned_url, mock_metadata):
    mock_metadata.return_value = {
        "image_id": "abc123",
        "user_id": "user_001",
        "s3_key": "images/abc123.jpg"
    }
    mock_presigned_url.return_value = "https://s3.amazonaws.com/bucket/images/abc123.jpg?AWSAccessKeyId=..."

    response = client.get("/api/v1/images/abc123")

    assert response.status_code == 200
    data = response.json()
    assert data["image_id"] == "abc123"
    assert data["user_id"] == "user_001"
    assert "download_url" in data
    assert data["expires_in"] == 3600


@patch("services.aws_service.AWSService.get_image_metadata")
def test_get_image_not_found(mock_metadata):
    mock_metadata.return_value = None

    response = client.get("/api/v1/images/xyz999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


@patch("services.aws_service.AWSService.get_image_metadata")
def test_get_image_internal_error(mock_metadata):
    mock_metadata.side_effect = Exception("DB connection failed")

    response = client.get("/api/v1/images/error123")

    assert response.status_code == 500
    assert "Error fetching image" in response.json()["detail"]


@patch("services.aws_service.AWSService.query_images")
def test_list_all_images(mock_query):
    mock_query.return_value = [
        {
            "image_id": "abc123",
            "user_id": "user_001",
            "s3_url": "https://bucket.s3.amazonaws.com/user_001/abc123.jpg",
            "tags": ["travel", "sunset"],
            "uploaded_at": "2025-10-22T09:00:00Z"
        }
    ]

    response = client.get("/api/v1/images")
    assert response.status_code == 200

    data = response.json()
    assert "images" in data
    assert len(data["images"]) == 1
    assert data["images"][0]["user_id"] == "user_001"


@patch("services.aws_service.AWSService.query_images")
def test_list_images_filter_by_user(mock_query):
    mock_query.return_value = [
        {"image_id": "img456", "user_id": "user_002", "tags": ["food"], "uploaded_at": "2025-10-23T09:00:00Z"}
    ]

    response = client.get("/api/v1/images?user_id=user_002")

    assert response.status_code == 200
    data = response.json()
    assert len(data["images"]) == 1
    assert data["images"][0]["user_id"] == "user_002"


@patch("services.aws_service.AWSService.query_images")
def test_list_images_filter_by_tag(mock_query):
    mock_query.return_value = [
        {"image_id": "img789", "user_id": "user_003", "tags": ["nature"], "uploaded_at": "2025-10-24T09:00:00Z"}
    ]

    response = client.get("/api/v1/images?tag=nature")

    assert response.status_code == 200
    data = response.json()
    assert len(data["images"]) == 1
    assert "nature" in data["images"][0]["tags"]


@patch("services.aws_service.AWSService.query_images")
def test_list_images_invalid_filter(mock_query):
    mock_query.side_effect = ValueError("Invalid filter value")

    response = client.get("/api/v1/images?user_id=@@bad_id")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid filter value"


@patch("services.aws_service.AWSService.query_images")
def test_list_images_internal_error(mock_query):
    mock_query.side_effect = Exception("DynamoDB scan failed")

    response = client.get("/api/v1/images")

    assert response.status_code == 500
    assert "Failed to fetch images" in response.json()["detail"]


@patch("services.aws_service.AWSService.delete_metadata_from_dynamo")
@patch("services.aws_service.AWSService.delete_image_from_s3")
@patch("services.aws_service.AWSService.get_image_metadata")
def test_delete_image_success(mock_get_metadata, mock_delete_s3, mock_delete_dynamo):
    mock_get_metadata.return_value = {
        "image_id": "abc123",
        "user_id": "user_001",
        "s3_key": "images/abc123.jpg",
    }
    mock_delete_s3.return_value = None
    mock_delete_dynamo.return_value = None

    response = client.delete("/api/v1/images/abc123")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Image deleted successfully"
    assert data["image_id"] == "abc123"


@patch("services.aws_service.AWSService.get_image_metadata")
def test_delete_image_not_found(mock_get_metadata):
    mock_get_metadata.return_value = None

    response = client.delete("/api/v1/images/missing123")

    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


@patch("services.aws_service.AWSService.get_image_metadata")
def test_delete_image_missing_s3_key(mock_get_metadata):
    mock_get_metadata.return_value = {
        "image_id": "bad123",
        "user_id": "user_999",
        # intentionally missing s3_key
    }

    response = client.delete("/api/v1/images/bad123")

    assert response.status_code == 400
    assert response.json()["detail"] == "S3 key not found in metadata"


@patch("services.aws_service.AWSService.delete_image_from_s3")
@patch("services.aws_service.AWSService.get_image_metadata")
def test_delete_image_s3_failure(mock_get_metadata, mock_delete_s3):
    mock_get_metadata.return_value = {
        "image_id": "img_fail",
        "s3_key": "images/fail.jpg"
    }
    mock_delete_s3.side_effect = Exception("S3 service unavailable")

    response = client.delete("/api/v1/images/img_fail")

    assert response.status_code == 500
    assert "Failed to delete image" in response.json()["detail"]


@patch("services.aws_service.AWSService.get_image_metadata")
def test_delete_image_internal_error(mock_get_metadata):
    mock_get_metadata.side_effect = Exception("DynamoDB connection failed")

    response = client.delete("/api/v1/images/error123")

    assert response.status_code == 500
    assert "Failed to delete image" in response.json()["detail"]

