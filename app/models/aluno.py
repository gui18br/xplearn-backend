from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from .aluno_turma import aluno_turma

class Aluno(Base):
    __tablename__ = "Aluno"
    
    matricula = Column(String, primary_key=True, index=True)
    nickname = Column(String, unique=True, nullable=True)
    nome = Column(String, nullable=False)
    senha = Column(String, nullable=True)
    xp = Column(Integer, nullable=True)
    nivel = Column(Integer, nullable=True)
    
    avatar_id_fk = Column(Integer, ForeignKey("Avatar.id"), nullable=True)
    avatar = relationship("Avatar", backref="Aluno")
    
    turmas = relationship("Turma", secondary=aluno_turma, back_populates="alunos")
    
    badges_associados = relationship("AlunoBadge", back_populates="aluno")
    atividades_associadas = relationship("AlunoAtividade", back_populates="aluno")
    badges_associados = relationship("AlunoBadge", back_populates="aluno")
