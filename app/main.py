from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import aluno, atividade, avatar, badge, login, professor, turma
from fastapi.staticfiles import StaticFiles

app = FastAPI()

origins = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(aluno.router)
app.include_router(atividade.router)
app.include_router(avatar.router)
app.include_router(badge.router)
app.include_router(professor.router)
app.include_router(turma.router)
app.include_router(login.router)

@app.get("/")
def root():
    return {"message": "API rodando com FastAPI 🚀"}

app.mount("/static", StaticFiles(directory="app/static"), name="static")
