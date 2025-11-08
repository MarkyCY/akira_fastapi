from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.news import News
from routes.users import Users
from routes.contest import Contest
from routes.token import TokenAPI
from routes.group_stats import GroupStatsRoutes
from routes.icons import IconsAPI
from routes.canva import CanvaAPI
from routes.my_anime_list import MyAL

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
    MyAL, 
    prefix="/mal",
    tags=["MyAnimeList"]
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
app.include_router(
    IconsAPI, 
    prefix="/icons",
    tags=["Iconos"]
    )
app.include_router(
    CanvaAPI, 
    prefix="/canva",
    tags=["Canva"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)