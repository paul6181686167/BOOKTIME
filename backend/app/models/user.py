from pydantic import BaseModel

class UserAuth(BaseModel):
    first_name: str
    last_name: str