from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
FastAPI().mount("/", StaticFiles(directory="ui/dist", html=True), name="static")