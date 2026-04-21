import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
load_dotenv()

import boto3

IconsAPI = APIRouter()

# --- Config S3 ---
BUCKET_NAME = os.getenv("BUCKET_NAME")
AWS_ACCESS_KEY = os.getenv("S3_AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("S3_AWS_SECRET_KEY")

s3 = boto3.client(
    "s3",
    region_name="us-east-1",
    endpoint_url="https://objstorage.leapcell.io",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)


# --- Helpers ---
def list_all_objects(prefix: str):
    """Lista todos los objetos de un prefix (maneja paginación)"""
    objects = []
    continuation_token = None

    while True:
        kwargs = {
            "Bucket": BUCKET_NAME,
            "Prefix": prefix
        }

        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        response = s3.list_objects_v2(**kwargs)

        objects.extend(response.get("Contents", []))

        if response.get("IsTruncated"):
            continuation_token = response.get("NextContinuationToken")
        else:
            break

    return objects


# --- Endpoints ---

@IconsAPI.get("/packs_with_icons/")
async def list_packs_with_icons():
    try:
        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Delimiter="/"
        )

        packs_with_icons = {}

        for prefix in response.get("CommonPrefixes", []):
            pack = prefix["Prefix"].rstrip("/")

            # Ignorar canvas
            if pack == "canvas":
                continue

            objects = list_all_objects(prefix["Prefix"])

            icons = [
                obj["Key"].split("/")[-1]
                for obj in objects
                if not obj["Key"].endswith("/")
            ]

            packs_with_icons[pack] = icons

        return {"packs": packs_with_icons}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@IconsAPI.get("/pack/{pack_name}/{icon_name}")
async def get_icon_image(pack_name: str, icon_name: str):
    try:
        key = f"{pack_name}/{icon_name}"

        obj = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=key
        )

        return StreamingResponse(
            obj["Body"],
            media_type=obj.get("ContentType", "application/octet-stream"),
            headers={
                "Cache-Control": "public, max-age=3600, immutable"
            }
        )

    except s3.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Icono no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))