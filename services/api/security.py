import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED

_security = HTTPBasic()


def require_basic_auth(credentials: HTTPBasicCredentials = Depends(_security)) -> None:
    user = os.getenv("API_BASIC_USER", "admin")
    password = os.getenv("API_BASIC_PASS", "admin")
    if not (credentials and credentials.username == user and credentials.password == password):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
