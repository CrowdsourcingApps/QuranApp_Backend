from fastapi import APIRouter, UploadFile, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.controllers.dependencies import db_session_dependency, api_key_dependency
from src.services import data_upload as data_upload_service

data_upload_router = APIRouter(
    prefix="/data-upload",
    tags=["data-upload"],
    dependencies=[api_key_dependency]
)


@data_upload_router.post("/ayah-parts")
def upload_ayah_parts_data(
        data_file: UploadFile,
        db: Session = db_session_dependency
):
    if not data_file.filename.endswith(".json"):
        raise HTTPException(detail="Data file must have a .json extension", status_code=status.HTTP_400_BAD_REQUEST)

    service = data_upload_service.AyahPartsDataUploader(db=db)
    try:
        service.save_data_from_ayah_parts_file(data_file.file)
    except ValidationError as e:
        raise HTTPException(detail=e.errors(), status_code=status.HTTP_400_BAD_REQUEST)
    except data_upload_service.DataUploadException as e:
        raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    finally:
        data_file.file.close()


@data_upload_router.post("/page-images")
def upload_page_images_data(
        data_file: UploadFile,
        db: Session = db_session_dependency
):
    if not data_file.filename.endswith(".json"):
        raise HTTPException(
            detail="Data file must have a .json extension", status_code=status.HTTP_400_BAD_REQUEST
        )

    service = data_upload_service.PageImagesDataUploader(db=db)
    try:
        service.save_data_from_page_images_file(data_file.file)
    except ValidationError as e:
        raise HTTPException(detail=e.errors(), status_code=status.HTTP_400_BAD_REQUEST)
    except data_upload_service.DataUploadException as e:
        raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    finally:
        data_file.file.close()


@data_upload_router.post("/surahs-in-mushaf")
def upload_surahs_in_mushaf_data(
        data_file: UploadFile,
        db: Session = db_session_dependency
):
    if not data_file.filename.endswith(".json"):
        raise HTTPException(
            detail="Data file must have a .json extension", status_code=status.HTTP_400_BAD_REQUEST
        )

    service = data_upload_service.SurahsInMushafDataUploader(db=db)
    try:
        service.save_data_from_surahs_in_mushaf_file(data_file.file)
    except ValidationError as e:
        raise HTTPException(detail=e.errors(), status_code=status.HTTP_400_BAD_REQUEST)
    except data_upload_service.DataUploadException as e:
        raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    finally:
        data_file.file.close()
