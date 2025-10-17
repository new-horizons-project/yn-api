import os
import platform
from datetime import datetime

import fastapi
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from colorama import Fore, Style
from user_agents import parse

from .routers import *
from .db import init_db, get_session, users, topic, media
from . import __version__, __release_subname__, config

started_at = datetime.now()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"""                    
    {Fore.BLUE + Style.BRIGHT}                       ##
    {Fore.BLUE + Style.BRIGHT}                      ###
    {Fore.BLUE + Style.BRIGHT}                **## *###
    {Fore.BLUE + Style.BRIGHT}              ++**# **##         {Fore.CYAN + Style.BRIGHT}New Horizons Project{Style.RESET_ALL}
    {Fore.BLUE + Style.BRIGHT}        =-----===+ ***#          {Fore.CYAN + Style.BRIGHT}API Codename {Style.RESET_ALL}{Fore.YELLOW}Yoshino Niku{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}   =-----== = ====+++**                    
    {Fore.BLUE + Style.BRIGHT}  ---      ===++ +*******#       {Style.BRIGHT + Fore.CYAN}Python          : {Style.RESET_ALL}{Fore.YELLOW}{platform.python_version()}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}  --     --===+ ++***   **##     {Style.BRIGHT + Fore.CYAN}FastAPI version : {Style.RESET_ALL}{Fore.YELLOW}{fastapi.__version__}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}        ---=== +++***    **#     {Style.BRIGHT + Fore.CYAN}API version     : {Style.RESET_ALL}{Fore.YELLOW}{__version__} {__release_subname__}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}       --====  +++**     +*      {Style.BRIGHT + Fore.CYAN}OS              : {Style.RESET_ALL}{Fore.YELLOW}{platform.release()}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}     =---=====++++*   =          {Style.BRIGHT + Fore.CYAN}Started at      : {Style.RESET_ALL}{Fore.YELLOW}{started_at.strftime('%Y-%m-%d %H:%M:%S')}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}    -----=====++++*
    {Fore.BLUE + Style.BRIGHT}   ------= ===++++
    {Fore.BLUE + Style.BRIGHT}    =----  ===+++
    """)

    await init_db()

    if not os.path.isdir(config.settings.STATIC_MEDIA_FOLDER):
        os.mkdir(config.settings.STATIC_MEDIA_FOLDER)

    session_generator = get_session()
    session = await anext(session_generator)

    try:
        await users.create_root_user(session)
        await topic.create_base_translation(session)
        await media.init_media(session)
        yield
    finally:
        await session.close()


app = FastAPI(title=config.settings.APP_NAME, version=__version__, lifespan=lifespan)


@app.get("/")
def ping(request: Request):
    since_started = datetime.now() - started_at
    user_agent = parse(request.headers.get("user-agent", "unknown"))

    if user_agent.is_mobile:
        device_type = "mobile"
    elif user_agent.is_tablet:
        device_type = "tablet"
    elif user_agent.is_pc:
        device_type = "pc"
    elif user_agent.is_bot:
        device_type = "bot"
    else:
        device_type = "unknown"

    info = {
        "app_name": config.settings.APP_NAME,
        "api_version": __version__,
        "release": __release_subname__,
        "fastapi_version": fastapi.__version__,
        "uptime": f"{since_started.days}:{since_started.seconds // 3600:02}:{(since_started.seconds // 60) % 60:02}:{since_started.seconds:02}",
        "client_information": {
            "ip": request.client.host,
            "os_family": user_agent.os.family,
            "os_version": user_agent.os.version_string,
            "browser": user_agent.browser.family,
            "browser_version": user_agent.browser.version_string,
            "device": user_agent.device.family,
            "type": device_type
        }
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