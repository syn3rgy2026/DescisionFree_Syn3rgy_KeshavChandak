"""
main.py
-------
Entry point for Synergy Agent.
Launches the Textual TUI dashboard.
"""

from ui.app import SynergyAgentApp


def main():
    app = SynergyAgentApp()
    app.run()


if __name__ == "__main__":
    main()
