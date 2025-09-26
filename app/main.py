import platform
from datetime import datetime

import fastapi
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from colorama import Fore, Style

from .routers import *
from .db import init_db, get_session, users, topic
from . import __version__

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
    {Fore.BLUE + Style.BRIGHT}        ---=== +++***    **#     {Style.BRIGHT + Fore.CYAN}API version     : {Style.RESET_ALL}{Fore.YELLOW}{__version__}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}       --====  +++**     +*      {Style.BRIGHT + Fore.CYAN}OS              : {Style.RESET_ALL}{Fore.YELLOW}{platform.release()}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}     =---=====++++*   =          {Style.BRIGHT + Fore.CYAN}Started at      : {Style.RESET_ALL}{Fore.YELLOW}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Fore.RESET}
    {Fore.BLUE + Style.BRIGHT}    -----=====++++*              
    {Fore.BLUE + Style.BRIGHT}   ------= ===++++               
    {Fore.BLUE + Style.BRIGHT}    =----  ===+++                 
	""")

	await init_db()

	session_generator = get_session()
	session = await anext(session_generator)

	try:
		await users.create_root_user(session)
		await topic.create_base_translation(session)
		yield
	finally:
		await session.close()


app = FastAPI(title="New Horizons API", version=__version__, lifespan=lifespan)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(user_router_public)
app.include_router(topic_router)
app.include_router(topic_router_public)
app.include_router(tag_router)
app.include_router(tag_router_public)
app.include_router(translation_codes_router)
