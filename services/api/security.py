import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED

_security = HTTPBasic()
_USER = os.getenv("API_BASIC_USER", "admin")
_PASS = os.getenv("API_BASIC_PASS", "admin")

def require_basic_auth(credentials: HTTPBasicCredentials = Depends(_security)) -> None:
    if not (credentials and credentials.username == _USER and credentials.password == _PASS):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
