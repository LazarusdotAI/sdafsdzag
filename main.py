from fastapi import FastAPI, Header, Query, Body
from dotenv import load_dotenv
import requests
import os

# Load variables from a local .env file, if present
load_dotenv()

app = FastAPI(title="ATLAS Proxy API", version="1.0.0")

# Base URLs for the upstream services
ALP_BASE: str = "https://paper-api.alpaca.markets"
FMP_BASE: str = "https://financialmodelingprep.com/api/v4"

# Read secrets from environment variables (recommended)
ALP_KEY: str | None = os.getenv("APCA_API_KEY_ID")
ALP_SECRET: str | None = os.getenv("APCA_API_SECRET_KEY")
FMP_KEY: str | None = os.getenv("FMP_KEY")


@app.post("/call_alpaca")
def call_alpaca(
    path: str = Body(..., description="Alpaca REST path, e.g. /v2/orders"),
    method: str = Body("GET", description="HTTP method to use when calling Alpaca"),
    params: dict | None = Body({}, description="Query parameters"),
    body: dict | None = Body({}, description="JSON body for POST/PUT requests"),
    apca_api_key_id: str | None = Header(None, description="Override Alpaca API key ID"),
    apca_api_secret_key: str | None = Header(None, description="Override Alpaca API secret")
):
    """Proxy any request to Alpaca's REST API.

    The user's keys are pulled from headers if provided, otherwise fall back
    to environment variables set on the host running this service.
    """
    url = f"{ALP_BASE}{path}"

    headers = {
        "APCA-API-KEY-ID": apca_api_key_id or ALP_KEY,
        "APCA-API-SECRET-KEY": apca_api_secret_key or ALP_SECRET,
        "Content-Type": "application/json",
    }

    # Ensure we have credentials
    if headers["APCA-API-KEY-ID"] is None or headers["APCA-API-SECRET-KEY"] is None:
        return {
            "error": "Missing Alpaca credentials. Provide them via headers or environment variables."
        }

    response = requests.request(method, url, headers=headers, params=params, json=body)
    response.raise_for_status()
    return response.json()


@app.post("/call_fmp")
def call_fmp(
    path: str = Body(..., description="FMP API path, e.g. /insider-trading"),
    params: dict | None = Body({}, description="Additional query params")
):
    """Proxy any request to Financial Modeling Prep's API."""
    if not FMP_KEY:
        return {"error": "Missing FMP_KEY environment variable."}

    query_params = params.copy() if params else {}
    query_params["apikey"] = FMP_KEY

    url = f"{FMP_BASE}{path}"
    response = requests.get(url, params=query_params)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Support `python main.py` for quick local dev (not for prod)
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 