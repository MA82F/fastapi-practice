from pydantic import BaseModel,Field
from typing import Optional

class CostSchema(BaseModel):
    description: str = Field(..., min_length=1,max_length=200,description="The description of the cost item")
    amount: float = Field(..., gt=0, description="The amount of the cost item(most be over greater than zero)")

class CreateCostSchema(CostSchema):
    pass

class UpdateCostSchema(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=200, description="The description of the cost item")
    amount: Optional[float] = Field(None, gt=0, description="The amount of the cost item(most be over greater than zero)")

class CostResponseSchema(CostSchema):
    id: int = Field(..., description="The unique identifier of the cost item")
    
    class Config:
        from_attributes = True  # For Pydantic v2 (or use orm_mode = True for v1)


# User Schemas
class UserSchema(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=150, description="The username")
    password: str = Field(..., min_length=1, max_length=150, description="The user password")

class CreateUserSchema(UserSchema):
    pass

class UserResponseSchema(BaseModel):
    id: int = Field(..., description="The unique identifier of the user")
    user_name: str = Field(..., description="The username")
    
    class Config:
        from_attributes = True