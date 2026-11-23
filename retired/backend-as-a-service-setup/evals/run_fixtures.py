#!/usr/bin/env python3
"""Run the fixture cases against scripts/baas_audit.py.

    python evals/run_fixtures.py            # run all cases
    python evals/run_fixtures.py --write D  # only write the fixture projects into folder D to inspect them

The fixture projects are built in a temporary folder at run time. Secret-looking
values are assembled in code (fake, random-looking, never real) so that no
credential-shaped text is stored in the package. Expected findings are in
fixtures/expected.json (checked by hand). Writes nothing inside the skill folder.
Exit 0 if every case passes, 1 otherwise.
"""
import base64
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import baas_audit  # noqa: E402


def b64(obj):
    return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).decode().rstrip("=")


def fake_jwt(role, ref):
    return b64({"alg": "HS256", "typ": "JWT"}) + "." + b64({"role": role, "ref": ref}) + "." + b64({"sig": ref * 3})


def fake_letters(seed, n=24):
    return "".join(chr(97 + (i * seed) % 26) for i in range(n))


SVC = fake_jwt("service_role", "proj1")
SVC_DEV = fake_jwt("service_role", "dev1")
ANON = fake_jwt("anon", "proj1")
ANON_DEV = fake_jwt("anon", "dev1")
WHSEC = "whsec_" + fake_letters(7)
ADMIN = fake_letters(5)
DBURL = "postgres://app:" + fake_letters(3, 10) + "@db.example.test:5432/app"
LIVE = "sk_live_" + fake_letters(11)
ADMINKEY = fake_letters(9, 22)
PEM = "-----BEGIN " + "PRIVATE KEY-----" + fake_letters(13, 30)
ALL_SECRETS = [SVC, SVC_DEV, WHSEC, ADMIN, DBURL, LIVE, ADMINKEY, PEM]

RULES_BAD = """rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // test mode
    match /{document=**} {
      allow read, write: if true;
    }
    match /posts/{id} {
      allow read: if request.auth != null;
    }
    match /temp/{id} {
      allow write: if request.time < timestamp.date(2030, 1, 1);
    }
    match /public/{id} {
      allow read;
    }
  }
}
"""
RULES_GOOD = """rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /notes/{noteId} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.ownerId;
    }
  }
}
"""
RTDB_BAD = """{
  "rules": {
    ".read": true,
    "users": {
      "$uid": { ".read": "auth != null", ".write": "auth.uid === $uid" }
    },
    "queue": { ".write": "now < 1900000000000" }
  }
}
"""
SQL_BAD = """-- notes without rls
create table public.notes (id int);
create table public.profiles (id uuid);
alter table public.profiles enable row level security;
create policy "anyone updates" on public.profiles for update using (true);
create table public.things (id int);
alter table public.things enable row level security;
grant all on public.notes to anon;
create function public.f() returns void security definer language sql as $$ select 1 $$;
"""
SQL_GOOD = """create table public.notes (id uuid primary key, owner uuid not null, body text);
alter table public.notes enable row level security;
create policy "owner reads" on public.notes for select to authenticated using (owner = auth.uid());
create policy "owner writes" on public.notes for insert to authenticated with check (owner = auth.uid());
"""


def make_index(paths):
    out = b"DIRC" + (2).to_bytes(4, "big") + len(paths).to_bytes(4, "big")
    for p in paths:
        name = p.encode()
        entry = b"\x00" * 60 + min(len(name), 0xFFF).to_bytes(2, "big") + name
        entry += b"\x00" * (8 - len(entry) % 8)
        out += entry
    return out + b"\x00" * 20


def fixtures():
    return {
        "good": {
            ".gitignore": ".env*\n!.env.example\nnode_modules/\n",
            ".env.example": "SUPABASE_URL=https://your-project.example.test\nSUPABASE_SERVICE_ROLE_KEY=your-service-role-key\nNEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key\n",
            ".env.development": "SUPABASE_URL=https://dev.example.test\nSUPABASE_SERVICE_ROLE_KEY=%s\nNEXT_PUBLIC_SUPABASE_ANON_KEY=%s\n" % (SVC_DEV, ANON_DEV),
            ".env.production": "SUPABASE_URL=https://prod.example.test\nSUPABASE_SERVICE_ROLE_KEY=%s\nNEXT_PUBLIC_SUPABASE_ANON_KEY=%s\n" % (SVC, ANON),
            "firestore.rules": RULES_GOOD,
            "firebase.json": '{"firestore": {"rules": "firestore.rules"}}',
            "supabase/migrations/001_notes.sql": SQL_GOOD,
            "supabase/config.toml": "[storage.buckets.private_docs]\npublic = false\n",
            "src/client.js": "const url = process.env.SUPABASE_URL;\nconst apiSecret = \"your-secret-here-please\";\n",
        },
        "bad_env": {
            ".gitignore": "node_modules/\n",
            ".env": "NEXT_PUBLIC_SUPABASE_URL=https://abc.example.test\nNEXT_PUBLIC_SUPABASE_ANON_KEY=%s\nSUPABASE_SERVICE_ROLE_KEY=%s\nSTRIPE_WEBHOOK_SECRET=%s\nNEXT_PUBLIC_ADMIN_SECRET=%s\nDATABASE_URL=%s\n" % (ANON, SVC, WHSEC, ADMIN, DBURL),
            ".env.production": "NEXT_PUBLIC_SERVICE_ROLE_KEY=%s\n" % SVC,
            ".env.example": "SUPABASE_SERVICE_ROLE_KEY=%s\n" % SVC,
        },
        "drift": {
            ".gitignore": ".env*\n",
            ".env.development": "API_URL=https://dev.app.test\nPROJECT_URL=https://shared.app.test\nFEATURE_X=on\n",
            ".env.production": "API_URL=http://localhost:54321\nPROJECT_URL=https://shared.app.test\nSENTRY_DSN=https://k@o1.app.test/1\n",
            ".env.staging": "API_URL=https://stg.app.test\nPROJECT_URL=https://stg2.app.test\n",
        },
        "bad_rules": {
            "firestore.rules": RULES_BAD,
            "database.rules.json": RTDB_BAD,
            "firebase.json": '{"firestore": {"rules": "firestore.rules"}, "storage": {"rules": "storage.rules"}, "database": {}}',
            "supabase/migrations/001.sql": SQL_BAD,
            "supabase/config.toml": "[storage.buckets.avatars]\npublic = true\n",
            "appwrite.json": json.dumps({"collections": [{"$id": "posts", "$permissions": ['read("any")', 'create("any")']}]}),
        },
        "bad_source": {
            ".gitignore": "secrets/\n",
            "public/config.js": 'window.CFG = { url: "https://x.example.test", key: "%s" };\nconst adminKey = "%s";\n' % (SVC, ADMINKEY),
            "server/seed.py": 'STRIPE = "%s"\n' % LIVE,
            "secrets/key.json": '{"type": "service_account", "private_key": "%s"}' % PEM,
            "certs/deploy.pem": "# fake test key\n%s\n" % PEM,
            "src/app.js": "const url = process.env.SUPABASE_URL;\nconst secretKey = process.env.SECRET_KEY;\nconst apiSecret = \"your-secret-here-please\";\n",
        },
        "tracked": {
            ".gitignore": ".env\n",
            ".env": "SUPABASE_SERVICE_ROLE_KEY=%s\n" % SVC,
            "src/a.js": "export const a = 1;\n",
        },
    }


def write_fixture(root, name, files):
    base = os.path.join(root, name)
    os.makedirs(os.path.join(base, ".git"), exist_ok=True)  # pins the repo root to the fixture
    for rel, content in files.items():
        path = os.path.join(base, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    if name == "tracked":
        with open(os.path.join(base, ".git", "index"), "wb") as fh:
            fh.write(make_index([".env", ".gitignore", "src/a.js"]))
    return base


def run_audit(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = baas_audit.main(args)
    return code, out.getvalue()


def strict_json(text):
    def refuse(token):
        raise ValueError("non-standard JSON constant " + token)
    return json.loads(text, parse_constant=refuse)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--write":
        for name, files in fixtures().items():
            print(write_fixture(sys.argv[2], name, files))
        return 0
    expected = json.load(open(os.path.join(HERE, "fixtures", "expected.json"), encoding="utf-8"))
    failures, total = [], 0

    def check(label, ok, detail=""):
        nonlocal total
        total += 1
        print(("PASS " if ok else "FAIL ") + label + ("" if ok else "  " + detail))
        if not ok:
            failures.append(label)

    with tempfile.TemporaryDirectory() as tmp:
        for name, files in fixtures().items():
            base = write_fixture(tmp, name, files)
            code, text = run_audit([base])
            leaked = [i for i, s in enumerate(ALL_SECRETS) if s in text]
            try:
                report = strict_json(text)
            except ValueError as exc:
                check(name + ": strict JSON", False, str(exc))
                continue
            got = sorted(([f["category"], f["file"], f["line"], f["key"]] for f in report["findings"]), key=json.dumps)
            want = sorted(expected[name]["findings"], key=json.dumps)
            check(name + ": findings", got == want, "got %r wanted %r" % (got, want))
            check(name + ": verdict and exit", report["verdict"] == expected[name]["verdict"] and code == expected[name]["exit"],
                  "verdict %s exit %s" % (report["verdict"], code))
            check(name + ": no secret value in output", not leaked, "leaked secret index %r" % leaked)
        # usage and options
        bad_env = os.path.join(tmp, "bad_env")
        check("fail-on never exits 0", run_audit([bad_env, "--fail-on", "never"])[0] == 0)
        check("fail-on critical on drift exits 0", run_audit([os.path.join(tmp, "drift"), "--fail-on", "critical"])[0] == 0)
        check("fail-on medium on drift exits 1", run_audit([os.path.join(tmp, "drift"), "--fail-on", "medium"])[0] == 1)
        check("tracked index parsed", strict_json(run_audit([os.path.join(tmp, "tracked")])[1])["git"]["index_readable"] is True)
        check("missing folder exits 2", run_audit([os.path.join(tmp, "nope")])[0] == 2)
        check("no argument exits 2", run_audit([])[0] == 2)
    print("%d/%d checks passed" % (total - len(failures), total))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
