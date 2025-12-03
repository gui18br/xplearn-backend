from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class Badge(Base):
    __tablename__ = "Badge"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    requisito = Column(String, nullable=True)
    caminho_foto = Column(String, nullable=True)
    
    alunos_associados = relationship("AlunoBadge", back_populates="badge")
