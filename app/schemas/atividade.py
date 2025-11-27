from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel

class AtividadeBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    nota_max: Decimal
    pontos: int
    badge_id_fk: int
    turma_id_fk: int
    data_entrega: datetime
    
class AtividadeCreate(AtividadeBase):
    pass

class AtividadeUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    nota_max: Optional[Decimal] = None
    pontos: Optional[int] = None
    badge_id_fk: Optional[int] = None
    turma_id_fk: Optional[int] = None
    data_entrega: Optional[datetime] = None

class AtividadeRead(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    nota_max: Decimal
    pontos: int
    badge_id_fk: int
    turma_id_fk: int
    data_entrega: datetime       
     
    class Config:
        from_attributes = True

class AtividadeResponse(BaseModel):
    data: List[AtividadeRead]
        
    class Config:
        from_attributes = True
        
class AtividadeResponseSingle(BaseModel):
    data: AtividadeRead     
     
    class Config:
        from_attributes = True