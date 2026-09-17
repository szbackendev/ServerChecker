import contextlib

from fastapi import FastAPI

from database import init_db


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    print("====================","Приложуха завершает свою работу", "====================", sep="\n")
    # 1. Надо сделать проверку зависимостей из файла requirements.txt



