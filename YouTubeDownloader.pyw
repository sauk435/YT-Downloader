import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui_main import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
