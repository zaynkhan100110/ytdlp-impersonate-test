
#!/usr/bin/env python3
"""
yt-dlp Impersonation Tester

Discover and test curl_cffi impersonation profiles supported by yt-dlp.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_ytdlp(explicit_path: str | None) -> str:
    """Find the yt-dlp executable."""
    if explicit_path:
        path = shutil.which(explicit_path) or explicit_path
        if Path(path).is_file():
            return str(Path(path).resolve())
        raise SystemExit(f"yt-dlp executable not found: {explicit_path}")

    candidates = [
        Path(sys.executable).parent / "yt-dlp",
        Path(sys.executable).parent / "yt-dlp.exe",
        Path(sys.executable).parent.parent / "Scripts" / "yt-dlp.exe",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    discovered = shutil.which("yt-dlp")
    if discovered:
        return discovered

    raise SystemExit(
        "yt-dlp was not found. Install it or pass --yt-dlp /path/to/yt-dlp."
    )


def run_command(
    command: list[str],
    timeout: int,
) -> subprocess.CompletedProcess[str] | None:
    """Run a command without raising on non-zero exit codes."""
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None


def discover_profiles(ytdlp: str, timeout: int) -> list[str]:
    """Read the profiles advertised by yt-dlp --list-impersonate."""
    result = run_command(
        [ytdlp, "--list-impersonate"],
        timeout=timeout,
    )

    if result is None:
        raise RuntimeError("Timed out while discovering impersonation profiles.")

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "Could not list impersonation profiles."
        )

    profiles: list[str] = []

    for line in result.stdout.splitlines():
        columns = line.split()

        # Ignore the table header and separator.
        if len(columns) >= 3 and columns[2].lower() == "curl_cffi":
            profile = f"{columns[0]}:{columns[1]}"
            if profile not in profiles:
                profiles.append(profile)

    return profiles


def classify_failure(output: str) -> str:
    """Classify common HTTP and extraction failures."""
    text = output.lower()

    if "http error 403" in text or "403: forbidden" in text:
        return "BLOCKED_403"

    if "http error 429" in text or "429: too many requests" in text:
        return "RATE_LIMITED_429"

    if "http error 401" in text or "401: unauthorized" in text:
        return "UNAUTHORIZED_401"

    if "http error 404" in text or "404: not found" in text:
        return "NOT_FOUND_404"

    if "unsupported url" in text:
        return "UNSUPPORTED_URL"

    if "sign in" in text or "login required" in text:
        return "AUTH_REQUIRED"

    return "FAILED"


def extract_error(result: subprocess.CompletedProcess[str]) -> str:
    """Return a useful, bounded error message."""
    output = (result.stderr or result.stdout or "").strip()
    lines = [line.strip() for line in output.splitlines() if line.strip()]

    if not lines:
        return "yt-dlp exited unsuccessfully without an error message."

    # yt-dlp's final ERROR line is generally the most useful.
    error_lines = [line for line in lines if "ERROR:" in line]
    message = error_lines[-1] if error_lines else lines[-1]

    return message[:1500]


def test_profile(
    ytdlp: str,
    url: str,
    profile: str,
    timeout: int,
    browser: str | None,
    proxy: str | None,
) -> dict[str, Any]:
    """Test one profile by asking yt-dlp to extract metadata only."""
    command = [
        ytdlp,
        "--ignore-config",
        "--no-warnings",
        "--no-progress",
        "--skip-download",
        "--dump-single-json",
        "--impersonate",
        profile,
    ]

    if browser:
        command.extend(["--cookies-from-browser", browser])

    if proxy:
        command.extend(["--proxy", proxy])

    command.append(url)

    started = time.monotonic()
    result = run_command(command, timeout=timeout)
    elapsed = round(time.monotonic() - started, 2)

    base: dict[str, Any] = {
        "profile": profile,
        "status": "",
        "http_status": None,
        "title": "",
        "extractor": "",
        "format_count": 0,
        "duration_seconds": elapsed,
        "details": "",
    }

    if result is None:
        base.update({
            "status": "TIMEOUT",
            "details": f"Timed out after {timeout} seconds.",
        })
        return base

    if result.returncode == 0:
        try:
            # --dump-single-json should return one JSON object.
            info = json.loads(result.stdout)

            base.update({
                "status": "WORKING",
                "title": info.get("title") or "",
                "extractor": info.get("extractor_key")
                    or info.get("extractor")
                    or "",
                "format_count": len(info.get("formats") or []),
                "details": "Metadata extraction succeeded.",
            })
            return base

        except json.JSONDecodeError:
            base.update({
                "status": "INVALID_JSON",
                "details": "yt-dlp succeeded but did not return valid JSON.",
            })
            return base

    error = extract_error(result)
    status = classify_failure(error)

    base.update({
        "status": status,
        "details": error,
    })

    return base


def save_reports(
    results: list[dict[str, Any]],
    output_dir: Path,
    metadata: dict[str, Any],
) -> None:
    """Write JSON, CSV, and separate working/failed profile reports."""
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "metadata": metadata,
        "summary": {
            "total": len(results),
            "working": sum(r["status"] == "WORKING" for r in results),
            "failed": sum(r["status"] != "WORKING" for r in results),
        },
        "results": results,
    }

    (output_dir / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    fields = [
        "profile",
        "status",
        "http_status",
        "title",
        "extractor",
        "format_count",
        "duration_seconds",
        "details",
    ]

    with (output_dir / "results.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    working = [r for r in results if r["status"] == "WORKING"]
    failed = [r for r in results if r["status"] != "WORKING"]

    (output_dir / "working_profiles.txt").write_text(
        "\n".join(r["profile"] for r in working)
        + ("\n" if working else ""),
        encoding="utf-8",
    )

    (output_dir / "failed_profiles.txt").write_text(
        "\n".join(
            f'{r["profile"]} | {r["status"]} | {r["details"]}'
            for r in failed
        )
        + ("\n" if failed else ""),
        encoding="utf-8",
    )


def load_previous_results(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("results", [])
    except (OSError, json.JSONDecodeError, AttributeError):
        return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Discover and test yt-dlp impersonation profiles "
            "against any supported media URL."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-u", "--url",
        help="Media URL to test.",
    )
    parser.add_argument(
        "--yt-dlp",
        help="Path to the yt-dlp executable. Auto-detected by default.",
    )
    parser.add_argument(
        "--browser",
        help="Optional browser cookie source, e.g. firefox or chrome.",
    )
    parser.add_argument(
        "--proxy",
        help="Optional proxy URL accepted by yt-dlp.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait between profile tests.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=40,
        help="Maximum seconds allowed for each profile test.",
    )
    parser.add_argument(
        "--output",
        default="impersonate-results",
        help="Directory in which reports are saved.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        help="Test a specific profile. Can be supplied more than once.",
    )
    parser.add_argument(
        "--profiles-file",
        help="Text file containing profiles, one per line.",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit without testing a URL.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip profiles already present in the output results.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start a fresh run and replace existing reports.",
    )
    parser.add_argument(
        "--max-profiles",
        type=int,
        help="Test no more than this many profiles.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.delay < 0:
        raise SystemExit("--delay cannot be negative.")

    if args.timeout < 1:
        raise SystemExit("--timeout must be at least 1 second.")

    if args.max_profiles is not None and args.max_profiles < 1:
        raise SystemExit("--max-profiles must be at least 1.")

    ytdlp = find_ytdlp(args.yt_dlp)

    try:
        discovered = discover_profiles(ytdlp, args.timeout)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    if args.list_profiles:
        print(f"yt-dlp: {ytdlp}")
        print(f"Available impersonation profiles: {len(discovered)}")
        for profile in discovered:
            print(profile)
        return 0

    if not args.url:
        raise SystemExit("Provide a URL with --url, or use --list-profiles.")

    profiles = discovered

    if args.profiles_file:
        profile_file = Path(args.profiles_file)
        if not profile_file.is_file():
            raise SystemExit(f"Profiles file not found: {profile_file}")

        requested = [
            line.strip()
            for line in profile_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        profiles = requested

    if args.profile:
        profiles = args.profile

    # Remove duplicates but preserve the user's order.
    profiles = list(dict.fromkeys(profiles))

    if not profiles:
        raise SystemExit("No impersonation profiles were selected.")

    unknown = [p for p in profiles if p not in discovered]
    if unknown:
        print(
            "Warning: these profiles are not listed by this yt-dlp build: "
            + ", ".join(unknown),
            file=sys.stderr,
        )

    if args.max_profiles:
        profiles = profiles[:args.max_profiles]

    output_dir = Path(args.output)
    results_path = output_dir / "results.json"

    results: list[dict[str, Any]] = []
    completed: set[str] = set()

    if args.resume and not args.no_resume:
        results = load_previous_results(results_path)
        completed = {r.get("profile") for r in results}

    metadata = {
        "url": args.url,
        "yt_dlp": ytdlp,
        "browser_cookies": args.browser or None,
        "proxy_configured": bool(args.proxy),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    pending = [p for p in profiles if p not in completed]

    print(f"\nyt-dlp: {ytdlp}")
    print(f"URL: {args.url}")
    print(f"Profiles selected: {len(profiles)}")
    print(f"Profiles remaining: {len(pending)}")
    print(f"Cookie source: {args.browser or 'none'}")
    print(f"Proxy: {'configured' if args.proxy else 'none'}")
    print()

    try:
        for index, profile in enumerate(pending, 1):
            print(
                f"[{index}/{len(pending)}] {profile}: ",
                end="",
                flush=True,
            )

            result = test_profile(
                ytdlp=ytdlp,
                url=args.url,
                profile=profile,
                timeout=args.timeout,
                browser=args.browser,
                proxy=args.proxy,
            )

            results = [r for r in results if r.get("profile") != profile]
            results.append(result)

            print(
                f'{result["status"]} '
                f'({result["duration_seconds"]}s)'
            )

            if result["status"] == "WORKING":
                print(
                    f'    {result["format_count"]} formats | '
                    f'{result["title"][:100]}'
                )
            else:
                print(f'    {result["details"][:220]}')

            # Persist progress after every test.
            save_reports(results, output_dir, metadata)

            if index < len(pending):
                time.sleep(args.delay)

    except KeyboardInterrupt:
        print("\nInterrupted. Saving results collected so far.")

    save_reports(results, output_dir, metadata)

    working = [r for r in results if r["status"] == "WORKING"]
    failed = [r for r in results if r["status"] != "WORKING"]

    print("\n========== SUMMARY ==========")
    print(f"Results recorded: {len(results)}")
    print(f"Working:          {len(working)}")
    print(f"Not working:      {len(failed)}")
    print(f"Reports:          {output_dir.resolve()}")

    if working:
        print("\nWorking profiles:")
        for result in working:
            print(
                f'  {result["profile"]} '
                f'({result["format_count"]} formats)'
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
