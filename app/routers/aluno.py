from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import database
from app.schemas import aluno as schemas
from app.models.aluno import Aluno
from app.models.avatar import Avatar


from datetime import timedelta
from app.security import hash_password, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/alunos", tags=["Alunos"])

@router.post("/", response_model=schemas.AlunoResponseCreate)
def create_user(aluno: schemas.AlunoCreate, db: Session = Depends(database.get_db)):
    
    try:
        db_aluno = db.query(Aluno).filter(Aluno.matricula == aluno.matricula).first()
        if db_aluno:
            raise HTTPException(status_code=400, detail="Matricula já registrada")
        
        avatar = None
        if aluno.avatar_id_fk:
            avatar = db.query(Avatar).filter(Avatar.id == aluno.avatar_id_fk).first()
            if not avatar:
                raise HTTPException(status_code=404, detail="Avatar não encontrado")
            
        existing_user = db.query(Aluno).filter(Aluno.nickname == aluno.nickname).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Nickname já está em uso")

        hashed_pwd = hash_password(aluno.senha)
        
        new_aluno = Aluno(
            matricula=aluno.matricula,
            senha=hashed_pwd,
            nickname=aluno.nickname,
            nome=aluno.nome,
            xp=aluno.xp,
            nivel=aluno.nivel,
            avatar_id_fk=aluno.avatar_id_fk
        )
        
        db.add(new_aluno)
        db.commit()
        db.refresh(new_aluno)
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(new_aluno.matricula)}, 
            expires_delta=access_token_expires
        )

        return {
            "data": {
                "matricula": aluno.matricula, "access_token": access_token
            }
        }

    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao criar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados: Não foi possível criar o aluno. Detalhe: {e}"
        )
    except Exception as e:
        db.rollback() 
        print(f"Erro inesperado ao criar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao criar aluno."
        )
    
@router.get("/", response_model=schemas.AlunoResponseList)
def get_alunos(db: Session = Depends(database.get_db)):
    try:
        alunos = db.query(Aluno).all()
        return {"data": alunos}
    except SQLAlchemyError as e:
        print(f"Erro no banco de dados ao listar alunos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no banco de dados ao buscar lista de alunos."
        )
    except Exception as e:
        print(f"Erro inesperado ao listar alunos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar alunos."
        )

@router.get("/{matricula}", response_model=schemas.AlunoResponseSingle)
def get_aluno_by_id(matricula: str, db: Session = Depends(database.get_db)):
    try:
        aluno = db.query(Aluno).filter(Aluno.matricula == matricula).first()
        
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        return {"data": aluno}
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        print(f"Erro no banco de dados ao buscar aluno por matrícula: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no banco de dados ao buscar aluno."
        )
    except Exception as e:
        print(f"Erro inesperado ao buscar aluno por matrícula: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar aluno."
        )

@router.put("/{matricula}", response_model=schemas.AlunoResponseSingle)
def update_aluno(
    matricula: str,
    aluno_update: schemas.AlunoUpdate,
    db: Session = Depends(database.get_db)
):
    try:
        # Busca o aluno existente
        aluno = db.query(Aluno).filter(Aluno.matricula == matricula).first()
        
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Valida avatar se fornecido
        if aluno_update.avatar_id_fk is not None:
            avatar = db.query(Avatar).filter(Avatar.id == aluno_update.avatar_id_fk).first()
            if not avatar:
                raise HTTPException(status_code=404, detail="Avatar não encontrado")
            aluno.avatar_id_fk = aluno_update.avatar_id_fk
        
        # Valida nickname se fornecido
        if aluno_update.nickname is not None:
            # Trata string vazia como None
            nickname_final = aluno_update.nickname.strip() if aluno_update.nickname and aluno_update.nickname.strip() else None
            
            # Só valida se o nickname for diferente do atual e não for None
            if nickname_final != aluno.nickname and nickname_final is not None:
                existing_aluno = db.query(Aluno).filter(
                    Aluno.nickname == nickname_final,
                    Aluno.matricula != matricula
                ).first()
                if existing_aluno:
                    raise HTTPException(status_code=400, detail="Nickname já está em uso")
            
            aluno.nickname = nickname_final
        
        # Atualiza nome se fornecido
        if aluno_update.nome is not None:
            aluno.nome = aluno_update.nome
        
        # Valida e atualiza senha se fornecida
        if aluno_update.nova_senha:
            if not aluno_update.senha_atual:
                raise HTTPException(
                    status_code=400,
                    detail="É necessário informar a senha atual para alterar a senha"
                )
            
            # Verifica se a senha atual está correta
            if not verify_password(aluno_update.senha_atual, aluno.senha):
                raise HTTPException(
                    status_code=400,
                    detail="Senha atual incorreta"
                )
            
            # Valida tamanho mínimo da nova senha
            if len(aluno_update.nova_senha) < 6:
                raise HTTPException(
                    status_code=400,
                    detail="A nova senha deve ter no mínimo 6 caracteres"
                )
            
            # Atualiza a senha
            aluno.senha = hash_password(aluno_update.nova_senha)
        
        db.commit()
        db.refresh(aluno)
        
        # Recarrega o aluno com relacionamentos
        aluno_atualizado = db.query(Aluno).filter(Aluno.matricula == matricula).first()
        
        if not aluno_atualizado:
            raise HTTPException(status_code=404, detail="Erro ao recarregar aluno após atualização")
        
        return {"data": aluno_atualizado}
    
    except HTTPException as e:
        db.rollback()
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao atualizar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados: Não foi possível atualizar o aluno. Detalhe: {e}"
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao atualizar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao atualizar aluno."
        )