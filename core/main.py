from fastapi import FastAPI, Query, status, HTTPException, Path, Form, Body, File, UploadFile, Depends, Response
from typing import List, Optional

from fastapi.responses import JSONResponse
from .schemas import (
    CostResponseSchema, CostSchema, CreateCostSchema, UpdateCostSchema,
    UserSchema, CreateUserSchema, UserResponseSchema, RefreshTokenSchema
)

from .database import get_db, SessionLocal, Base, engine
from sqlalchemy.orm import Session

from .models import UserModel,CostModel

from .auth.jwt_auth import generate_access_token,generate_refresh_token,get_authenticated_user,validate_refresh_token,validate_refresh_token_from_cookie

app = FastAPI()

def set_secure_cookies(response: Response, access_token: str, refresh_token: str):
    """Set secure HTTP-only cookies for tokens"""
    # Set access token cookie (5 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=60 * 5,  # 5 minutes
        httponly=True,  # Prevent XSS attacks
        secure=True,    # Only send over HTTPS in production
        samesite="lax"  # CSRF protection
    )
    
    # Set refresh token cookie (24 hours)
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=60 * 60 * 24,  # 24 hours
        httponly=True,  # Prevent XSS attacks
        secure=True,    # Only send over HTTPS in production
        samesite="lax"  # CSRF protection
    )

def clear_auth_cookies(response: Response):
    """Clear authentication cookies"""
    response.delete_cookie(key="access_token", httponly=True, secure=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, secure=True, samesite="lax")

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

@app.post("/costs-legacy", response_model=CostResponseSchema, status_code=status.HTTP_201_CREATED)
def create_cost_legacy(cost: CreateCostSchema, user_id: int = Query(1, description="User ID to assign the cost to"), db: Session = Depends(get_db)):
    """
    Legacy endpoint - Create cost with manual user_id (kept for backward compatibility)
    """
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    db_cost = CostModel(
        user_id=user_id,
        description=cost.description,
        amount=cost.amount
    )
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

@app.post("/users/{user_id}/costs", response_model=CostResponseSchema, status_code=status.HTTP_201_CREATED)
def create_cost_for_user(user_id: int, cost: CreateCostSchema, current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """
    Create cost for a specific user - Users can only create costs for themselves
    """
    # Users can only create costs for themselves
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You can only create costs for yourself")
    
    # Check if user exists (redundant since current_user is already authenticated, but kept for safety)
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    db_cost = CostModel(
        user_id=user_id,
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

@app.post("/refresh-token", status_code=status.HTTP_200_OK)
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

@app.post("/refresh-token-legacy", status_code=status.HTTP_200_OK)
def refresh_access_token_legacy(token_data: RefreshTokenSchema, db: Session = Depends(get_db)):
    """
    Legacy refresh access token using refresh token in request body
    This endpoint is kept for backward compatibility
    """
    # Validate refresh token and get user_id
    user_id = validate_refresh_token(token_data.refresh_token, db)
    
    # Generate new access token
    new_access_token = generate_access_token(user_id)
    
    return {
        "detail": "Access token refreshed successfully",
        "access_token": new_access_token
    }

@app.get("/users", response_model=List[UserResponseSchema], status_code=status.HTTP_200_OK)
def read_users(current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """
    Get all users - Admin endpoint (requires authentication)
    In a real application, you might want to add role-based access control here
    """
    users = db.query(UserModel).all()
    return users

@app.get("/users/{user_id}", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
def read_user(user_id: int, current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """
    Get user by ID - Users can only access their own profile or admin can access any
    """
    # Users can only access their own profile
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You can only access your own profile")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")
    return user

@app.get("/users/{user_id}/costs", response_model=List[CostResponseSchema], status_code=status.HTTP_200_OK)
def read_user_costs(user_id: int, current_user: UserModel = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """
    Get costs for a specific user - Users can only access their own costs
    """
    # Users can only access their own costs
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You can only access your own costs")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")
    
    costs = db.query(CostModel).filter(CostModel.user_id == user_id).all()
    return costs

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