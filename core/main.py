from fastapi import FastAPI, status, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from models import UserModel, CostModel
from schemas import (
    CostResponseSchema, CreateCostSchema, UpdateCostSchema,
    UserSchema, CreateUserSchema
)
from auth.jwt_cookie_auth import (
    generate_access_token, generate_refresh_token, get_authenticated_user,
    set_secure_cookies, clear_auth_cookies, validate_refresh_token_from_cookie
)

app = FastAPI()


@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "Hello World!"}

@app.post("/costs", response_model=CostResponseSchema, status_code=status.HTTP_201_CREATED)
def create_cost(cost: CreateCostSchema, current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """
    Create a cost for the authenticated user
    Uses secure cookie-based authentication
    """
    db_cost = CostModel(
        user_id=current_user.id,  # Use authenticated user's ID
        description=cost.description,
        amount=cost.amount
    )
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

@app.get("/costs/{cost_id}", response_model=CostResponseSchema, status_code=status.HTTP_200_OK)
def read_cost(cost_id: int, current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    cost = db.query(CostModel).filter(CostModel.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost with id {cost_id} not found")
    
    # Check if the cost belongs to the authenticated user
    if cost.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: This cost doesn't belong to you")
    
    return cost
    
@app.get("/costs",response_model=List[CostResponseSchema] ,status_code=status.HTTP_200_OK)
def read_costs(current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    # Return only costs that belong to the authenticated user
    costs = db.query(CostModel).filter(CostModel.user_id == current_user.id).all()
    return costs  

@app.put("/costs/{cost_id}", response_model=CostResponseSchema, status_code=status.HTTP_200_OK)
def update_cost(cost_id: int, updated_cost: UpdateCostSchema, current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    cost = db.query(CostModel).filter(CostModel.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost with id {cost_id} not found")
    
    # Check if the cost belongs to the authenticated user
    if cost.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: This cost doesn't belong to you")
    
    # Update only the fields that are provided
    if updated_cost.description is not None:
        cost.description = updated_cost.description
    if updated_cost.amount is not None:
        cost.amount = updated_cost.amount
    
    db.commit()
    db.refresh(cost)
    return cost

@app.delete("/costs/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cost(cost_id: int, current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    cost = db.query(CostModel).filter(CostModel.id == cost_id).first()
    if not cost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost with id {cost_id} not found"
        )
    
    # Check if the cost belongs to the authenticated user
    if cost.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: This cost doesn't belong to you")
    
    db.delete(cost)
    db.commit()
    return  # 204 No Content shouldn't return data


# User endpoints
@app.post("/signup", status_code=status.HTTP_201_CREATED)
def create_user(user: CreateUserSchema, response: Response, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(UserModel).filter(UserModel.user_name == user.user_name).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    db_user = UserModel(
        user_name=user.user_name,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Generate tokens
    access_token = generate_access_token(db_user.id)
    refresh_token = generate_refresh_token(db_user.id)
    
    # Set secure cookies
    set_secure_cookies(response, access_token, refresh_token)
    
    return {
        "detail": "signed up successfully",
        "user": {
            "id": db_user.id,
            "user_name": db_user.user_name
        }
    }

@app.post("/login", status_code=status.HTTP_200_OK)
def login_user(user: UserSchema, response: Response, db: Session = Depends(get_db)):
    # Check if user exists and password is correct
    db_user = db.query(UserModel).filter(UserModel.user_name == user.user_name).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # In a real application, you should hash passwords and compare hashed versions
    if db_user.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Generate tokens
    access_token = generate_access_token(db_user.id)
    refresh_token = generate_refresh_token(db_user.id)
    
    # Set secure cookies
    set_secure_cookies(response, access_token, refresh_token)
    
    return {
        "detail": "logged in successfully",
        "user": {
            "id": db_user.id,
            "user_name": db_user.user_name
        }
    }

@app.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(response: Response, current_user: UserModel = Depends(get_authenticated_user)):
    """
    Logout endpoint - Clear authentication cookies
    In a real application, you would also want to:
    1. Add the token to a blacklist/blocklist
    2. Store blacklisted tokens in Redis or database
    3. Check blacklist in get_authenticated_user function
    """
    # Clear authentication cookies
    clear_auth_cookies(response)
    
    return {"detail": "Successfully logged out"}

@app.post("/refresh-tokens", status_code=status.HTTP_200_OK)
def refresh_access_token(response: Response, user_id: int = Depends(validate_refresh_token_from_cookie)):
    """
    Refresh access token using refresh token from HTTP-only cookie
    """
    # Generate new access token and refresh token
    new_access_token = generate_access_token(user_id)
    new_refresh_token = generate_refresh_token(user_id)
    
    # Set new secure cookies
    set_secure_cookies(response, new_access_token, new_refresh_token)
    
    return {
        "detail": "Tokens refreshed successfully"
    }

@app.get("/auth/me", status_code=status.HTTP_200_OK)
def get_current_user(current_user: UserModel = Depends(get_authenticated_user)):
    """
    Get current authenticated user information
    This endpoint can be used to verify if the user is still authenticated
    """
    return {
        "id": current_user.id,
        "user_name": current_user.user_name
    }