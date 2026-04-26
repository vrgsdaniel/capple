from pydantic import BaseModel


class ReadinessResponse(BaseModel):
    serviceAvailable: bool
