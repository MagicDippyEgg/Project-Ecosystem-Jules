#!/usr/bin/env python3
"""Entry point for Project Ecosystem: Artificial Life Simulation native desktop application."""
import sys
from ecosystem.app import EcosystemApp

def main():
    app = EcosystemApp(width=1200, height=800)
    app.run()

if __name__ == "__main__":
    main()
