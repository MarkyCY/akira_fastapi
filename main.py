from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.news import News
from routes.users import Users
from routes.contest import Contest
from routes.token import TokenAPI
from routes.group_stats import GroupStatsRoutes

app = FastAPI(swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

app.add_middleware(
   CORSMiddleware,
   allow_origins=["https://akira-mini-app.vercel.app"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
   expose_headers=["Content-Range"],
   allow_origin_regex="^https://akira-mini-app\.vercel\.app$"
)

app.include_router(
    TokenAPI, 
    tags=["Token"]
    )
app.include_router(
    Users, 
    tags=["Usuarios"]
    )
app.include_router(
    Contest, 
    tags=["Concursos"]
    )
app.include_router(
    News,
    tags=["Noticias"]
    )
app.include_router(
    GroupStatsRoutes, 
    tags=["Estadísticas"]
    )
