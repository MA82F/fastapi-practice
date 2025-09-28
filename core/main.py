from fastapi import FastAPI, HTTPException, status, Body
from typing import List, Optional
from schemas import CostResponseSchema,CostSchema,CreateCostSchema,UpdateCostSchema

app = FastAPI()

costs = [
    {"id": 1, "description": "First bought", "amount": 10.0},
]



@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "Hello World!"}
@app.post("/costs/", response_model=CostResponseSchema, status_code=status.HTTP_201_CREATED)
def create_cost(cost: CreateCostSchema):
    if costs:
        last_id = costs[-1]["id"]
        next_id = last_id + 1
    else:
        next_id = 1
    
    new_cost = {
        "id": next_id,
        "description": cost["description"],
        "amount": float(cost["amount"])
    }
    costs.append(new_cost)
    return new_cost

@app.get("/costs/{cost_id}", response_model=List[CostResponseSchema], status_code=status.HTTP_200_OK)
def read_cost(cost_id: int):
    for cost in costs:
        if cost["id"] == cost_id:
            return cost
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost with id {cost_id} not found")
    
@app.get("/costs/",response_model=List[CostResponseSchema] ,status_code=status.HTTP_200_OK)
def read_cost():
    return costs  

@app.put("/costs/{cost_id}", response_model=CostResponseSchema, status_code=status.HTTP_200_OK)
def update_cost(cost_id: int, updated_cost: UpdateCostSchema):
    for item in costs:
        if item["id"] == cost_id:
            item["description"] = updated_cost.description
            item["amount"] = updated_cost.amount
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cost with id {cost_id} not found")

@app.delete("/costs/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cost(cost_id: int):
    for item in costs:
        if item["id"] == cost_id:
            costs.remove(item)
            return  # 204 No Content shouldn't return data
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Cost with id {cost_id} not found"
    )