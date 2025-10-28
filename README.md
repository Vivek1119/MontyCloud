# MontyCloud

# FastAPI Instagram-like Image Upload Service

This project implements an **image upload and management service** similar to Instagram, built with **FastAPI**, **AWS S3**, and **DynamoDB** — all simulated locally using **LocalStack** for development and testing.

---

## Features

- Upload images to **S3** with metadata in **DynamoDB**
- List images with optional filters (`user_id`, `tag`)
- Retrieve single image via **presigned S3 URL**
- Delete image (from both **S3** and **DynamoDB**)
- Full **serverless simulation** locally
- Containerized with **Docker Compose**

---

## Tech Stack

| Component | Technology |
|------------|-------------|
| Backend Framework | FastAPI (Python 3.11) |
| Cloud Services | AWS S3, DynamoDB (via LocalStack) |
| Containerization | Docker + Docker Compose |
| AWS SDK | boto3 |
| Testing Framework | unittest |

---

> Inside Docker, the app connects to LocalStack via `http://localstack:4566` — **not** `localhost`.

---

## Running the App (Local Development)

### Build and start the containers

```bash

docker compose down -v
docker compose up --build -d

```
