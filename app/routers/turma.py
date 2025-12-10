from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import database
from app.schemas import turma as schemas
from app.models import turma as models
from app.models.aluno import Aluno
from app.models.turma import Turma
from app.models.professor import Professor

router = APIRouter(prefix="/turmas", tags=["Turmas"])

@router.post("/", response_model=schemas.TurmaResponseSingle)
def create_turma(turma: schemas.TurmaCreate, db: Session = Depends(database.get_db),):

    try:
        prof = None
        if turma.professor_matricula_fk:
            prof = db.query(Professor).filter(Professor.matricula == turma.professor_matricula_fk).first()
            if not prof:
                raise HTTPException(status_code=404, detail="Professor não encontrado")
        
        prof_matricula = prof.matricula if prof else None

        new_turma = Turma(
            nome=turma.nome,
            professor_matricula_fk=prof_matricula
        )
        
        db.add(new_turma)
        db.commit()
        db.refresh(new_turma)
        
        return {"data": new_turma}
    
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao criar turma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados: Não foi possível criar a turma. Detalhe: {e}"
        )
    except Exception as e:
        db.rollback() 
        print(f"Erro inesperado ao criar turma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao criar turma."
        )

@router.get("/", response_model=schemas.TurmaResponseList)
def get_turmas(db: Session = Depends(database.get_db)):
    try:
        turmas = db.query(Turma).all()
        return {"data":turmas}
    except SQLAlchemyError as e:
        print(f"Erro no banco de dados ao listar turmas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no banco de dados ao buscar lista de turmas."
        )
    except Exception as e:
        print(f"Erro inesperado ao listar turmas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar turmas."
        )

@router.get("/{id}", response_model=schemas.TurmaResponseSingle)
def get_turma_by_id(id: int, db: Session = Depends(database.get_db)):
    try:
        turma = db.query(Turma).filter(Turma.id == id).first()
        
        if not turma:
            raise HTTPException(status_code=404, detail="Turma não encontrada")
        
        return {"data":turma}
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        print(f"Erro no banco de dados ao buscar turma por ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no banco de dados ao buscar turma."
        )
    except Exception as e:
        print(f"Erro inesperado ao buscar turma por ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar turma."
        )

@router.post("/{turma_id}/alunos/{matricula}")
def add_aluno_turma(matricula: str, turma_id: int, db: Session = Depends(database.get_db)):
    
    try:
        aluno = db.get(Aluno, matricula)
        turma = db.get(Turma, turma_id)
        
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        if not turma:
            raise HTTPException(status_code=404, detail="Turma não encontrada")

        if turma in aluno.turmas:
            raise HTTPException(status_code=400, detail="Aluno já está matriculado nessa turma")

        aluno.turmas.append(turma)
        db.commit()
        return {"msg": f"Aluno {aluno.nome} adicionado à turma {turma.nome}"}
    
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao adicionar aluno à turma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados: Não foi possível adicionar o aluno à turma. Detalhe: {e}"
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao adicionar aluno à turma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao adicionar aluno à turma."
        )

@router.get("/alunos/{matricula}")
def listar_turmas_aluno(matricula: str, db: Session = Depends(database.get_db)):
    try:
        aluno = db.get(Aluno, matricula)
        
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        return {"data": aluno.turmas}
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        print(f"Erro no banco de dados ao listar turmas do aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no banco de dados ao buscar turmas do aluno."
        )
    except Exception as e:
        print(f"Erro inesperado ao listar turmas do aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar turmas do aluno."
        )
    
@router.delete("/{turma_id}/alunos/{matricula}")
def remove_aluno_turma(matricula: str, turma_id: int, db: Session = Depends(database.get_db)):
    try:
        aluno = db.get(Aluno, matricula)
        turma = db.get(Turma, turma_id)
        
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        if not turma:
            raise HTTPException(status_code=404, detail="Turma não encontrada")

        if turma not in aluno.turmas:
            raise HTTPException(status_code=400, detail="Aluno não pertence a esta turma")

        aluno.turmas.remove(turma) # Remove a relação
        db.commit()
        return {"msg": f"Aluno {aluno.nome} removido da turma {turma.nome}"}
    
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro ao remover aluno: {e}")
        raise HTTPException(status_code=500, detail="Erro no banco de dados.")
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor.")