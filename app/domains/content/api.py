from fastapi import APIRouter, Response

router = APIRouter(prefix="/admin/content", tags=["admin"], include_in_schema=False)


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)
async def deprecated_content(
    path: str = "", response: Response | None = None
) -> Response:
    return Response(
        status_code=299, headers={"Warning": "Deprecated, use /admin/nodes"}
    )
