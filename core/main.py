from fastapi import FastAPI, Query, status, HTTPException,Path,Form,Body,File,UploadFile,Depends
from typing import List, Optional
from .schemas import (
    CostResponseSchema, CostSchema, CreateCostSchema, UpdateCostSchema,
    UserSchema, CreateUserSchema, UserResponseSchema
)

from .database import get_db, SessionLocal, Base, engine
from sqlalchemy.orm import Session

from .models import UserModel,CostModel

app = FastAPI()

@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "Hello World!"}

@app.post("/costs", response_model=CostResponseSchema, status_code=status.HTTP_201_CREATED)
def create_cost(cost: CreateCostSchema, user_id: int = Query(1, description="User ID to assign the cost to"), db: Session = Depends(get_db)):
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
def create_cost_for_user(user_id: int, cost: CreateCostSchema, db: Session = Depends(get_db)):
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

@app.get("/costs/{cost_id}", response_model=CostResponseSchema, status_code=status.HTTP_200_OK)
def read_cost(cost_id: int, db: Session = Depends(get_db)):
    cost = db.query(CostModel).filter(CostModel.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost with id {cost_id} not found")
    return cost
    
@app.get("/costs",response_model=List[CostResponseSchema] ,status_code=status.HTTP_200_OK)
def read_costs(db: Session = Depends(get_db)):
    costs = db.query(CostModel).all()
    return costs  

@app.put("/costs/{cost_id}", response_model=CostResponseSchema, status_code=status.HTTP_200_OK)
def update_cost(cost_id: int, updated_cost: UpdateCostSchema, db: Session = Depends(get_db)):
    cost = db.query(CostModel).filter(CostModel.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost with id {cost_id} not found")
    
    # Update only the fields that are provided
    if updated_cost.description is not None:
        cost.description = updated_cost.description
    if updated_cost.amount is not None:
        cost.amount = updated_cost.amount
    
    db.commit()
    db.refresh(cost)
    return cost

@app.delete("/costs/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cost(cost_id: int, db: Session = Depends(get_db)):
    cost = db.query(CostModel).filter(CostModel.id == cost_id).first()
    if not cost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost with id {cost_id} not found"
        )
    
    db.delete(cost)
    db.commit()
    return  # 204 No Content shouldn't return data


# User endpoints
@app.post("/users", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: CreateUserSchema, db: Session = Depends(get_db)):
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
    return db_user

@app.get("/users", response_model=List[UserResponseSchema], status_code=status.HTTP_200_OK)
def read_users(db: Session = Depends(get_db)):
    users = db.query(UserModel).all()
    return users

@app.get("/users/{user_id}", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")
    return user

@app.get("/users/{user_id}/costs", response_model=List[CostResponseSchema], status_code=status.HTTP_200_OK)
def read_user_costs(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")
    
    costs = db.query(CostModel).filter(CostModel.user_id == user_id).all()
    return costs