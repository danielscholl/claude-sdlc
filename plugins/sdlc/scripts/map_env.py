#!/usr/bin/env -S uv run python
import os, sys, re, argparse, time, shutil, tempfile
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Populate .env from .env.sample using current shell env.")
    p.add_argument("sample", nargs="?", default=".env.sample")
    p.add_argument("target", nargs="?", default=".env")
    p.add_argument("--empty-missing", action="store_true", help="Write KEY= when missing instead of keeping placeholder.")
    p.add_argument("--force", action="store_true", help="Overwrite existing target without backup.")
    p.add_argument("--dry-run", action="store_true", help="Do not write files; only log actions.")
    return p.parse_args()

# Token synonyms (UPPERCASE)
SYN = {
    "DATABASE": ["DATABASE", "DB", "DATASOURCE"],
    "URL": ["URL", "URI", "ENDPOINT", "CONNECTION", "CONN"],
    "KEY": ["KEY", "TOKEN", "SECRET"],
    "PASSWORD": ["PASSWORD", "PASS", "SECRET", "TOKEN", "KEY"],
    "USER": ["USER", "USERNAME"],
    "OPENAI": ["OPENAI"],
    "ANTHROPIC": ["ANTHROPIC"],
    "API": ["API", "TOKEN", "KEY", "SECRET"],
}

def quote_value(val: str) -> str:
    if "\n" in val:
        raise ValueError("Refusing to write value containing newline(s).")
    # Allow simple unquoted values
    if re.fullmatch(r"[A-Za-z0-9_./:@-]+", val or ""):
        return val
    # Otherwise single-quote and escape
    return "'" + val.replace("'", r"'\''") + "'"

def parts_for_key(key_up: str):
    if key_up == "DATABASE_URL":
        return [["DATABASE","DB","DATASOURCE"], ["URL","URI","ENDPOINT","CONNECTION","CONN"]]
    parts = key_up.split("_")
    out = []
    for t in parts:
        out.append(SYN.get(t, [t]))
    return out

def find_source_for_key(key: str, env_names_up, env_names_orig):
    key_up = key.upper()

    # 1) exact match
    if key_up in env_names_up:
        idx = env_names_up.index(key_up)
        name = env_names_orig[idx]
        return name, os.environ.get(name)

    # 2) OPENAI_API_KEY / {PROVIDER}_API_KEY style fallbacks
    m = re.match(r"^(.+)_API_KEY$", key_up)
    if m:
        prefix = m.group(1)
        trylist = [f"{prefix}_API_KEY", f"{prefix}_KEY", f"{prefix}_TOKEN",
                   f"{prefix}_SECRET", f"{prefix}_API_TOKEN", f"{prefix}_API_SECRET"]
        for t in trylist:
            if t in env_names_up:
                idx = env_names_up.index(t)
                name = env_names_orig[idx]
                return name, os.environ.get(name)

    # 3) fuzzy token match: for each token group, at least one synonym appears in the name
    token_groups = parts_for_key(key_up)
    for idx, upname in enumerate(env_names_up):
        ok = True
        for group in token_groups:
            if not any(g in upname for g in group):
                ok = False
                break
        if ok:
            name = env_names_orig[idx]
            return name, os.environ.get(name)

    return None, None

def main():
    args = parse_args()
    sample = Path(args.sample)
    target = Path(args.target)

    if not sample.exists():
        print(f"Sample not found: {sample}", file=sys.stderr)
        sys.exit(1)

    # Build env name lists keeping original casing
    env_names_orig = list(os.environ.keys())
    env_names_up = [n.upper() for n in env_names_orig]

    mapped = []
    missing = []

    tmp = tempfile.NamedTemporaryFile("w", delete=False)
    tmp_path = Path(tmp.name)

    with sample.open() as f_in, tmp:
        for raw in f_in:
            line = raw.rstrip("\n")

            # Preserve blank and comment lines exactly
            if not line.strip() or line.lstrip().startswith("#"):
                tmp.write(line + "\n")
                continue

            m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$", line)
            if not m:
                tmp.write(line + "\n")
                continue

            key, rhs = m.group(1), m.group(2)
            src, val = find_source_for_key(key, env_names_up, env_names_orig)

            if src is not None and val is not None:
                try:
                    qv = quote_value(val)
                except ValueError as e:
                    print(f"ERROR for {key}: {e}", file=sys.stderr)
                    sys.exit(1)
                tmp.write(f"{key}={qv}\n")
                mapped.append((key, src))
            else:
                if args.empty_missing:
                    tmp.write(f"{key}=\n")
                else:
                    tmp.write(f"{key}={rhs}\n")  # keep placeholder
                missing.append(key)

    # Handle target writing
    if args.dry_run:
        print(f"[dry-run] Would write: {target}")
        if target.exists() and not args.force:
            print(f"[dry-run] Would create backup of existing {target}", file=sys.stderr)
        # Print summary without secrets
        print("\nSummary:")
        for k, s in mapped:
            print(f"  • Set {k} from ${s}")
        for k in missing:
            print(f"  • Missing {k} (kept placeholder or empty)")
        # Cleanup temp
        tmp_path.unlink(missing_ok=True)
        return

    if target.exists() and not args.force:
        ts = time.strftime("%Y%m%d-%H%M%S")
        backup = target.with_name(target.name + f".bak-{ts}")
        shutil.copy2(target, backup)
        print(f"Backup created: {backup}", file=sys.stderr)

    # Move temp into place
    tmp_path.replace(target)
    print(f"Wrote {target}")

    # Summary (no secrets)
    print("\nSummary:")
    for k, s in mapped:
        print(f"  • Set {k} from ${s}")
    for k in missing:
        print(f"  • Missing {k} (kept placeholder or empty)")

if __name__ == "__main__":
    main()