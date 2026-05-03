# Polymarket Clone — FastAPI

A simplified prediction market REST API built with FastAPI, SQLAlchemy, and PostgreSQL.

---

## Features

- JWT authentication (register, login)
- Markets: create, list, resolve
- Trading: buy/sell YES or NO shares via a constant-sum AMM
- Automatic settlement and payout on resolution
- Wallet: deposit and withdraw balance
- Full transaction ledger

---

## Project Structure

```
polymarket/
├── app/
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Settings from .env
│   ├── database.py        # SQLAlchemy engine + get_db dependency
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── exceptions.py      # Custom HTTP exceptions
│   ├── auth/
│   │   ├── hashing.py     # bcrypt password hashing
│   │   ├── jwt.py         # JWT create/decode
│   │   └── dependencies.py # get_current_user, require_admin
│   ├── crud/
│   │   ├── users.py
│   │   ├── markets.py
│   │   ├── positions.py
│   │   └── transactions.py
│   ├── services/
│   │   ├── pricing.py     # AMM price calculation
│   │   ├── trading.py     # execute_buy / execute_sell
│   │   └── settlement.py  # resolve market + pay winners
│   └── routers/
│       ├── auth.py        # /auth/register, /auth/login, /auth/me
│       ├── users.py       # /users/me, /users/me/positions
│       ├── markets.py     # /markets CRUD + buy/sell/resolve
│       └── wallet.py      # /wallet/deposit, /wallet/withdraw
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
├── alembic.ini
├── seed.py
├── requirements.txt
└── .env.example
```

---

## Quickstart

### 1. Clone and install

```bash
git clone <your-repo>
cd polymarket

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql://user_bet:bets753@localhost:5432/bets_bot
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

### 3. Create the database

```bash
# Create the DB in postgres first:
createdb polymarket

# Run migrations:
alembic upgrade head
```

### 4. Seed admin user

```bash
python seed.py
# Creates admin@example.com / admin1234 with $1000 balance
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | — | Create account |
| POST | `/api/v1/auth/login` | — | Get JWT token |
| GET | `/api/v1/auth/me` | ✓ | Current user |
| GET | `/api/v1/users/me` | ✓ | Profile |
| PATCH | `/api/v1/users/me` | ✓ | Update profile |
| GET | `/api/v1/users/me/positions` | ✓ | My positions |
| GET | `/api/v1/users/me/transactions` | ✓ | My transaction history |
| POST | `/api/v1/wallet/deposit` | ✓ | Add funds |
| POST | `/api/v1/wallet/withdraw` | ✓ | Withdraw funds |
| GET | `/api/v1/markets` | — | List markets |
| GET | `/api/v1/markets/{id}` | — | Market detail |
| POST | `/api/v1/markets` | Admin | Create market |
| PATCH | `/api/v1/markets/{id}` | Admin | Update market |
| POST | `/api/v1/markets/{id}/buy` | ✓ | Buy shares |
| POST | `/api/v1/markets/{id}/sell` | ✓ | Sell shares |
| POST | `/api/v1/markets/{id}/resolve` | Admin | Resolve market |

---

## How Trading Works

Prices are driven by a **constant-sum AMM**:

```
yes_price = yes_shares / (yes_shares + no_shares)
no_price  = no_shares  / (yes_shares + no_shares)
```

Prices always sum to 1.0. Buying YES raises the YES price; selling YES lowers it.

On resolution, each winning share pays out **$1.00**. Losing shares pay $0.

---

## Example Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"alice","password":"password123"}'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=password123"

# 3. Deposit funds (use token from step 2)
curl -X POST http://localhost:8000/api/v1/wallet/deposit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100}'

# 4. Buy YES shares on market 1
curl -X POST http://localhost:8000/api/v1/markets/1/buy \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"side": "yes", "amount": 10}'
```
