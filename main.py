from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.users import Users
from routes.token import TokenAPI
from routes.group_stats import GroupStatsRoutes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
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
    GroupStatsRoutes, 
    tags=["Estadísticas"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)