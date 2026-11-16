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


def builds(tok, bundle, want=None):
    """What App Store Connect thinks of the builds we have uploaded.

    An upload succeeding only means Apple accepted the bytes. The build then
    has to process, and can sit in PROCESSING, come back INVALID, or be held
    waiting on export compliance — none of which the upload step can see.

    With `want`, returns that build's processing state, or None if Apple has
    no record of it yet. That is the difference between "we sent it" and
    "they have it", and it is the whole reason a green upload can be followed
    by an empty TestFlight.
    """
    code, body = get(tok, f"/v1/apps?filter[bundleId]={bundle}")
    if code != 200 or not body.get("data"):
        print(f"\n=== app lookup: HTTP {code} ===")
        for e in body.get("errors", [])[:2]:
            print("   ", e.get("title"), "-", e.get("detail"))
        return None
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
        return None
    rows = body.get("data", [])
    print(f"   {len(rows)} builds\n")
    print(f"   {'build':<14} {'state':<12} {'expired':<8} {'encryption':<11} uploaded")
    found = None
    for b in rows:
        a = b["attributes"]
        here = str(a.get("version", ""))
        print(f"   {here:<14} {a.get('processingState',''):<12} "
              f"{str(a.get('expired','')):<8} {str(a.get('usesNonExemptEncryption','')):<11} "
              f"{a.get('uploadedDate','')}"
              f"{'   <- this run' if want and here == str(want) else ''}")
        if want and here == str(want):
            found = a.get("processingState", "UNKNOWN")
    if rows:
        testers(tok, app["id"], rows[0])
    return found


def testers(tok, app_id, newest):
    """Who, if anyone, the newest build has actually been given to.

    A VALID build is not a delivered build. It sits in App Store Connect
    until it is assigned to a group that has testers in it, and nothing
    about the upload says whether that ever happened — so ten green uploads
    and an empty TestFlight app is a perfectly consistent state.
    """
    code, body = get(tok, f"/v1/apps/{app_id}/betaGroups?limit=50"
                          "&fields[betaGroups]=name,isInternalGroup,"
                          "hasAccessToAllBuilds")
    if code != 200:
        print(f"\n   beta groups: HTTP {code}")
        return
    groups = body.get("data", [])
    print(f"\n   {len(groups)} testing groups")
    if not groups:
        print("   -> nothing to hand a build to. Every build will stay in "
              "App Store Connect and reach no one.")
        return
    print(f"\n   {'group':<28} {'kind':<10} {'all builds':<11} testers")
    for g in groups:
        a = g["attributes"]
        code, b2 = get(tok, f"/v1/betaGroups/{g['id']}/betaTesters?limit=1")
        n = b2.get("meta", {}).get("paging", {}).get("total", "?") \
            if code == 200 else "?"
        print(f"   {a.get('name',''):<28} "
              f"{'internal' if a.get('isInternalGroup') else 'external':<10} "
              f"{str(a.get('hasAccessToAllBuilds','')):<11} {n}")

    ver = newest["attributes"].get("version", "")
    code, body = get(tok, f"/v1/builds/{newest['id']}/betaGroups?limit=50"
                          "&fields[betaGroups]=name")
    named = [g["attributes"].get("name", "") for g in body.get("data", [])] \
        if code == 200 else []
    print(f"\n   build {ver} is assigned to: "
          + (", ".join(named) if named else "no group"))
    if not named:
        print("   -> this is why it is not in the TestFlight app. The build "
              "is fine; it has simply not been given to anybody.")


def await_build(key_id, issuer, p8, bundle, want, tries=20, gap=30):
    """Wait until App Store Connect actually has the build.

    Polled rather than assumed. Apple processes asynchronously, so a build
    that will end up INVALID is VALID-looking for a while and then simply
    never appears in TestFlight — with nothing in this log to say so.
    """
    for i in range(1, tries + 1):
        state = builds(token(key_id, issuer, p8), bundle, want)
        if state in ("VALID", "PROCESSING"):
            print(f"\nApple has build {want}: {state}")
            # PROCESSING is a fine place to stop waiting: the build is on
            # their side and will appear in TestFlight when it finishes.
            return 0
        if state in ("INVALID", "FAILED"):
            print(f"\n::error::build {want} came back {state} — check the "
                  "email App Store Connect sent the account owner")
            return 1
        print(f"\n   not there yet ({i}/{tries}); waiting {gap}s")
        time.sleep(gap)
    print(f"\n::error::App Store Connect never showed build {want}. The upload "
          "reported success, so the binary was accepted for delivery and "
          "then dropped during processing — the reason is in the email Apple "
          "sent the account owner.")
    return 1


def main():
    key_id, issuer, p8 = sys.argv[1], sys.argv[2], sys.argv[3]
    # positional, but only if it is one: otherwise `--await 123` would be
    # read as the bundle id and every lookup would quietly find no app
    bundle = (sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith("--")
              else "com.orthoprayers.western")
    if "--await" in sys.argv:
        want = sys.argv[sys.argv.index("--await") + 1]
        sys.exit(await_build(key_id, issuer, p8, bundle, want))
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
