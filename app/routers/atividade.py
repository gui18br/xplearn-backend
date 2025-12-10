from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import database
from app.schemas import atividade as schemas
from app.models.atividade import Atividade
from app.models.badge import Badge
from app.models.turma import Turma
from app.models.aluno_atividade import AlunoAtividade


router  = APIRouter(prefix="/atividades", tags=["Atividades"])

@router.post("/", response_model=schemas.AtividadeResponseSingle)
def create_atv(
    atv: schemas.AtividadeCreate,
    db: Session = Depends(database.get_db)
    ):
    
    try:
        badge = None
        if atv.badge_id_fk:
            badge = db.query(Badge).filter(Badge.id == atv.badge_id_fk).first()
            if not badge:
                raise HTTPException(status_code=404, detail="Badge não encontrada")

        turma = None
        if atv.turma_id_fk:
            turma = db.query(Turma).filter(Turma.id == atv.turma_id_fk).first()
            if not turma:
                raise HTTPException(status_code=404, detail="Turma não encontrada")

        badge_id = badge.id if badge else None
        turma_id = turma.id if turma else None
    
        new_atv = Atividade(
            nome=atv.nome,
            descricao=atv.descricao,
            nota_max=atv.nota_max,
            pontos=atv.pontos,
            badge_id_fk=badge_id,
            turma_id_fk=turma_id,
            data_entrega=atv.data_entrega
        )
    
        db.add(new_atv)
        db.commit()
        db.refresh(new_atv)
    
        return {"data": new_atv}
    
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao criar atividade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados: Não foi possível criar a atividade. Detalhe: {e}"
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao criar atividade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao criar atividade."
        )
    
@router.get("/", response_model=schemas.AtividadeResponse)
def get_atvs(db: Session = Depends(database.get_db)):
    try:
        atvs = db.query(Atividade).all()
        return {"data": atvs}
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao listar atividades: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao buscar lista de atividades."
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao listar atividades: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao listar atividades."
        )

@router.get("/{id}", response_model=schemas.AtividadeResponseSingle)
def get_atv_by_id(id: int, db: Session = Depends(database.get_db)):
    try:
        atv = db.query(Atividade).filter(Atividade.id == id).first()
    
        if not atv:
            raise HTTPException(status_code=404, detail="Atividade não encontrada")
    
        return {"data": atv}
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao buscar atividade por ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao buscar atividade."
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao buscar atividade por ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao buscar atividade."
        )

@router.post("/alunos/{matricula}/atividades/{atv_id}")
def atribuir_nota_aluno(matricula: str, atv_id: int, nota: str, db: Session = Depends(database.get_db)):
    try:
        atv_com_nota = AlunoAtividade(
            aluno_matricula_fk=matricula,
            atividade_id_fk=atv_id,
            nota=nota
        )
    
        db.add(atv_com_nota)
        db.commit()
        return {"msg": f"Nota da atividade {atv_id} atribuída ao aluno {matricula}"}
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao atribuir nota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados: Não foi possível atribuir a nota. Detalhe: {e}"
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao atribuir nota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao atribuir nota."
        )
