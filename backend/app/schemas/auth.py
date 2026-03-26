import uuid

from pydantic import BaseModel, EmailStr


class GoogleAuthRequest(BaseModel):
    """Google OAuth 인증 요청 — authorization code를 서버로 전달한다."""

    authorization_code: str


class TokenResponse(BaseModel):
    """JWT 토큰 응답 — 로그인/회원가입 성공 시 반환한다."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마."""

    id: uuid.UUID
    email: EmailStr
    name: str

    model_config = {"from_attributes": True}
