"""Explicit API/worker cloud launcher. Use --check-config without binding or I/O."""
from cloud_runtime import main

if __name__ == '__main__':
    raise SystemExit(main())
