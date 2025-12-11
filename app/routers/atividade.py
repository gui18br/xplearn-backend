from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError
from app import database
from app.schemas import atividade as schemas
from app.models.atividade import Atividade
from app.models.badge import Badge
from app.models.turma import Turma
from app.models.aluno_atividade import AlunoAtividade
from app.models.aluno import Aluno
from app.models.aluno_turma import aluno_turma
from app.models.aluno_badge import AlunoBadge
from app.schemas import aluno_atividade as aluno_atividade_schemas
from datetime import datetime
import traceback


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
        
        # Recarrega com relacionamentos
        created_atv = db.query(Atividade).options(
            joinedload(Atividade.badge),
            joinedload(Atividade.turma)
        ).filter(Atividade.id == new_atv.id).first()
    
        return {"data": created_atv}
    
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
        # Carrega os relacionamentos de badge e turma
        atvs = db.query(Atividade).options(
            joinedload(Atividade.badge),
            joinedload(Atividade.turma)
        ).all()
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
        atv = db.query(Atividade).options(
            joinedload(Atividade.badge),
            joinedload(Atividade.turma)
        ).filter(Atividade.id == id).first()
    
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

@router.put("/{id}", response_model=schemas.AtividadeResponseSingle)
def update_atv(
    id: int,
    atv: schemas.AtividadeCreate,
    db: Session = Depends(database.get_db)
):
    try:
        activity = db.query(Atividade).filter(Atividade.id == id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Atividade não encontrada")

        if atv.turma_id_fk:
            turma = db.query(Turma).filter(Turma.id == atv.turma_id_fk).first()
            if not turma:
                raise HTTPException(status_code=404, detail="Turma informada não encontrada")
            activity.turma_id_fk = turma.id
        else:
            pass

        if atv.badge_id_fk:
            badge = db.query(Badge).filter(Badge.id == atv.badge_id_fk).first()
            if not badge:
                raise HTTPException(status_code=404, detail="Badge informada não encontrada")
            activity.badge_id_fk = badge.id
        else:
            pass

        activity.nome = atv.nome
        activity.descricao = atv.descricao
        activity.nota_max = atv.nota_max
        activity.pontos = atv.pontos
        activity.data_entrega = atv.data_entrega

        db.commit()
        db.refresh(activity)

        updated_atv = db.query(Atividade).options(
            joinedload(Atividade.badge),
            joinedload(Atividade.turma)
        ).filter(Atividade.id == activity.id).first()

        return {"data": updated_atv}

    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco ao atualizar atividade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao atualizar atividade."
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao atualizar atividade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao atualizar atividade."
        )

@router.post("/{id}/alunos/{matricula}")
def marcar_aluno_fez_atividade(
    id: int,
    matricula: str,
    nota: aluno_atividade_schemas.AlunoAtividadeCreate,
    db: Session = Depends(database.get_db)
):
    try:
        # Verifica se a atividade existe
        atividade = db.query(Atividade).filter(Atividade.id == id).first()
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade não encontrada")
        
        # Verifica se o aluno existe
        aluno = db.query(Aluno).filter(Aluno.matricula == matricula).first()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Verifica se o aluno está na turma da atividade
        if atividade.turma_id_fk:
            aluno_na_turma = db.query(aluno_turma).filter(
                aluno_turma.c.aluno_matricula_fk == matricula,
                aluno_turma.c.turma_id_fk == atividade.turma_id_fk
            ).first()
            
            if not aluno_na_turma:
                raise HTTPException(
                    status_code=400,
                    detail=f"Aluno {matricula} não está matriculado na turma desta atividade"
                )
        
        # Verifica se já existe registro de atividade feita
        existing = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id,
            AlunoAtividade.aluno_matricula_fk == matricula
        ).first()
        
        if existing:
            # Se já existe, APENAS atualiza a nota
            if nota.nota is not None:
                try:
                    nota_valor = float(nota.nota)
                    nota_max = float(atividade.nota_max) if atividade.nota_max else 10.0
                    
                    if nota_valor < 0 or nota_valor > nota_max:
                        raise HTTPException(status_code=400, detail="Nota fora dos limites permitidos")
                    
                    existing.nota = str(nota_valor)
                    db.commit()
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail="Nota inválida")
            return {"msg": "Nota atualizada. O aluno já possuía o XP e Badge desta atividade."}
        
        # === 1. PROCESSAR NOTA ===
        nota_valor = 0.0
        if nota.nota is not None:
            try:
                nota_valor = float(nota.nota)
                nota_max = float(atividade.nota_max) if atividade.nota_max else 10.0
                if nota_valor < 0 or nota_valor > nota_max:
                    raise HTTPException(status_code=400, detail="Nota fora dos limites permitidos")
            except ValueError:
                raise HTTPException(status_code=400, detail="Nota inválida")
        
        # Cria o registro de que fez a atividade
        novo_registro = AlunoAtividade(
            aluno_matricula_fk=matricula,
            atividade_id_fk=id,
            nota=str(nota_valor)
        )
        db.add(novo_registro)
        
        # === 2. ATRIBUIR XP E NÍVEL ===
        pontos_da_atividade = atividade.pontos if atividade.pontos else 0
        xp_atual = aluno.xp if aluno.xp else 0
        
        # Soma o XP
        aluno.xp = xp_atual + pontos_da_atividade
        
        # CORREÇÃO: Nível a cada 1000 XP
        aluno.nivel = 1 + (aluno.xp // 1000)
        
        # === 3. ATRIBUIR BADGE (SE HOUVER) ===
        msg_badge = ""
        if atividade.badge_id_fk:
            # Verifica se o aluno já tem esse badge
            badge_existente = db.query(AlunoBadge).filter(
                AlunoBadge.aluno_matricula_fk == matricula,
                AlunoBadge.badge_id_fk == atividade.badge_id_fk
            ).first()

            if not badge_existente:
                novo_badge_aluno = AlunoBadge(
                    aluno_matricula_fk=matricula,
                    badge_id_fk=atividade.badge_id_fk,
                    data_conquista=datetime.now() # <--- AQUI ESTAVA FALTANDO A DATA
                )
                db.add(novo_badge_aluno)
                msg_badge = " e Badge conquistado!"
            else:
                msg_badge = " (Badge já possuído)"

        db.commit()
        
        return {
            "msg": f"Atividade concluída! +{pontos_da_atividade} XP.{msg_badge} Nível atual: {aluno.nivel}"
        }
    
    except HTTPException as e:
        db.rollback()
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao marcar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao marcar aluno: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao marcar aluno: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao marcar aluno."
        )

@router.put("/{id}/alunos/{matricula}/nota")
def atualizar_nota_aluno(
    id: int,
    matricula: str,
    nota_update: aluno_atividade_schemas.AlunoAtividadeCreate,
    db: Session = Depends(database.get_db)
):
    try:
        # Verifica se a atividade existe
        atividade = db.query(Atividade).filter(Atividade.id == id).first()
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade não encontrada")
        
        # Verifica se o aluno existe
        aluno = db.query(Aluno).filter(Aluno.matricula == matricula).first()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Busca o registro
        registro = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id,
            AlunoAtividade.aluno_matricula_fk == matricula
        ).first()
        
        if not registro:
            raise HTTPException(status_code=404, detail="Aluno não está marcado como tendo feito esta atividade")
        
        # Valida a nota
        try:
            nota_valor = float(nota_update.nota) if nota_update.nota is not None else 0.0
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Nota inválida")
        
        # Valida se a nota está dentro do range permitido
        nota_max = float(atividade.nota_max) if atividade.nota_max else 10.0
        
        if nota_valor < 0:
            raise HTTPException(status_code=400, detail="A nota não pode ser menor que 0")
        
        if nota_valor > nota_max:
            raise HTTPException(
                status_code=400,
                detail=f"A nota não pode ser maior que {nota_max} (nota máxima da atividade)"
            )
        
        # Atualiza a nota
        registro.nota = str(nota_valor)
        db.commit()
        
        return {"msg": f"Nota do aluno {matricula} atualizada com sucesso"}
    
    except HTTPException as e:
        db.rollback()
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao atualizar nota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao atualizar nota."
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao atualizar nota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao atualizar nota."
        )

@router.delete("/{id}/alunos/{matricula}")
def desmarcar_aluno_fez_atividade(
    id: int,
    matricula: str,
    db: Session = Depends(database.get_db)
):
    try:
        # Busca a atividade
        atividade = db.query(Atividade).filter(Atividade.id == id).first()
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade não encontrada")

        # Busca o aluno
        aluno = db.query(Aluno).filter(Aluno.matricula == matricula).first()

        # Busca o registro da atividade feita
        registro = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id,
            AlunoAtividade.aluno_matricula_fk == matricula
        ).first()
        
        if not registro:
            raise HTTPException(status_code=404, detail="Registro não encontrado")
        
        # === 1. REMOVE XP e RECALCULA NÍVEL ===
        if aluno:
            pontos_a_remover = atividade.pontos if atividade.pontos else 0
            xp_atual = aluno.xp if aluno.xp else 0
            
            # Subtrai o XP
            novo_xp = xp_atual - pontos_a_remover
            aluno.xp = novo_xp if novo_xp >= 0 else 0
            
            # CORREÇÃO: Recalcula nível (Regra 1000 XP)
            aluno.nivel = 1 + (aluno.xp // 1000)
        
        # === 2. REMOVE BADGE (SE HOUVER E FOI GANHO NESTA ATIVIDADE) ===
        if atividade.badge_id_fk:
            badge_associado = db.query(AlunoBadge).filter(
                AlunoBadge.aluno_matricula_fk == matricula,
                AlunoBadge.badge_id_fk == atividade.badge_id_fk
            ).first()
            
            if badge_associado:
                db.delete(badge_associado)

        # Remove o registro da atividade
        db.delete(registro)
        db.commit()
        
        return {"msg": f"Aluno {matricula} desmarcado. XP e Badge removidos."}
    
    except HTTPException as e:
        db.rollback()
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao desmarcar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao desmarcar aluno."
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao desmarcar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao desmarcar aluno."
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

@router.get("/{id}/alunos", response_model=aluno_atividade_schemas.AlunosAtividadeResponse)
def get_alunos_atividade(id: int, db: Session = Depends(database.get_db)):
    try:
        # Busca a atividade com turma
        atividade = db.query(Atividade).options(
            joinedload(Atividade.turma)
        ).filter(Atividade.id == id).first()
        
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade não encontrada")
        
        if not atividade.turma:
            return {"atividade_id": id, "alunos": []}
        
        alunos_da_turma = db.query(Aluno).join(
            aluno_turma, Aluno.matricula == aluno_turma.c.aluno_matricula_fk
        ).filter(
            aluno_turma.c.turma_id_fk == atividade.turma.id
        ).options(
            joinedload(Aluno.avatar)
        ).all()
        
        alunos_que_fizeram = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id
        ).all()
        
        mapa_notas = {}
        for aa in alunos_que_fizeram:
            nota_val = str(aa.nota) if aa.nota is not None else None
            mapa_notas[aa.aluno_matricula_fk] = nota_val
        
        matriculas_da_turma = {aluno.matricula for aluno in alunos_da_turma}
        matriculas_com_atividade = set(mapa_notas.keys())
        matriculas_extras = matriculas_com_atividade - matriculas_da_turma
        
        alunos_adicionais = []
        if matriculas_extras:
            alunos_adicionais = db.query(Aluno).filter(
                Aluno.matricula.in_(list(matriculas_extras))
            ).options(
                joinedload(Aluno.avatar)
            ).all()
        
        todos_alunos = list(alunos_da_turma) + list(alunos_adicionais)
        
        lista_final_alunos = []
        
        for aluno in todos_alunos:
            try:
                fez = aluno.matricula in mapa_notas
                nota_aluno = mapa_notas.get(aluno.matricula)
                
                # BLINDAGEM DE DADOS: Evita erro de validação Pydantic
                # Se o schema pedir string e vier None, quebra. Aqui garantimos string.
                safe_nome = aluno.nome if aluno.nome else "Sem nome"
                safe_nickname = aluno.nickname if aluno.nickname else "" 
                
                # Monta avatar
                avatar_data = None
                if aluno.avatar:
                    avatar_data = {
                        "id": aluno.avatar.id,
                        "caminho_foto": aluno.avatar.caminho_foto or ""
                    }

                aluno_obj = aluno_atividade_schemas.AlunoStatusAtividade(
                    matricula=aluno.matricula,
                    nome=safe_nome,
                    nickname=safe_nickname,  # Passando string vazia em vez de None
                    fez_atividade=fez,
                    nota=nota_aluno,         # Pode ser None dependendo do schema
                    avatar=avatar_data
                )
                lista_final_alunos.append(aluno_obj)
                
            except Exception as e:
                print(f"ERRO DE VALIDAÇÃO NO ALUNO {aluno.matricula}: {e}")
                # Não dá raise aqui, apenas pula o aluno problemático para não quebrar a tela toda
                continue

        return {
            "atividade_id": id,
            "alunos": lista_final_alunos
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        print("====== ERRO 500 CRÍTICO ======")
        traceback.print_exc() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no servidor."
        )