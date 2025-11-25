"""
SDLC - Software Development Lifecycle Commands

A unified CLI tool for development workflow automation.
"""

import click
from sdlc.commands.health import health
from sdlc.commands.watcher import watcher
from sdlc.commands.gitlab_watcher import gitlab_watcher


@click.group()
@click.version_option(version="0.1.0", prog_name="sdlc")
def main():
    """SDLC - Software Development Lifecycle Commands.

    A unified CLI tool for development workflow automation including:

    \b
    - System health checks
    - GitHub operations
    - Development environment management
    - And more...

    Run 'sdlc COMMAND --help' for more information on a specific command.
    """
    pass


# Register commands
main.add_command(health)
main.add_command(watcher)
main.add_command(gitlab_watcher)


if __name__ == "__main__":
    main()
