from pydantic import BaseModel


class HttpErrorResponse(BaseModel):
    errorMessage: str
    errorCode: str
    timestamp: str
