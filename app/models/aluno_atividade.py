from app.database import Base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Date, ForeignKey, Integer, String

class AlunoAtividade(Base):
    __tablename__ = "Aluno_Atividade"

    aluno_matricula_fk = Column("aluno_matricula_fk", String, ForeignKey("Aluno.matricula"), primary_key=True)
    atividade_id_fk = Column("atividade_id_fk", Integer, ForeignKey("Atividade.id"), primary_key=True)
    nota = Column("nota", String, nullable=False)

    aluno = relationship("Aluno", back_populates="atividades_associadas")
    atividade = relationship("Atividade", back_populates="alunos_associados")