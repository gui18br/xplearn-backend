from typing import List
from pydantic import BaseModel

class ProfessorBase(BaseModel):
    matricula: str
    nome: str
    senha: str
    icone: str | None = None
    avatar_id_fk: int
    
class ProfessorCreate(ProfessorBase):
    pass

class ProfessorResponse(BaseModel):
    matricula: str
    nome: str
    icone: str | None = None
    avatar_id_fk: int
        
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
    
    
