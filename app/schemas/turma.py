from pydantic import BaseModel, field_validator
from typing import List, Optional

class TurmaBase(BaseModel):
    nome: str
    professor_matricula_fk: Optional[str] = None

class TurmaCreate(TurmaBase):
    pass

class TurmaResponse(BaseModel):
    id: int
    nome: str
    professor_matricula_fk: Optional[str] = None
    
    professor: Optional[str] = None  

    class Config:
        from_attributes = True

    @field_validator('professor', mode='before')
    def extract_professor_name(cls, v):
        if v and hasattr(v, 'nome'):
            return v.nome

class TurmaResponseList(BaseModel):
    data: List[TurmaResponse]

    class Config:
        from_attributes = True

class TurmaResponseSingle(BaseModel):
    data: TurmaResponse

    class Config:
        from_attributes = True
