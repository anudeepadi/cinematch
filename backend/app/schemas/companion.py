from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime


class CompanionLinkRequest(BaseModel):
    """Request to link a companion account"""
    email: EmailStr = Field(..., description="Email of the user to link with")
    nickname: Optional[str] = Field(None, max_length=100, description="Nickname for this companion")


class CompanionLinkResponse(BaseModel):
    """Response after sending a companion link request"""
    id: int
    status: Literal['pending', 'accepted', 'rejected']
    companion_email: str
    nickname: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanionResponse(BaseModel):
    """Response for a linked companion"""
    id: int
    user_id: int
    companion_id: int
    nickname: Optional[str] = None
    status: str
    companion_username: str
    companion_avatar: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanionPreferencesResponse(BaseModel):
    """Companion's preferences for joint recommendations"""
    companion_id: int
    username: str
    preferred_genres: List[int] = []
    year_range_min: int = 1970
    year_range_max: int = 2025
    mood_action: int = 3
    mood_comedy: int = 3
    mood_drama: int = 3
    mood_horror: int = 3
    mood_romance: int = 3
    mood_scifi: int = 3
    mood_thriller: int = 3
    mood_documentary: int = 3


class CompanionRequestResponse(BaseModel):
    """Pending companion request details"""
    id: int
    from_user_id: int
    from_username: str
    from_avatar: Optional[str] = None
    nickname: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanionRequestAction(BaseModel):
    """Action on a companion request"""
    action: Literal['accept', 'reject']


class CompanionListResponse(BaseModel):
    """List of all companions"""
    companions: List[CompanionResponse]
    pending_requests: List[CompanionRequestResponse]
    sent_requests: List[CompanionLinkResponse]
