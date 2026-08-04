"""Gmail OAuth + thread listing for AIOS dashboard Inbox tab."""
import base64
import json
import os
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE = Path(__file__).parent.parent
CRED_FILE = BASE / ".gmail-credentials.json"
TOKEN_FILE = BASE / ".gmail-token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


def _service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CRED_FILE), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def auth_status() -> dict:
    return {
        "credentials_present": CRED_FILE.exists(),
        "token_present": TOKEN_FILE.exists(),
        "ready": CRED_FILE.exists() and TOKEN_FILE.exists(),
    }


def authorize():
    """Force-run the OAuth flow. Returns status dict."""
    if not CRED_FILE.exists():
        return {"ok": False, "error": "missing .gmail-credentials.json"}
    flow = InstalledAppFlow.from_client_secrets_file(str(CRED_FILE), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)
    TOKEN_FILE.write_text(creds.to_json())
    return {"ok": True, "token_path": str(TOKEN_FILE)}


def list_threads(query: str = "in:inbox", limit: int = 20) -> dict:
    """Return latest threads w/ snippet, subject, from, ts."""
    svc = _service()
    res = svc.users().threads().list(userId="me", q=query, maxResults=limit).execute()
    threads = []
    for t in res.get("threads", []):
        full = svc.users().threads().get(userId="me", id=t["id"], format="metadata",
                                          metadataHeaders=["From", "Subject", "Date"]).execute()
        msgs = full.get("messages", [])
        if not msgs:
            continue
        last = msgs[-1]
        hdrs = {h["name"]: h["value"] for h in last.get("payload", {}).get("headers", [])}
        threads.append({
            "id": t["id"],
            "snippet": full.get("snippet", ""),
            "from": hdrs.get("From", ""),
            "subject": hdrs.get("Subject", "(no subject)"),
            "date": hdrs.get("Date", ""),
            "msg_count": len(msgs),
            "labels": last.get("labelIds", []),
            "unread": "UNREAD" in last.get("labelIds", []),
        })
    return {"threads": threads, "count": len(threads), "query": query}


def get_thread(thread_id: str) -> dict:
    svc = _service()
    full = svc.users().threads().get(userId="me", id=thread_id, format="full").execute()
    msgs = []
    for m in full.get("messages", []):
        hdrs = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
        body = _extract_body(m.get("payload", {}))
        msgs.append({
            "id": m["id"],
            "from": hdrs.get("From", ""),
            "to": hdrs.get("To", ""),
            "subject": hdrs.get("Subject", ""),
            "date": hdrs.get("Date", ""),
            "body": body[:5000],
        })
    return {"id": thread_id, "messages": msgs}


def _extract_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
        # fall through to first part
        for part in payload["parts"]:
            text = _extract_body(part)
            if text:
                return text
    data = payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
    return ""


def send_draft(to: str, subject: str, body: str) -> dict:
    """Create a draft, return id. (Sending requires Bryan to manually press send.)"""
    svc = _service()
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = svc.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return {"draft_id": draft["id"]}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "auth":
        print(json.dumps(authorize(), indent=2))
    elif cmd == "list":
        print(json.dumps(list_threads(limit=10), indent=2))
    elif cmd == "status":
        print(json.dumps(auth_status(), indent=2))
