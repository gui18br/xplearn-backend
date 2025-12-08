from sqlalchemy import Column, String, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base

class AlunoBadge(Base):
    __tablename__ = "Aluno_Badge"

    aluno_matricula_fk = Column(String, ForeignKey("Aluno.matricula"), primary_key=True)
    badge_id_fk = Column(Integer, ForeignKey("Badge.id"), primary_key=True)
    data_conquista = Column(Date, nullable=False)

    aluno = relationship("Aluno", back_populates="badges_associados")
    badge = relationship("Badge", back_populates="alunos_associados")
