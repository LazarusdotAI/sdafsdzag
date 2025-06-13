import os
import subprocess
import sys
import time
import threading
import signal
import requests
from pathlib import Path

try:
    import webview  # pywebview provides a lightweight desktop window
except ImportError:
    print("pywebview not installed. Run: pip install pywebview[qt]")
    sys.exit(1)

HERE = Path(__file__).parent.resolve()


def run_subprocess(args: list[str], name: str):
    """Launch a subprocess that stays alive until parent exits."""
    print(f"Starting {name}...")
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=HERE)


def wait_for_service(url: str, timeout: int = 30):
    """Wait for a service to become available."""
    print(f"Waiting for {url} to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(f"✓ {url} is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    print(f"✗ {url} failed to start within {timeout} seconds")
    return False


def launch_proxy():
    # uvicorn main:app --port 8000 --host 127.0.0.1
    return run_subprocess([sys.executable, "-m", "uvicorn", "main:app", "--port", "8000", "--host", "127.0.0.1"], "FastAPI Proxy")


def launch_dashboard():
    # streamlit run dashboard.py --server.port 8501 --server.headless true
    return run_subprocess([
        sys.executable, "-m", "streamlit", "run", 
        str(HERE / "dashboard.py"), 
        "--server.port", "8501",
        "--server.headless", "true",
        "--server.address", "127.0.0.1"
    ], "Streamlit Dashboard")


def main():
    print("🚀 Starting ATLAS Trading Assistant...")
    
    # Ensure env vars are loaded from .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Environment variables loaded")
    except ImportError:
        print("⚠ python-dotenv not found, using system environment only")

    # Check required environment variables
    required_vars = ["OPENAI_API_KEY", "APCA_API_KEY_ID", "APCA_API_SECRET_KEY", "FMP_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"✗ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or system environment")
        input("Press Enter to exit...")
        return

    # Start services
    proxy_proc = launch_proxy()
    dash_proc = launch_dashboard()

    # Wait for services to be ready
    services_ready = True
    
    if not wait_for_service("http://127.0.0.1:8000/docs", 30):
        print("✗ FastAPI proxy failed to start")
        services_ready = False
    
    if not wait_for_service("http://127.0.0.1:8501", 30):
        print("✗ Streamlit dashboard failed to start")
        services_ready = False

    if not services_ready:
        print("\n💥 Services failed to start. Check error logs above.")
        input("Press Enter to exit...")
        cleanup_processes([proxy_proc, dash_proc])
        return

    def cleanup_processes(processes):
        print("🧹 Cleaning up processes...")
        for p in processes:
            try:
                if p.poll() is None:
                    p.terminate()
                    p.wait(5)
            except Exception as e:
                print(f"Error cleaning up process: {e}")

    # Set PROXY_URL for the dashboard
    os.environ["PROXY_URL"] = "http://127.0.0.1:8000"

    # Launch desktop window
    try:
        print("🖥️ Opening desktop window...")
        webview.create_window(
            "ATLAS Trading Assistant", 
            "http://127.0.0.1:8501", 
            width=1400, 
            height=900,
            resizable=True
        )
        webview.start(debug=False)
    except Exception as e:
        print(f"Error starting webview: {e}")
    finally:
        cleanup_processes([dash_proc, proxy_proc])


if __name__ == "__main__":
    main() 