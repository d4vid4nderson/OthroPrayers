#!/usr/bin/env python3
"""Ask the Developer portal what an App Store Connect API key can reach.

Xcode's automatic signing reports what it could not find, never why, so a key
with no portal access, a key on the wrong team and a misconfigured project all
produce the same message. This asks Apple directly.

Everything here is a GET. Nothing is created, changed or deleted.

No third-party packages: the ES256 signature is made with openssl, which every
macOS runner has, because `pip install` into the system Python is not reliably
available and a probe that cannot run tells you nothing.

    python3 asc_probe.py <key-id> <issuer-id> <path-to-.p8> [bundle-id]
"""
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request


def b64(data: bytes) -> str:
    """base64url, unpadded — what JWS uses."""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def der_to_raw(der: bytes) -> bytes:
    """An ES256 JWS signature is r||s, 32 bytes each.

    openssl emits DER: SEQUENCE { INTEGER r, INTEGER s }, where each integer is
    minimally encoded — leading zero byte when the high bit is set, shorter when
    there are leading zeros. Both have to come out fixed-width.
    """
    if der[0] != 0x30:
        raise ValueError("not a DER sequence")
    # skip SEQUENCE tag and length (short or long form)
    i = 2 if der[1] < 0x80 else 2 + (der[1] & 0x7F)

    def integer(j):
        if der[j] != 0x02:
            raise ValueError("expected a DER integer")
        n = der[j + 1]
        v = der[j + 2: j + 2 + n]
        return v.lstrip(b"\x00").rjust(32, b"\x00"), j + 2 + n

    r, i = integer(i)
    s, _ = integer(i)
    return r + s


def token(key_id: str, issuer: str, p8_path: str) -> str:
    header = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    now = int(time.time())
    claims = {"iss": issuer, "iat": now, "exp": now + 600,
              "aud": "appstoreconnect-v1"}
    signing_input = f"{b64(json.dumps(header).encode())}." \
                    f"{b64(json.dumps(claims).encode())}"
    der = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", p8_path],
        input=signing_input.encode(), capture_output=True, check=True).stdout
    return f"{signing_input}.{b64(der_to_raw(der))}"


def get(tok: str, path: str):
    req = urllib.request.Request(
        "https://api.appstoreconnect.apple.com" + path,
        headers={"Authorization": "Bearer " + tok})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except Exception:
            return e.code, {}


def builds(tok, bundle):
    """What App Store Connect thinks of the builds we have uploaded.

    An upload succeeding only means Apple accepted the bytes. The build then
    has to process, and can sit in PROCESSING, come back INVALID, or be held
    waiting on export compliance — none of which the upload step can see.
    """
    code, body = get(tok, f"/v1/apps?filter[bundleId]={bundle}")
    if code != 200 or not body.get("data"):
        print(f"\n=== app lookup: HTTP {code} ===")
        for e in body.get("errors", [])[:2]:
            print("   ", e.get("title"), "-", e.get("detail"))
        return
    app = body["data"][0]
    print(f"\n=== {app['attributes']['name']} ({app['id']}) ===")

    code, body = get(tok, f"/v1/builds?filter[app]={app['id']}"
                          "&limit=10&sort=-uploadedDate"
                          "&fields[builds]=version,processingState,uploadedDate,"
                          "expired,usesNonExemptEncryption")
    if code != 200:
        print(f"   builds: HTTP {code}")
        for e in body.get("errors", [])[:2]:
            print("   ", e.get("title"), "-", e.get("detail"))
        return
    rows = body.get("data", [])
    print(f"   {len(rows)} builds\n")
    print(f"   {'build':<14} {'state':<12} {'expired':<8} {'encryption':<11} uploaded")
    for b in rows:
        a = b["attributes"]
        print(f"   {a.get('version',''):<14} {a.get('processingState',''):<12} "
              f"{str(a.get('expired','')):<8} {str(a.get('usesNonExemptEncryption','')):<11} "
              f"{a.get('uploadedDate','')}")


def main():
    key_id, issuer, p8 = sys.argv[1], sys.argv[2], sys.argv[3]
    bundle = sys.argv[4] if len(sys.argv) > 4 else "com.orthoprayers.western"
    tok = token(key_id, issuer, p8)
    if "--builds" in sys.argv:
        builds(tok, bundle)
        return

    checks = [
        ("certificates", "/v1/certificates?limit=200"),
        ("bundle id", f"/v1/bundleIds?filter[identifier]={bundle}"),
        ("profiles", "/v1/profiles?limit=200"),
    ]
    forbidden = 0
    for label, path in checks:
        code, body = get(tok, path)
        print(f"\n=== {label}: HTTP {code} ===")
        if code != 200:
            forbidden += 1
            for err in body.get("errors", [])[:3]:
                print("   ", err.get("title"), "-", err.get("detail"))
            continue
        rows = body.get("data", [])
        print(f"    {len(rows)} returned")
        for d in rows[:30]:
            a = d.get("attributes", {})
            bits = [a.get("certificateType") or a.get("profileType")
                    or a.get("identifier") or "",
                    a.get("name") or "", a.get("status") or ""]
            print("    ", " | ".join(str(b) for b in bits if b))

    print("\n--- verdict ---")
    if forbidden == 0:
        print("the key can read the Developer portal; manual signing is viable")
    else:
        print(f"{forbidden} of {len(checks)} endpoints refused — this key cannot "
              "manage signing assets, whatever role the UI shows")


if __name__ == "__main__":
    main()
