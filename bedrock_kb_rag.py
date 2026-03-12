# bedrock_kb_rag.py
import os
import requests
import boto3
from requests_aws4auth import AWS4Auth

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_KB_ID = os.getenv("BEDROCK_KB_ID")

BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0"
)

_BOTO_SESSION = boto3.Session(region_name=AWS_REGION)


def _sigv4_auth(service_name: str = "bedrock-agent-runtime") -> AWS4Auth:
    """
    Creates a fresh SigV4 signer each request.
    With temporary creds (like SSO-exported creds in .env), this ensures we always use
    whatever is currently in the environment.
    """
    creds = _BOTO_SESSION.get_credentials()
    if creds is None:
        raise RuntimeError(
            "No AWS credentials found. Paste AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/AWS_SESSION_TOKEN into .env."
        )

    frozen = creds.get_frozen_credentials()
    return AWS4Auth(
        frozen.access_key,
        frozen.secret_key,
        AWS_REGION,
        service_name,
        session_token=frozen.token,
    )


def retrieve_and_generate(user_text: str, top_k: int = 5, timeout: int = 60) -> str:
    """
    Calls Bedrock Knowledge Base RetrieveAndGenerate (single-call RAG).
    """
    if not BEDROCK_KB_ID:
        raise RuntimeError("BEDROCK_KB_ID is not set.")

    url = (
        f"https://bedrock-agent-runtime.{AWS_REGION}.amazonaws.com/retrieveAndGenerate"
    )

    model_arn = f"arn:aws:bedrock:{AWS_REGION}::foundation-model/{BEDROCK_MODEL_ID}"

    payload = {
        "input": {"text": user_text},
        "retrieveAndGenerateConfiguration": {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": BEDROCK_KB_ID,
                "modelArn": model_arn,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {"numberOfResults": top_k}
                },
            }
        },
    }

    r = requests.post(
        url,
        json=payload,
        auth=_sigv4_auth(service_name="bedrock"),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )

    print(f"retrieveAndGenerate failed: {r.status_code} {r.text}")

    if r.status_code != 200:
        
        raise RuntimeError(f"retrieveAndGenerate failed: {r.status_code} {r.text}")

    data = r.json()
    answer = (data.get("output") or {}).get("text")
    if not answer:
        raise RuntimeError(f"Unexpected response shape: {data}")

    return answer
    
    
def health_probe(timeout: int = 15) -> dict:
    """
    Lightweight call to validate:
    - env vars are loaded
    - SigV4 signing works
    - credentials are not expired
    - KB endpoint is reachable
    """
    if not BEDROCK_KB_ID:
        return {"ok": False, "error": "BEDROCK_KB_ID is not set"}

    # Minimal query to avoid cost/latency
    test_question = "health check"

    try:
        answer = retrieve_and_generate(test_question, top_k=1, timeout=timeout)
        return {
            "ok": True,
            "region": AWS_REGION,
            "knowledge_base_id": BEDROCK_KB_ID,
            "model_id": BEDROCK_MODEL_ID,
            "sample_answer_preview": (answer[:120] + "...") if len(answer) > 120 else answer,
        }
    except Exception as e:
        return {
            "ok": False,
            "region": AWS_REGION,
            "knowledge_base_id": BEDROCK_KB_ID,
            "model_id": BEDROCK_MODEL_ID,
            "error": str(e),
        }
