
# yt-dlp Impersonation Tester

A command-line tool that discovers and tests the browser impersonation profiles supported by your installed [yt-dlp](https://github.com/yt-dlp/yt-dlp) version.

It helps identify which impersonation profiles can successfully extract metadata from a given media URL.

The tool works with any URL supported by yt-dlp. It is not limited to Rumble.

**Repository:** https://github.com/zaynkhan100110/ytdlp-impersonate-test

---

## Features

- **Automatic profile discovery** — reads the profiles available from your installed yt-dlp.
- **Any supported URL** — test Rumble, YouTube, Vimeo, Reddit, Bilibili, and other yt-dlp-supported sites.
- **Browser cookies** — optionally test with cookies extracted from a supported browser.
- **Proxy support** — optionally route requests through a proxy supported by yt-dlp.
- **Individual profile testing** — test one or more selected profiles.
- **Profile file support** — load a custom list of profiles from a text file.
- **Configurable delay** — control the pause between requests.
- **Configurable timeout** — limit how long each profile test can run.
- **Progress saving** — reports are updated after each test.
- **Resume support** — continue an interrupted test without repeating completed profiles.
- **Multiple report formats** — JSON, CSV, working profiles, and failed profiles.
- **Useful error classification** — distinguish HTTP 403, HTTP 429, authentication failures, timeouts, and other errors.

## How it works

The tool performs the following steps:

1. Locates the yt-dlp executable.
2. Runs `yt-dlp --list-impersonate`.
3. Discovers the impersonation profiles available in the installed build.
4. Tests each selected profile against the supplied URL.
5. Uses yt-dlp metadata extraction without downloading the media.
6. Classifies the result.
7. Saves the results to the output directory.

The default test uses:

```bash
yt-dlp \
  --ignore-config \
  --no-warnings \
  --no-progress \
  --skip-download \
  --dump-single-json \
  --impersonate "PROFILE" \
  "MEDIA_URL"
```

This is a metadata extraction test, not a full media download test.

---

## Requirements

### Required

| Requirement | Description |
|---|---|
| Python | Python 3.10 or newer |
| yt-dlp | Installed and accessible |
| curl_cffi | Required for the curl_cffi impersonation profiles |
| Internet connection | Required to contact the media website |

The impersonation profiles depend on the curl_cffi support and versions available to your installed yt-dlp.

### Optional

| Component | Purpose |
|---|---|
| Firefox | Browser cookie extraction |
| Chrome / Chromium | Browser cookie extraction |
| Other supported browsers | Browser cookie extraction |
| Proxy | Test through another network route |

Not every browser or operating system supports every cookie extraction method.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/zaynkhan100110/ytdlp-impersonate-test.git
cd ytdlp-impersonate-test
```

### 2. Create a virtual environment

Linux and macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Install Python dependencies

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install yt-dlp with impersonation support:

```bash
python -m pip install -U "yt-dlp[default,curl-cffi]"
```

The script itself uses only Python standard-library modules. yt-dlp and its curl_cffi support provide the actual extraction and impersonation functionality.

### 4. Verify installation

```bash
yt-dlp --version
yt-dlp --list-impersonate
```

If profiles are listed, your yt-dlp installation has impersonation targets available.

---

## Usage

### Basic test

```bash
python impersonate_test.py --url "https://example.com/video"
```

The tool automatically discovers and tests all profiles supported by your installed yt-dlp.

### Test a Rumble URL

```bash
python impersonate_test.py \
  --url "https://rumble.com/v7hv80u-example.html"
```

### Test a YouTube URL

```bash
python impersonate_test.py \
  --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Test with Firefox cookies

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --browser firefox
```

### Test with Chrome cookies

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --browser chrome
```

The browser must be installed and its cookie database must be accessible to yt-dlp.

### Use a proxy

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --proxy "http://127.0.0.1:8080"
```

For an authenticated proxy:

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --proxy "http://username:password@127.0.0.1:8080"
```

Be careful when placing credentials in command-line arguments. They may be visible in shell history or process listings.

### Change the delay

Default delay is two seconds.

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --delay 5
```

### Change the timeout

Default timeout is 40 seconds per profile.

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --timeout 60
```

### Limit the number of profiles

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --max-profiles 10
```

### Test a specific profile

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --profile "Safari-18.4:Macos-15"
```

### Test multiple specific profiles

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --profile "Safari-18.4:Macos-15" \
  --profile "Chrome-152:Windows-10" \
  --profile "Firefox-153:Windows-10"
```

Profiles must be available in the installed yt-dlp version.

### List available profiles

```bash
python impersonate_test.py --list-profiles
```

This lists profiles without contacting the media website.

### Use a custom yt-dlp executable

Linux:

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --yt-dlp "/home/user/project/.venv/bin/yt-dlp"
```

Windows:

```powershell
python impersonate_test.py `
  --url "https://example.com/video" `
  --yt-dlp ".venv\Scripts\yt-dlp.exe"
```

### Load profiles from a file

Create `profiles.txt`:

```text
Safari-18.4:Macos-15
Safari-17.2:Ios-17.2
Chrome-152:Windows-10
Chrome-131:Macos-14
```

Run:

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --profiles-file profiles.txt
```

Lines beginning with `#` and blank lines are ignored.

### Resume an interrupted test

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --resume
```

The tool reads previous results from the selected output directory and skips profiles already recorded there.

Use a separate output directory for each URL to avoid mixing test results.

---

## Command-line options

| Option | Description | Default |
|---|---|---|
| `-u`, `--url` | Media URL to test | Required |
| `--yt-dlp` | yt-dlp executable path | Auto-detected |
| `--browser` | Browser cookie source | None |
| `--proxy` | Proxy URL | None |
| `--delay` | Delay between profile tests | `2` seconds |
| `--timeout` | Timeout per profile | `40` seconds |
| `--output` | Report directory | `impersonate-results` |
| `--profile` | Specific profile; repeatable | All discovered |
| `--profiles-file` | File containing profiles | None |
| `--list-profiles` | List profiles and exit | Disabled |
| `--resume` | Skip profiles already recorded | Disabled |
| `--no-resume` | Start a fresh run | Disabled |
| `--max-profiles` | Maximum number to test | All selected |

Show all available options:

```bash
python impersonate_test.py --help
```

---

## Results

The default output directory is:

```text
impersonate-results/
```

The tool generates four files:

```text
impersonate-results/
├── results.json
├── results.csv
├── working_profiles.txt
└── failed_profiles.txt
```

### results.json

Contains:

- Test URL
- yt-dlp executable
- Cookie source name, if configured
- Whether a proxy was configured
- Summary counts
- Every profile's result
- Extraction title and extractor
- Number of available formats
- Duration of each test
- Error details

### results.csv

A spreadsheet-friendly version of the results.

### working_profiles.txt

Contains only profiles for which metadata extraction succeeded.

Example:

```text
Safari-18.4:Macos-15
Chrome-152:Windows-10
```

### failed_profiles.txt

Contains failed profiles, their result classifications, and error messages.

Example:

```text
Chrome-133:Macos-15 | BLOCKED_403 | HTTP Error 403: Forbidden
Safari-26.0:Ios-26.0 | FAILED | HTTP Error 400: Bad Request
```

---

## Result classifications

| Status | Meaning |
|---|---|
| `WORKING` | Metadata extraction succeeded |
| `BLOCKED_403` | Website returned HTTP 403 |
| `RATE_LIMITED_429` | Website returned HTTP 429 |
| `UNAUTHORIZED_401` | Website returned HTTP 401 |
| `NOT_FOUND_404` | Website returned HTTP 404 |
| `AUTH_REQUIRED` | Error indicates login or authentication is required |
| `UNSUPPORTED_URL` | yt-dlp does not recognize the URL |
| `TIMEOUT` | Profile test exceeded the configured timeout |
| `INVALID_JSON` | yt-dlp did not return valid JSON |
| `FAILED` | Another extraction error occurred |

A successful profile means that yt-dlp extracted metadata. It does not guarantee that the selected media formats can be downloaded.

---

## Understanding HTTP 403

HTTP 403 means the server refused the request.

Possible causes include:

- IP address or network reputation restrictions.
- VPN or proxy exit IP restrictions.
- Browser fingerprint restrictions.
- Missing or invalid cookies.
- Geographic restrictions.
- Website anti-bot protection.
- Temporary server-side restrictions.

Changing the impersonation profile may help in some situations, but it cannot guarantee access.

### VPN testing

You can run the same command with your normal network and with a VPN connection.

For example:

```bash
python impersonate_test.py \
  --url "https://rumble.com/example.html" \
  --output results-normal-network
```

Then, after changing your network connection:

```bash
python impersonate_test.py \
  --url "https://rumble.com/example.html" \
  --output results-vpn
```

Compare the generated reports.

Use reasonable delays and avoid repeatedly sending large batches of requests if the website is returning rate-limit or access-denied responses.

---

## Important limitations

1. The default test only extracts metadata.
2. It does not download the complete video.
3. It does not guarantee that every returned format is playable or downloadable.
4. A working profile can stop working if a website changes its protection.
5. Results depend on the installed yt-dlp version, curl_cffi version, network, IP address, cookies, and website behavior.
6. A profile working on one network does not mean it will work on another.
7. The tool does not bypass account restrictions, subscriptions, DRM, or other access controls.
8. Cookie extraction depends on browser support and operating-system permissions.

---

## Security and privacy

- Browser cookies can contain active login sessions.
- Do not share cookie databases or cookie exports.
- Do not commit credentials, cookies, or private proxy URLs to Git.
- Use trusted proxies only.
- Reports may contain media titles and URLs. Review them before publishing.
- The tool does not intentionally write browser cookie values into its reports.

---

## Troubleshooting

### No impersonation profiles are listed

Install yt-dlp with curl_cffi support:

```bash
python -m pip install -U "yt-dlp[default,curl-cffi]"
```

Then check:

```bash
yt-dlp --list-impersonate
```

### yt-dlp is not found

Pass the executable explicitly:

```bash
python impersonate_test.py \
  --url "https://example.com/video" \
  --yt-dlp "/path/to/yt-dlp"
```

### All profiles return HTTP 403

Try checking the same URL using a different network connection, and compare the results. This can help distinguish a profile issue from an IP or network restriction.

### Browser cookies cannot be extracted

Make sure the browser is installed, its profile is accessible, and it is not preventing access to its cookie database.

Try closing the browser before running the test.

### A profile returns HTTP 400

That profile may be incompatible with the website or may produce a request the website rejects.

### A profile works but the download fails

Metadata extraction and media delivery are separate requests. The media CDN may reject the download even when the webpage extraction succeeds.

---

## Development

The project uses Python's standard library for:

- Command-line parsing
- Process execution
- JSON and CSV reports
- File handling
- Timing and progress tracking

yt-dlp performs the actual media extraction.

Run:

```bash
python -m py_compile impersonate_test.py
python impersonate_test.py --help
```

---

## Contributing

Contributions, bug reports, and improvements are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test your changes.
5. Submit a pull request.

Please include your Python version, operating system, yt-dlp version, and a sanitized error message when reporting issues.

Do not include browser cookies, passwords, authentication tokens, or private proxy credentials.

---

## License

This project is released under the MIT License.

See [LICENSE](LICENSE) for details.

---

## Author

**Repository:** [zaynkhan100110/ytdlp-impersonate-test](https://github.com/zaynkhan100110/ytdlp-impersonate-test)

