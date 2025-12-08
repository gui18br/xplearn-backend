from sqlalchemy import String, Table, Column, Integer, ForeignKey
from app.database import Base

aluno_turma = Table(
    "Aluno_Turma",
    Base.metadata,
    Column("aluno_matricula_fk", String, ForeignKey("Aluno.matricula"), primary_key=True),
    Column("turma_id_fk", Integer, ForeignKey("Turma.id"), primary_key=True)
)
