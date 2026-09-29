"""Desktop notifications for moments the operator should look at the loop.

Under WSL the toast goes through Windows' own powershell.exe, whatever terminal the
loop runs in; elsewhere, and whenever the toast cannot be sent, the terminal bell is
all there is. Sending never blocks the loop and never raises.
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import threading
from typing import Callable
from xml.sax.saxutils import escape

# Toasts need a registered app id; PowerShell's is on every Windows install.
_APP_ID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
_SCRIPT = """\
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('{xml}')
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{app}').Show([Windows.UI.Notifications.ToastNotification]::new($xml))
"""


def toast_command(title: str, body: str, powershell: str = "powershell.exe") -> list[str]:
    """The powershell.exe invocation that shows one toast.

    -EncodedCommand (base64 UTF-16LE) because powershell.exe decodes piped stdin in the
    Windows code page, which garbles anything outside ASCII."""
    xml = ('<toast><visual><binding template="ToastGeneric">'
           f"<text>{escape(title)}</text><text>{escape(body)}</text>"
           "</binding></visual></toast>")
    # Inside a single-quoted PowerShell string the only special character is ' itself.
    script = _SCRIPT.format(xml=xml.replace("'", "''"), app=_APP_ID)
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return [powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]


class Notifier:
    def __init__(self, *, bell: Callable[[], None], enabled: bool = True,
                 powershell: str | None = None, run=subprocess.run) -> None:
        self._bell = bell
        self._enabled = enabled
        self._powershell = powershell if powershell is not None else shutil.which("powershell.exe")
        self._run = run
        self._threads: list[threading.Thread] = []

    def __call__(self, title: str, body: str) -> None:
        if not self._enabled:
            return
        self._bell()
        if not self._powershell:
            return
        # A thread rather than a bare Popen, so the child is reaped; it takes about half a second.
        thread = threading.Thread(target=self._send, daemon=True,
                                  args=(toast_command(title, body, self._powershell),))
        thread.start()
        self._threads = [t for t in self._threads if t.is_alive()] + [thread]

    def flush(self, timeout: float = 5.0) -> None:
        """Waits for toasts still being sent, so the last one survives the loop exiting."""
        for thread in self._threads:
            thread.join(timeout)

    def _send(self, argv: list[str]) -> None:
        try:
            self._run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL, timeout=30)
        except (OSError, subprocess.SubprocessError):
            self._powershell = None  # e.g. WSL interop disabled: stop trying, keep the bell
