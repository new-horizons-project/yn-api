import os
import uuid
import platform
from datetime import datetime

import fastapi
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from colorama import Fore, Style
from user_agents import parse

from .routers import *
from .db import init_db, get_session, users, topic, media, application_parameter as ap, tasks as tasks_db
from . import __version__, __release_subname__, config, tasks


async def init_config(db: AsyncSession):
    ap_value, _ = await ap.get_application_parameter_with_value(db, "application.system.root_user")
    config.system_ap.root_user_id = uuid.UUID(ap_value.default_value) if ap_value.default_value is not None else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"""                    
    {Fore.BLUE + Style.BRIGHT}                       ##
    {Fore.BLUE + Style.BRIGHT}                      ###
    {Fore.BLUE + Style.BRIGHT}                **## *###
    {Fore.BLUE + Style.BRIGHT}              ++**# **##         {Fore.CYAN + Style.BRIGHT}New Horizons{Style.RESET_ALL}
    {Fore.BLUE + Style.BRIGHT}        =-----===+ ***#          {Fore.CYAN + Style.BRIGHT}API Codename {Style.RESET_ALL}{Fore.YELLOW}Yoshino Niku{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}   =-----== = ====+++**                    
    {Fore.BLUE + Style.BRIGHT}  ---      ===++ +*******#       {Style.BRIGHT + Fore.CYAN}Python          : {Style.RESET_ALL}{Fore.YELLOW}{platform.python_version()}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}  --     --===+ ++***   **##     {Style.BRIGHT + Fore.CYAN}FastAPI version : {Style.RESET_ALL}{Fore.YELLOW}{fastapi.__version__}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}        ---=== +++***    **#     {Style.BRIGHT + Fore.CYAN}API version     : {Style.RESET_ALL}{Fore.YELLOW}{__version__} {__release_subname__}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}       --====  +++**     +*      {Style.BRIGHT + Fore.CYAN}OS              : {Style.RESET_ALL}{Fore.YELLOW}{platform.release()}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}     =---=====++++*   =          {Style.BRIGHT + Fore.CYAN}Started at      : {Style.RESET_ALL}{Fore.YELLOW}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}    -----=====++++*
    {Fore.BLUE + Style.BRIGHT}   ------= ===++++
    {Fore.BLUE + Style.BRIGHT}    =----  ===+++
    """)

    await init_db()

    if not os.path.isdir(config.settings.STATIC_MEDIA_FOLDER):
        os.mkdir(config.settings.STATIC_MEDIA_FOLDER)

    session_generator = get_session()
    session = await anext(session_generator)

    await init_config(session)

    try:
        await ap.init_ap(session)
        await users.create_root_user(session)
        await topic.create_base_translation(session)
        await media.init_media(session)
        await tasks_db.init_tasks(session)
        await tasks.schedule_tasks(session)
        yield
    finally:
        await session.close()


app = FastAPI(title=config.settings.APP_NAME, version=__version__, lifespan=lifespan)


@app.get("/")
def ping():
    info = {
        "app_name": config.settings.APP_NAME,
        "api_version": __version__,
        "release": __release_subname__,
        "fastapi_version": fastapi.__version__
    }

    return info

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Access-Control-Allow-Origin", "Authorization"]
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(user_router_public)
app.include_router(topic_router)
app.include_router(topic_router_public)
app.include_router(tag_router)
app.include_router(tag_router_public)
app.include_router(translation_codes_router)
app.include_router(media_router)
app.include_router(ap_router)
app.include_router(ap_router_public)
app.include_router(category_router)
app.include_router(category_router_public)