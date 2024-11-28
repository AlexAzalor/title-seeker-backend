# from typing import Annotated

# from botocore.exceptions import ClientError
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from mypy_boto3_sns import SNSClient
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.orm import Session
# import sqlalchemy as sa
# from google.oauth2 import id_token
# from google.auth.transport import requests


# import app.models as m
# from api.dependency import get_db
# from api.controllers.oauth2 import create_access_token
# from app import schema as s
# from app.logger import log
# from config import config

# ISSUER_WHITELIST = ["accounts.google.com", "https://accounts.google.com"]

# router = APIRouter(prefix="/auth", tags=["Auth"])

# CFG = config()


# @router.post("/login", status_code=status.HTTP_200_OK, response_model=s.Token, include_in_schema=False)
# def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db=Depends(get_db)):
#     """Logs in a user"""
#     user = m.User.authenticate(form_data.username, form_data.password, session=db)
#     if not user:
#         log(log.ERROR, "User [%s] wrong username or password", form_data.username)
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
#     log(log.INFO, "User [%s] logged in", user.first_name)
#     return s.Token(access_token=create_access_token(user.id))
