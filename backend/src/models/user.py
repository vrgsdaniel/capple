from pydantic import BaseModel


class CurrentUser(BaseModel):
    """Internal representation of the authenticated caller.

    Decouples controllers from the auth User type — only the
    fields the application actually uses are surfaced here.
    """

    id: str
