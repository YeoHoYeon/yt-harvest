"""PyInstaller 진입점. 모듈 import 처리 안정화."""
from src.main import main
import sys

sys.exit(main())
