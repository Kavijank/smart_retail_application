"""
SmartMart Retail Analytics Application - Main Desktop Launcher
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app_window import SmartMartApp


def main():
    print("=" * 70)
    print("SmartMart Retail Analytics Platform")
    print("Standalone Desktop-Based Data Processing & Analytics Engine")
    print("=" * 70)
    app = SmartMartApp()
    app.mainloop()


if __name__ == '__main__':
    main()
