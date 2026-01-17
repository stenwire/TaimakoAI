from typing import Optional
from pydantic import BaseModel, Field


# ===== Input Schemas =====

class GetContextInput(BaseModel):
    """Input schema for the get_context tool."""
    user_input: str = Field(
        ...,
        description="The user's question or query to search for in the knowledge base",
        min_length=1,
        max_length=1000
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "What are the features of Vendkit?"
            }
        }


class SayHelloInput(BaseModel):
    """Input schema for the say_hello tool."""
    name: Optional[str] = Field(
        None,
        description="Optional name of the person to greet",
        max_length=100
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John"
            }
        }


class SayGoodbyeInput(BaseModel):
    """Input schema for the say_goodbye tool (no parameters needed)."""
    pass


# ===== Output Schemas =====

class ContextOutput(BaseModel):
    """Output schema for the get_context tool."""
    context_text: str = Field(
        ...,
        description="The retrieved context from the knowledge base"
    )
    chunks_count: int = Field(
        ...,
        description="Number of context chunks retrieved"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "context_text": "Vendkit is a comprehensive utility vending platform...",
                "chunks_count": 3
            }
        }


class GreetingOutput(BaseModel):
    """Output schema for the say_hello tool."""
    message: str = Field(
        ...,
        description="The greeting message"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, John! How can I help you today?"
            }
        }


class FarewellOutput(BaseModel):
    """Output schema for the say_goodbye tool."""
    message: str = Field(
        ...,
        description="The farewell message"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Goodbye! Have a great day."
            }
        }
