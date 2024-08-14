from fastapi import FastAPI

from routes.users import Users
from routes.token import TokenAPI

app = FastAPI()

app.include_router(
    TokenAPI, 
    tags=["Token"]
    )
app.include_router(
    Users, 
    tags=["Usuarios"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)