from typing import Any

from pydantic import BaseModel, Field


class QAGenerateRequest(BaseModel):
    user_id: str = Field(..., description="User triggering generation")
    spec_id: str | None = Field(None, description="Optional specification ID")
    spec_data: dict[str, Any] = Field(..., description="Item specification payload")
    generation_method: str = Field("template", description="template | llm | hybrid")
    instruction: str | None = Field(None, description="Optional instruction override")
    prompt_text: str | None = Field(None, description="Optional prompt_text override")


class QAValidateRequest(BaseModel):
    user_id: str = Field(..., description="User triggering validation")
    item_id: str | None = Field(None, description="Existing item ID")
    item_data: dict[str, Any] | None = Field(None, description="Inline item payload")


class QAActivateRequest(BaseModel):
    user_id: str = Field(..., description="User triggering activation")
    item_id: str = Field(..., description="Item to activate")


class QARetireRequest(BaseModel):
    user_id: str = Field(..., description="User triggering retirement")
    item_id: str = Field(..., description="Item to retire")
    reason: str = Field("Retired by user", description="Retirement reason")
