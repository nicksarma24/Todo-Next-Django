
Double-check `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` match exactly between the
two files — a typo here (I fat-fingered an extra letter once) will get you a
DNS error or a 401 that's annoying to trace back.

Both `.env` files are already git-ignored — don't commit them.

## Running it locally (no Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Defaults to SQLite (`db.sqlite3`), so there's nothing else to install to try
it out. If you want Postgres instead, set `DATABASE_URL` to something like
`postgres://todo_user:todo_password@localhost:5432/todo_db` and re-run
migrate.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then go to `http://localhost:3000`.

Both of the above need to be running at the same time, in separate
terminals — the frontend can't do much on its own since it just proxies
real work to Django.

## Running with Docker instead

```bash
docker compose up --build
```

Spins up Postgres, Django (migrations run automatically), and Next.js
together. You still need `backend/.env` and `frontend/.env.local` filled in
first, since Compose just reads them via `env_file`.

## API

Every endpoint needs `Authorization: Bearer <access token>`.

| Method | Path                | What it does                          |
|--------|---------------------|---------------------------------------|
| GET    | `/api/todos/`        | List your todos. Supports `?completed=true|false` and `?search=`. Paginated. |
| POST   | `/api/todos/`        | Create one (`title` required, `description` optional). |
| GET    | `/api/todos/:id/`    | Get one (has to be yours). |
| PATCH  | `/api/todos/:id/`    | Partial update, e.g. `{"completed": true}`. |
| DELETE | `/api/todos/:id/`    | Delete it.                        |

Errors always come back as `{"detail": "...", "status_code": 404}` or
similar, so the frontend doesn't have to special-case different shapes.

## Tests

```bash
cd backend
python manage.py test
```

A couple worth pointing out:
- `apps/authentication/tests.py` signs its own test JWTs with a locally
  generated RSA keypair (and swaps in a fake JWKS cache) so it can test real
  signature/issuer/audience/expiry checks without needing to hit Auth0.
- `apps/todos/tests/test_todos.py::TodoIsolationTests` is the important one
  — it specifically checks that account A can't read, update, or delete
  account B's todo by guessing the id, and that you can't fake ownership by
  sending `"account": <someone else's id>` in a create request.

I didn't get to writing frontend tests for this submission — the backend
suite is what's actually enforcing the security-critical stuff, so that's
where I focused. If I had more time I'd add a Playwright test for the
login → create → logout flow, and some MSW-mocked unit tests for the error
handling in `lib/api.ts`.

## Notes on some of the decisions I made

- **SQLite by default, Postgres via one env var.** Didn't want anyone
  (including me) to need to stand up Postgres just to poke at this locally.
- **Accounts get created the first time we see a token from them**, keyed
  off the Auth0 `sub` claim. There's no real "sign up" step to build on our
  end since Auth0's login screen already covers that.
- **404 instead of 403 for someone else's todo.** A 403 would be admitting
  "yeah that id exists, it's just not yours," which is a small info leak.
  Since the queryset is already scoped before the lookup even happens,
  another account's todo just looks like it doesn't exist, and DRF gives a
  404 for free — didn't need to add anything special for this.
- **The `/api/token` route** felt like the simplest way to bridge the
  server-side Auth0 session to something the browser can use to call Django
  directly, rather than proxying every single todo request through a Next.js
  API route. Trade-off is the access token sits in browser JS memory
  briefly, but it's short-lived and can't do anything outside this one API,
  so I was fine with that.
- **`account` isn't even a field on the serializer.** Not just "ignored if
  sent" — it's not there at all, so there's no field for a malicious payload
  to land in.
- Kept the UI pretty bare-bones on purpose, since the assignment says
  functionality matters more than visual polish. No component library, just
  enough CSS to make it usable on a phone.