from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="健康状态")
    version: str = Field(..., description="版本号")
    config_valid: bool = Field(..., description="配置是否有效")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "config_valid": True
            }
        }
