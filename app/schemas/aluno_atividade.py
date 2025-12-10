from pydantic import BaseModel
from typing import Optional

class AlunoAtividadeBase(BaseModel):
    aluno_matricula_fk: str
    atividade_id_fk: int
    nota: str

class AlunoAtividadeCreate(BaseModel):
    nota: Optional[str] = "0"

class AlunoAtividadeResponse(BaseModel):
    aluno_matricula_fk: str
    atividade_id_fk: int
    nota: str
    
    class Config:
        from_attributes = True

class AlunoStatusAtividade(BaseModel):
    matricula: str
    nome: str
    nickname: Optional[str] = None
    fez_atividade: bool
    nota: Optional[str] = None
    avatar: Optional[dict] = None

class AlunosAtividadeResponse(BaseModel):
    atividade_id: int
    alunos: list[AlunoStatusAtividade]

