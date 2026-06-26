#!/usr/bin/env python
"""
Setup configuration for Nexora package.
This file demonstrates the build configuration and post-install hooks.
The actual configuration is in pyproject.toml - this is for reference.
"""

from setuptools import setup, find_packages

setup(
    name="nexora-prediction",
    version="0.1.1",
    description="Autonomous predictive analytics platform",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "nexora=nexora.cli.main:cli",
        ],
        # Post-install hook (runs after installation)
        "pip": [
            "post_install = nexora.post_install:print_installation_info",
        ],
    },
)
