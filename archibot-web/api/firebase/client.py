import json
import os
from pathlib import Path
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore, storage


def _resolve_storage_bucket_name() -> str | None:
    bucket = (
        os.getenv("FIREBASE_STORAGE_BUCKET")
        or os.getenv("NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET")
        or "archibot-eb7be.firebasestorage.app"
    )
    bucket = bucket.strip()
    if bucket.startswith("gs://"):
        bucket = bucket[5:]
    return bucket or None


@lru_cache(maxsize=1)
def get_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    bucket_name = _resolve_storage_bucket_name()
    options = {"storageBucket": bucket_name} if bucket_name else None

    if service_account_json:
        credential = credentials.Certificate(json.loads(service_account_json))
        return firebase_admin.initialize_app(credential, options=options)
    if service_account_path:
        credential = credentials.Certificate(service_account_path)
        return firebase_admin.initialize_app(credential, options=options)

    firebase_dir = Path(__file__).resolve().parent
    json_files = sorted(firebase_dir.glob("*.json"))
    if len(json_files) == 1:
        credential = credentials.Certificate(str(json_files[0]))
        return firebase_admin.initialize_app(credential, options=options)

    return firebase_admin.initialize_app(options=options)


@lru_cache(maxsize=1)
def get_firestore_client():
    get_firebase_app()
    return firestore.client()


@lru_cache(maxsize=1)
def get_storage_bucket():
    app = get_firebase_app()
    bucket_name = _resolve_storage_bucket_name()
    return storage.bucket(name=bucket_name, app=app)
