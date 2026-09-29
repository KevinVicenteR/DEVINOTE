from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def saludar():
    print("hola mundo")
