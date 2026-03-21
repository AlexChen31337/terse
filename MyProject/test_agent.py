#!/usr/bin/env python3
"""
test_agent.py - Basic OpenClaw Agent Setup
A simple agent script demonstrating basic agent structure and initialization.
"""

import sys
import os
from datetime import datetime


class BasicAgent:
    """A basic OpenClaw-style agent with minimal setup."""

    def __init__(self, name: str = "TestAgent"):
        self.name = name
        self.created_at = datetime.now().isoformat()
        self.state = "initialized"

    def setup(self):
        """Initialize the agent."""
        print(f"[{self.name}] Setting up agent...")
        self.state = "ready"
        return self

    def run(self):
        """Run the agent's main logic."""
        print(f"[{self.name}] Agent is running!")
        print(f"[{self.name}] Hello from MyProject! 🚀")
        print(f"[{self.name}] Created at: {self.created_at}")
        print(f"[{self.name}] State: {self.state}")
        print(f"[{self.name}] Python version: {sys.version.split()[0]}")
        print(f"[{self.name}] Working directory: {os.getcwd()}")
        self.state = "completed"
        return self

    def teardown(self):
        """Clean up after the agent finishes."""
        print(f"[{self.name}] Teardown complete. State: {self.state}")


def main():
    print("=" * 50)
    print("  OpenClaw Agent — MyProject Test Agent")
    print("=" * 50)

    agent = BasicAgent(name="MyProjectAgent")
    agent.setup()
    agent.run()
    agent.teardown()

    print("=" * 50)
    print("  Agent execution finished successfully ✅")
    print("=" * 50)


if __name__ == "__main__":
    main()
