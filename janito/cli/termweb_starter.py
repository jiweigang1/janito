import sys
import subprocess
import tempfile
import time
import http.client
import os
import threading
import queue
from rich.console import Console
from janito.i18n import tr
from janito.cli.config import get_termweb_port


def wait_for_termweb(port, timeout=3.0):
    """Polls the Bottle app root endpoint until it responds or timeout (seconds) is reached."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = http.client.HTTPConnection("localhost", port, timeout=0.5)
            conn.request("GET", "/")
            resp = conn.getresponse()
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


def termweb_start_and_watch(shell_state, shellstate_lock, selected_port=None):
    """
    Start the termweb server on the given port in a background thread.
    Communicates (termweb_proc, started: bool, stdout_path, stderr_path) via result_queue if provided.
    Returns the Thread object.
    """

    def termweb_worker(shell_state, shellstate_lock, selected_port, check_interval=2.0):
        """
        Worker to start termweb process, then monitor its running state/health, and update shell_state fields in a thread-safe manner.
        - shell_state: context or state object to update (must provide .termweb_pid, .termweb_status, etc.)
        - shellstate_lock: a threading.Lock or similar to synchronize access
        """
        console = Console()
        # Try to locate app.py
        app_py_path = os.path.join(os.path.dirname(__file__), "..", "termweb", "app.py")
        app_py_path = os.path.abspath(app_py_path)
        if not os.path.isfile(app_py_path):
            try:
                import janito_termweb

                app_py_path = janito_termweb.__file__.replace("__init__.py", "app.py")
            except ImportError:
                with shellstate_lock:
                    shell_state.termweb_status = "notfound"
                    shell_state.termweb_pid = None
                    shell_state.termweb_stdout_path = None
                    shell_state.termweb_stderr_path = None
                return
        termweb_stdout = tempfile.NamedTemporaryFile(
            delete=False, mode="w+", encoding="utf-8"
        )
        termweb_stderr = tempfile.NamedTemporaryFile(
            delete=False, mode="w+", encoding="utf-8"
        )
        port_to_use = selected_port if selected_port is not None else get_termweb_port()
        termweb_proc = subprocess.Popen(
            [sys.executable, app_py_path, "--port", str(port_to_use)],
            stdout=termweb_stdout,
            stderr=termweb_stderr,
        )

        # Step 1: Wait for server to become healthy (initial check)
        if wait_for_termweb(port_to_use, timeout=3.0):
            with shellstate_lock:
                shell_state.termweb_status = "running"
                shell_state.termweb_pid = termweb_proc.pid
                shell_state.termweb_stdout_path = termweb_stdout.name
                shell_state.termweb_stderr_path = termweb_stderr.name
                shell_state.termweb_port = port_to_use
        else:
            termweb_proc.terminate()
            termweb_proc.wait()
            # console.print(f"[red]Failed to start TermWeb on port {port_to_use}. Check logs for details.[/red]")
            with shellstate_lock:
                shell_state.termweb_status = "failed-start"
                shell_state.termweb_pid = None
                shell_state.termweb_stdout_path = termweb_stdout.name
                shell_state.termweb_stderr_path = termweb_stderr.name
                shell_state.termweb_port = None
            return

        # Step 2: Run watcher loop; exit and set fields if process or health fails
        import time
        from http.client import HTTPConnection

        while True:
            if termweb_proc.poll() is not None:  # means process exited
                with shellstate_lock:
                    shell_state.termweb_status = "terminated"
                    shell_state.termweb_pid = None
                break
            try:
                conn = HTTPConnection("localhost", port_to_use, timeout=0.5)
                conn.request("GET", "/")
                resp = conn.getresponse()
                if resp.status != 200:
                    raise Exception("Bad status")
            except Exception:
                # console.print(f"[red]TermWeb on port {port_to_use} appears to have stopped responding![/red]")
                with shellstate_lock:
                    shell_state.termweb_status = "unresponsive"
                break
            time.sleep(check_interval)

    # Launch background thread
    t = threading.Thread(
        target=termweb_worker,
        args=(shell_state, shellstate_lock, selected_port),
        daemon=True,
    )
    t.start()
    return t
