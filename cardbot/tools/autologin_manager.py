"""Generates dynamic auto-login Chrome extensions for given accounts."""

import json
from pathlib import Path


def generate_autologin_extension(instance_id: int, account_line: str) -> str | None:
    """
    Parses 'user:pass', generates an auto-login Chrome extension for this instance,
    and returns its absolute directory path. Returns None if invalid format.
    """
    if not account_line or ":" not in account_line:
        return None

    try:
        username, password = account_line.split(":", 1)
        username = username.strip()
        password = password.strip()
    except ValueError:
        return None

    ext_dir = Path("cardbot/data/extensions") / f"instance_{instance_id}"
    ext_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "manifest_version": 3,
        "name": f"AutoLogin_{instance_id}",
        "version": "1.0",
        "description": "Injected Auto-Login for KingsCall",
        "content_scripts": [
            {
                "matches": ["*://*.xstargame.com/*"],
                "js": ["content.js"],
                "all_frames": True,
                "run_at": "document_idle"
            }
        ]
    }

    # Injectable JS: Looks for inputs, fills credentials, and clicks login randomly delayed
    # Note: Using setTimeouts to let Wancms SDK dynamically load its wrappers
    content_js = f"""
    (function autoLogin() {{
        const injectCredentials = () => {{
            let uInput = document.querySelector('input[type="text"], input[name="username"], input[placeholder*="账号"]');
            let pInput = document.querySelector('input[type="password"]');

            if (uInput && pInput) {{
                console.log("[AutoLogin] Found login fields! Injecting credentials.");
                uInput.value = "{username}";
                pInput.value = "{password}";
                
                // Dispatch input events so React/Vue/Wancms SDK registers the value change
                uInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                pInput.dispatchEvent(new Event('input', {{ bubbles: true }}));

                setTimeout(() => {{
                    let btn = document.querySelector('.login-btn, button[type="submit"], .btn-login');
                    if (btn) {{
                        console.log("[AutoLogin] Clicking login button.");
                        btn.click();
                    }}
                }}, 500);
            }}
        }};

        // Try injecting every second for up to 10 seconds to catch deferred IFRAME/DOM loads
        let attempts = 0;
        let iv = setInterval(() => {{
            if (attempts++ > 15) clearInterval(iv);
            injectCredentials();
        }}, 1000);
    }})();
    """

    (ext_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ext_dir / "content.js").write_text(content_js, encoding="utf-8")

    return str(ext_dir.absolute())

