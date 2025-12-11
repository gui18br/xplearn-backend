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
from app.schemas import aluno_atividade as aluno_atividade_schemas
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
        # Carrega os relacionamentos de badge e turma
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
            raise HTTPException(status_code=400, detail="Atividade não possui turma associada")
        
        # Busca todos os alunos da turma usando join explícito na tabela de junção
        alunos_da_turma = db.query(Aluno).join(
            aluno_turma, Aluno.matricula == aluno_turma.c.aluno_matricula_fk
        ).filter(
            aluno_turma.c.turma_id_fk == atividade.turma.id
        ).options(
            joinedload(Aluno.avatar)
        ).all()
        
        # Busca alunos que já fizeram a atividade
        alunos_que_fizeram = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id
        ).all()
        
        # Converte nota para string (pode vir como Decimal do banco)
        matriculas_que_fizeram = {}
        for aa in alunos_que_fizeram:
            nota_str = str(aa.nota) if aa.nota is not None else "0"
            matriculas_que_fizeram[aa.aluno_matricula_fk] = nota_str
        
        # Cria um conjunto de matrículas dos alunos da turma para verificação rápida
        matriculas_da_turma = {aluno.matricula for aluno in alunos_da_turma}
        
        # Busca alunos que fizeram a atividade mas podem não estar na turma (para garantir que apareçam)
        matriculas_que_fizeram_set = set(matriculas_que_fizeram.keys())
        matriculas_faltantes = matriculas_que_fizeram_set - matriculas_da_turma
        
        # Debug: log das matrículas
        print(f"DEBUG: Matrículas da turma: {matriculas_da_turma}")
        print(f"DEBUG: Matrículas que fizeram: {matriculas_que_fizeram_set}")
        print(f"DEBUG: Matrículas faltantes: {matriculas_faltantes}")
        
        # Se houver alunos marcados que não estão na lista da turma, busca eles também
        alunos_adicionais = []
        if matriculas_faltantes:
            print(f"DEBUG: Buscando {len(matriculas_faltantes)} alunos adicionais que fizeram a atividade")
            alunos_adicionais = db.query(Aluno).filter(
                Aluno.matricula.in_(matriculas_faltantes)
            ).options(
                joinedload(Aluno.avatar)
            ).all()
            print(f"DEBUG: Encontrados {len(alunos_adicionais)} alunos adicionais")
        
        # Combina ambas as listas (alunos da turma + alunos marcados que não estão na turma)
        todos_alunos = list(alunos_da_turma) + alunos_adicionais
        print(f"DEBUG: Total de alunos a processar: {len(todos_alunos)}")
        
        # Monta lista de status dos alunos
        alunos_status = []
        for aluno in todos_alunos:
            try:
                fez_atividade = aluno.matricula in matriculas_que_fizeram
                
                # Monta o objeto avatar de forma segura
                avatar_dict = None
                if aluno.avatar:
                    try:
                        avatar_dict = {
                            "id": aluno.avatar.id if hasattr(aluno.avatar, 'id') else None,
                            "caminho_foto": aluno.avatar.caminho_foto if hasattr(aluno.avatar, 'caminho_foto') else None
                        }
                    except Exception as e:
                        print(f"Erro ao processar avatar do aluno {aluno.matricula}: {e}")
                        avatar_dict = None
                
                # Converte nota para string se existir
                nota_aluno = matriculas_que_fizeram.get(aluno.matricula)
                if nota_aluno is not None:
                    # Garante que é string (pode vir como Decimal)
                    nota_aluno = str(nota_aluno)
                
                alunos_status.append(
                    aluno_atividade_schemas.AlunoStatusAtividade(
                        matricula=aluno.matricula,
                        nome=aluno.nome if aluno.nome else "",
                        nickname=aluno.nickname,
                        fez_atividade=fez_atividade,
                        nota=nota_aluno,
                        avatar=avatar_dict
                    )
                )
            except Exception as e:
                print(f"Erro ao processar aluno {aluno.matricula if aluno else 'desconhecido'}: {e}")
                import traceback
                traceback.print_exc()
                # Continua com o próximo aluno ao invés de quebrar tudo
                continue
        
        return {
            "atividade_id": id,
            "alunos": alunos_status
        }
    
    except HTTPException as e:
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao buscar alunos da atividade: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao buscar alunos da atividade."
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao buscar alunos da atividade: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar alunos da atividade."
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
        
        # Verifica se já existe registro
        existing = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id,
            AlunoAtividade.aluno_matricula_fk == matricula
        ).first()
        
        if existing:
            # Atualiza a nota se fornecida
            if nota.nota is not None:
                try:
                    nota_valor = float(nota.nota)
                    nota_max = float(atividade.nota_max) if atividade.nota_max else 10.0
                    
                    if nota_valor < 0:
                        raise HTTPException(status_code=400, detail="A nota não pode ser menor que 0")
                    if nota_valor > nota_max:
                        raise HTTPException(
                            status_code=400,
                            detail=f"A nota não pode ser maior que {nota_max} (nota máxima da atividade)"
                        )
                    
                    existing.nota = str(nota_valor)
                    db.commit()
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail="Nota inválida")
            return {"msg": f"Aluno {matricula} já estava marcado como tendo feito a atividade"}
        
        # Valida a nota se fornecida
        nota_valor = 0.0
        if nota.nota is not None:
            try:
                nota_valor = float(nota.nota)
                nota_max = float(atividade.nota_max) if atividade.nota_max else 10.0
                
                if nota_valor < 0:
                    raise HTTPException(status_code=400, detail="A nota não pode ser menor que 0")
                if nota_valor > nota_max:
                    raise HTTPException(
                        status_code=400,
                        detail=f"A nota não pode ser maior que {nota_max} (nota máxima da atividade)"
                    )
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Nota inválida")
        
        # Cria novo registro com nota padrão "0" se não fornecida
        novo_registro = AlunoAtividade(
            aluno_matricula_fk=matricula,
            atividade_id_fk=id,
            nota=str(nota_valor)
        )
        
        db.add(novo_registro)
        db.commit()
        
        return {"msg": f"Aluno {matricula} marcado como tendo feito a atividade"}
    
    except HTTPException as e:
        db.rollback()
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Erro no banco de dados ao marcar aluno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no banco de dados ao marcar aluno."
        )
    except Exception as e:
        db.rollback()
        print(f"Erro inesperado ao marcar aluno: {e}")
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
        # Busca o registro
        registro = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id,
            AlunoAtividade.aluno_matricula_fk == matricula
        ).first()
        
        if not registro:
            raise HTTPException(status_code=404, detail="Registro não encontrado")
        
        db.delete(registro)
        db.commit()
        
        return {"msg": f"Aluno {matricula} desmarcado da atividade"}
    
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
            # Retorna lista vazia se não tiver turma, em vez de erro
            return {"atividade_id": id, "alunos": []}
        
        # 1. Busca alunos da turma
        alunos_da_turma = db.query(Aluno).join(
            aluno_turma, Aluno.matricula == aluno_turma.c.aluno_matricula_fk
        ).filter(
            aluno_turma.c.turma_id_fk == atividade.turma.id
        ).options(
            joinedload(Aluno.avatar)
        ).all()
        
        # 2. Busca registros de quem já fez a atividade (notas)
        alunos_que_fizeram = db.query(AlunoAtividade).filter(
            AlunoAtividade.atividade_id_fk == id
        ).all()
        
        mapa_notas = {}
        for aa in alunos_que_fizeram:
            # Força conversão para string, tratando None como "0" ou vazio
            nota_val = str(aa.nota) if aa.nota is not None else None
            mapa_notas[aa.aluno_matricula_fk] = nota_val
        
        # 3. Identifica alunos extras
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