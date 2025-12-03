from sqlalchemy import Column, DateTime, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Atividade(Base):
    __tablename__ = "Atividade"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    nota_max = Column(Numeric(10, 2), nullable=True)
    pontos = Column(Integer, nullable=True)
    data_entrega = Column(DateTime, nullable=False)
    
    badge_id_fk = Column(Integer, ForeignKey("Badge.id"), nullable=False)
    turma_id_fk = Column(Integer, ForeignKey("Turma.id"), nullable=True)

    badge = relationship("Badge", backref="Atividade")
    turma = relationship("Turma", backref="Atividade")
    alunos_associados = relationship(
        "AlunoAtividade",
        back_populates="atividade",
        cascade="all, delete-orphan"
    )