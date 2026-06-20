# Release

## SmartStudy-Setup.exe

Windows installer: Docker pull (GHCR) → fallback ZIP build → or local repo copy.

### Build locally

```powershell
cd release
.\build.ps1
```

Outputs in `release/dist/`:
| File | Description |
|------|-------------|
| `SmartStudy-Setup-PS.exe` | **Recommended** — PowerShell, no PyInstaller |
| `SmartStudy-Setup.exe` | Python 3.12 onefile |
| `SmartStudy-Setup-Portable.zip` | Fallback if `PYI-16524` extraction error |

### PYI-16524 fix

If `SmartStudy-Setup.exe` fails with `Failed to extract unicodedata.pyd`:
- Use **`SmartStudy-Setup-PS.exe`** instead, or
- Extract **`SmartStudy-Setup-Portable.zip`** and run `SmartStudy-Setup-Portable.exe`

Cause: PyInstaller onefile + Python 3.14 or antivirus blocking temp extraction. Rebuild uses Python **3.12** and `--noupx`.

### Usage

```powershell
SmartStudy-Setup.exe                          # auto: pull or zip
SmartStudy-Setup.exe --local C:\path\to\repo  # no GitHub needed
SmartStudy-Setup.exe --build-only             # skip GHCR pull
SmartStudy-Setup.exe --pull-only              # only docker compose pull
SmartStudy-Setup.exe --base D:\SmartStudy     # custom install dir
```

### GitHub Release (CI)

Copy `scripts/ghcr-release.yml` → `.github/workflows/release.yml`, then:

```bash
git tag v1.0.0
git push origin v1.0.0
```

CI builds `SmartStudy-Setup.exe`, pushes Docker images to GHCR, creates GitHub Release.

Also copy `scripts/ghcr-docker-publish.yml` → `.github/workflows/docker-publish.yml` for image builds on every push to `main`.
