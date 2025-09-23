Auth API

Endpoints

- POST `/auth/register`
  - body: `{ "username": string, "password": string, "email?": string, "display_name?": string }`
  - sets HttpOnly cookies `session` and `refresh`. returns user `{ id, username, email, display_name, is_active }`

- POST `/auth/login`
  - body: `{ "login": string /* username or email */, "password": string }`
  - sets cookies as above, returns user.

- POST `/auth/refresh`
  - uses `refresh` cookie, rotates `session` cookie, returns user.

- POST `/auth/logout`
  - revokes current session, clears cookies.

- GET `/auth/me`
  - requires `session` cookie, returns user.

Roles

- Roles: `user`, `editor`, `moderator`, `admin`. Stored in `user_roles (user_id, role)`.
- A helper dependency is available: `require_roles("admin")`.
- Dev check endpoint: `GET /auth/admin/ping` requires `admin`.


Cookies

- `session`: short‑lived (env `SESSION_HOURS`, default 12h)
- `refresh`: long‑lived (env `REFRESH_DAYS`, default 30d)
- HttpOnly, Secure (env `COOKIE_SECURE=1|0`), SameSite (env `COOKIE_SAMESITE=lax|strict|none`), Domain (env `COOKIE_DOMAIN`)

DB

- users: requires `username` (unique, case‑insensitive), optional `password_hash` (bcrypt via pgcrypto), `email` optional
- user_sessions: stores sha256 hashes of tokens

Integration

- Include router in FastAPI app:
  ```python
  from apps.backend.domains.platform.auth import router as auth_router
  app.include_router(auth_router)
  ```
- For CORS with cookies:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "https://your-frontend"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

Frontend

- Login:
  ```ts
  await fetch("/auth/login", { method: "POST", credentials: "include", headers: {"content-type":"application/json"}, body: JSON.stringify({login, password}) })
  ```
- Get current user:
  ```ts
  await fetch("/auth/me", { credentials: "include" })
  ```
- Logout:
  ```ts
  await fetch("/auth/logout", { method: "POST", credentials: "include" })
  ```
