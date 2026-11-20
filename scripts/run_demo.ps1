$ErrorActionPreference = "Stop"

$env:DEEPTRACE_ENV = "development"
$env:DEEPTRACE_MODEL_PROVIDER = "deterministic"
$env:SEARCH_PROVIDER = "demo-correction"
$env:DEEPTRACE_MEMORY_BACKEND = "filesystem"
$env:DEEPTRACE_MEMORY_DIR = ".deeptrace-memory"
$env:DEEPTRACE_CHECKPOINT_BACKEND = "sqlite"
$env:DEEPTRACE_SQLITE_PATH = ".deeptrace-checkpoints.sqlite"
$env:DEEPTRACE_RATE_LIMIT_PER_MINUTE = "30"

& .\.venv\Scripts\python.exe main.py
