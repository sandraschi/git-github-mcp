"""
Authentication module for Git-Github MCP.
"""

import os
from secrets import compare_digest

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Simple Basic Auth for the Git-Github MCP Web Interface.
    """
    correct_username = os.getenv("GIT_GITHUB_WEB_USER", "sandra")
    correct_password = os.getenv("GIT_GITHUB_WEB_PASS", "vienna2026")

    is_username_correct = compare_digest(credentials.username, correct_username)
    is_password_correct = compare_digest(credentials.password, correct_password)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
