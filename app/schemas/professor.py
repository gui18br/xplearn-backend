from typing import List, Optional
from pydantic import BaseModel
from .avatar import AvatarResponse

class ProfessorBase(BaseModel):
    matricula: str
    nome: str
    senha: str
    icone: str | None = None
    avatar_id_fk: int
    
class ProfessorCreate(ProfessorBase):
    pass

class ProfessorUpdate(BaseModel):
    nome: Optional[str] = None
    avatar_id_fk: Optional[int] = None
    senha_atual: Optional[str] = None
    nova_senha: Optional[str] = None

class ProfessorResponse(BaseModel):
    matricula: str
    nome: str
    icone: str | None = None
    avatar_id_fk: int
    avatar: Optional[AvatarResponse] = None
    
    class Config:
        from_attributes = True
        
class ProfessorResponseList(BaseModel):
    data: List[ProfessorResponse]
    class Config:
        from_attributes = True
        
class ProfessorResponseSingle(BaseModel):
    data: ProfessorResponse
    class Config:
        from_attributes = True  

class ProfessorResponseCreate(BaseModel):
    data: dict
    
    
