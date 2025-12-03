from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.badge import BadgeResponse

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
    badge: BadgeResponse

class AtividadeResponse(BaseModel):
    data: List[AtividadeRead]
    class Config:
        from_attributes = True
        
class AtividadeResponseSingle(BaseModel):
    data: AtividadeRead     
    class Config:
        from_attributes = True