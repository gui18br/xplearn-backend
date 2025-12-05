from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from .avatar import AvatarResponse
from .badge import BadgeResponse

class AlunoBase(BaseModel):
    matricula: str
    nome: str
    nickname: str
    senha: str
    xp: int
    nivel: int
    icone: str | None = None
    avatar_id_fk: int
    
class AlunoCreate(AlunoBase):
    pass

class AlunoResponse(BaseModel):
    matricula: str
    nome: str
    nickname: str
    xp: int
    nivel: int
    icone: Optional[str] = None
    avatar: Optional[AvatarResponse] = None
    badges: List[BadgeResponse] = Field(default=[], validation_alias="badges_associados")

    @field_validator('badges', mode='before')
    def parse_badges(cls, v):
        if not v:
            return []
        
        # Se 'v' for uma lista, verifica se os itens são objetos da tabela associativa (AlunoBadge)
        # O modelo AlunoBadge tem um atributo '.badge', que é o que queremos retornar
        cleaned_badges = []
        for item in v:
            if hasattr(item, 'badge'):
                cleaned_badges.append(item.badge)
            else:
                # Caso já venha formatado ou seja outro tipo
                cleaned_badges.append(item)
                
        return cleaned_badges
class AlunoResponseList(BaseModel):
    data: List[AlunoResponse]
        
    class Config:
        from_attributes = True
        
class AlunoResponseSingle(BaseModel):
    data: AlunoResponse
    
    class Config:
        from_attributes = True        

class AlunoResponseCreate(BaseModel):
    data: dict
  
