import typing
import httpx
import os
from urllib.parse import urlparse
from starlette.responses import Response, JSONResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from nc_py_api import NextcloudApp
from nc_py_api.ex_app import AppAPIAuthMiddleware, LogLvl, run_app, nc_app
from nc_py_api.ex_app.integration_fastapi import fetch_models_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(AppAPIAuthMiddleware)
APP.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"{nc.app_cfg.app_name}={enabled}")
    if enabled:
        nc.log(LogLvl.INFO, f"{nc.app_cfg.app_name} is enabled")
    else:
        nc.log(LogLvl.INFO, f"{nc.app_cfg.app_name} is disabled")
    return ""


@APP.get("/heartbeat")
async def heartbeat_callback():
    return JSONResponse(content={"status": "ok"})


@APP.post("/init")
async def init_callback(
    b_tasks: BackgroundTasks, nc: typing.Annotated[NextcloudApp, Depends(nc_app)]
):
    b_tasks.add_task(fetch_models_task, nc, {}, 0)
    return JSONResponse(content={})


@APP.put("/enabled")
async def enabled_callback(
    enabled: bool, nc: typing.Annotated[NextcloudApp, Depends(nc_app)]
):
    return JSONResponse(content={"error": enabled_handler(enabled, nc)})


@APP.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH", "OPTIONS"]
)
async def proxy_Requests(_request: Request, path: str):
    response = await proxy_request_to_server(_request, path)

    headers = dict(response.headers)
    headers.pop("transfer-encoding", None)
    headers.pop("content-encoding", None)
    headers["content-length"] = str(response.content.__len__())
    headers["content-security-policy"] = (
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(headers),
    )


async def proxy_request_to_server(request: Request, path: str):
    async with httpx.AsyncClient(follow_redirects=False) as client:
        backend_url = get_backend_url()
        url = f"{backend_url}/{path}"
        headers = {}
        for k, v in request.headers.items():
            # NOTE:
            # - remove 'host' to make op routes work
            # - remove 'origin' to validate csrf
            if k == "host" or k == "origin":
                continue
            headers[k] = v

        if request.method == "GET":
            response = await client.get(
                url,
                params=request.query_params,
                headers=headers,
            )
        else:
            response = await client.request(
                method=request.method,
                url=url,
                params=request.query_params,
                headers=headers,
                content=await request.body(),
            )

        if response.is_redirect:
            if url.endswith("/login") or "/two_factor_authentication/" in url:
                redirect_path = urlparse(response.headers["location"]).path
                redirect_url = get_nc_url() + redirect_path
                response.headers["location"] = redirect_url
                # fake 200 status code so that NC passes the response to the browser
                response.status_code = 200
            else:
                headers["content-length"] = "0"
                response = await handle_redirects(
                    client,
                    request.method if response.status_code == 307 else "GET",
                    response.headers["location"],
                    headers,
                )

        return response


async def handle_redirects(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict,
):
    response = await client.request(
        method=method,
        url=url,
        headers=headers,
    )

    if response.is_redirect:
        return await handle_redirects(
            client,
            method if response.status_code == 307 else "GET",
            response.headers["location"],
            headers,
        )

    return response


def get_backend_url():
    return os.getenv("OP_BACKEND_URL", "http://localhost:8080")


def get_nc_url():
    nc_url = os.getenv("NEXTCLOUD_URL", "http://localhost/index.php")
    url = urlparse(nc_url)
    return f"{url.scheme}://{url.netloc}"


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
