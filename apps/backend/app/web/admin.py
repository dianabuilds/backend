from typing import Annotated


@router.post("/login")
async def login_action(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    # Поддерживаем и JSON, и form-data
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        data = await request.json()
        username = (data or {}).get("username")
        password = (data or {}).get("password")
    else:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

    tokens = await _authenticate(db, username, password)

    # Ставим HttpOnly cookie с access и refresh токенами
    # SameSite=Lax подходит для same-site (localhost:5173 -> localhost:8000 считается same-site)
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        "access_token", tokens.access_token, httponly=True, samesite="lax", path="/"
    )
    if getattr(tokens, "refresh_token", None):
        response.set_cookie(
            "refresh_token",
            tokens.refresh_token,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return response
