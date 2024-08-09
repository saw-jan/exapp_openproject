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
    backend_url = get_backend_url()
    url = urlparse(backend_url)

    # Requried for csrf validation
    _request.headers.__dict__["_list"].append(
        (
            "origin".encode(),
            f"{url.scheme}://{url.netloc}".encode(),
        )
    )

    response = await proxy_request_to_server(_request, path)

    response.headers["content-security-policy"] = (
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    )
    response.headers["referrer-policy"] = "strict-origin"
    return response


async def proxy_request_to_server(request: Request, path: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        backend_url = get_backend_url()
        url = f"{backend_url}/{path}"
        headers = {}
        for k, v in request.headers.items():
            if k == "cookie" or k == "host":
                continue
            headers[k] = v

        if request.method == "GET":
            response = await client.get(
                url,
                params=request.query_params,
                cookies=request.cookies,
                headers=headers,
            )

        else:
            cookies = {}
            for ck, cv in request.cookies.items():
                if ck == "_open_project_session":
                    cookies[ck] = cv

            req_body = await request.body()
            response = await client.request(
                method=request.method,
                url=url,
                params=request.query_params,
                cookies=cookies,
                headers=headers,
                content=req_body,
            )

        response_header = dict(response.headers)
        response_header.pop("transfer-encoding", None)
        response_header.pop("content-encoding", None)
        response_header["content-length"] = str(response.content.__len__())
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_header,
        )


def get_backend_url():
    return os.getenv("OP_BACKEND_URL", "http://localhost:8080")


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
