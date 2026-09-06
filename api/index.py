from fastapi import FastAPI

# Vercel looks for the `app` instance in this entry point file
app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World from FastAPI on Vercel!"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
