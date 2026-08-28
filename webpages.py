from fastapi import APIRouter, Request

from settings import settings
from templates_config import templates

router_pages = APIRouter(tags=["Frontend pages"])

@router_pages.get("/user")
def user_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboarduser.html")

@router_pages.get(f"{settings.admin_panel_url}/admin_login")
def admin_login(request: Request):
    return templates.TemplateResponse(request=request, name="adminlogin.html")

@router_pages.get(f"{settings.admin_panel_url}/admin_panel")
def admin_panel(request: Request):
    return templates.TemplateResponse(request=request, name="adminpanel.html")

@router_pages.get("/dashboard_server")
def dashboard_server(request: Request):
    return templates.TemplateResponse(request=request, name="dashboardserver.html")

@router_pages.get("/tg_connect")
def dashboard_tg(request: Request):
    return templates.TemplateResponse(request=request, name="dashboardtg.html")

@router_pages.get("/docs_page")
def docs(request: Request):
    return templates.TemplateResponse(request=request, name="docs.html")

@router_pages.get("/sign_in")
def user_sign_in(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router_pages.get("/sign_up")
def user_sign_up(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")
