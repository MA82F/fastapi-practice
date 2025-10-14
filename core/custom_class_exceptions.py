from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class CostNotFoundException(HTTPException):
    """Exception raised when a cost with a specific ID is not found"""
    def __init__(self, cost_id: int):
        super().__init__(
            status_code=404,
            detail=f"Cost with ID {cost_id} not found"
        )

async def cost_not_found_exception_handler(request: Request, exc: CostNotFoundException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )
