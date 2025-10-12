"""
Claude Code CLI Interaction Module

This module provides functions to execute Claude Code CLI commands
and parse their responses for use in the AI Developer Workflow.
"""

import json
import logging
import os
import subprocess
import sys
from typing import Optional, List, Tuple

from sdlc.lib.models import AgentPromptResponse


def check_claude_installed() -> bool:
    """Check if Claude Code CLI is installed and available.

    Returns:
        bool: True if Claude CLI is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def execute_claude_command(
    command: List[str],
    adw_id: str,
    agent_name: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    timeout: int = 600,
) -> Tuple[bool, str, Optional[str]]:
    """Execute a Claude Code CLI command and capture output.

    Args:
        command: The full command to execute (e.g., ["claude", "--print", "--model", "sonnet", "prompt"])
        adw_id: The ADW workflow ID for tracking
        agent_name: Optional agent name for organizing JSONL logs (e.g., "classify", "branch", "plan")
        logger: Optional logger instance
        timeout: Command timeout in seconds (default: 600)

    Returns:
        Tuple[bool, str, Optional[str]]: (success, output, session_id)
    """
    if logger:
        logger.debug(f"Executing Claude command: {' '.join(command)}")

    # Add --output-format stream-json to get JSONL output
    # This requires --verbose when used with --print
    if "--output-format" not in command:
        # Find position to insert (after --print, before the prompt)
        insert_pos = command.index("--print") + 1 if "--print" in command else 1
        command.insert(insert_pos, "--verbose")
        command.insert(insert_pos + 1, "--output-format")
        command.insert(insert_pos + 2, "stream-json")

    try:
        # Set up JSONL file if agent_name is provided
        jsonl_file_handle = None
        agent_dir = None

        if agent_name:
            agent_dir = os.path.join("agents", adw_id, agent_name)
            os.makedirs(agent_dir, exist_ok=True)
            # Create a temp file that we'll rename once we get the session_id
            temp_jsonl = os.path.join(agent_dir, "streaming.jsonl")
            jsonl_file_handle = open(temp_jsonl, 'w')
            if logger:
                logger.debug(f"Streaming JSONL to: {temp_jsonl}")

        # Execute the command with streaming output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )

        # Stream output line by line
        session_id = None
        output_text = ""
        all_lines = []

        if logger:
            logger.debug("Streaming Claude output...")

        for line in process.stdout:
            all_lines.append(line)

            # Write to JSONL file immediately
            if jsonl_file_handle:
                jsonl_file_handle.write(line)
                jsonl_file_handle.flush()  # Ensure it's written immediately

            # Try to parse each line for session_id and result
            try:
                data = json.loads(line.strip())
                if 'session_id' in data:
                    session_id = data.get('session_id')
                if 'result' in data:
                    output_text = data.get('result', output_text)

                # Log JSONL events at debug level
                if logger and data.get('type'):
                    event_type = data.get('type')
                    if event_type == 'result':
                        logger.debug(f"Claude session completed: {session_id}")
                    elif event_type == 'tool_use':
                        tool_name = data.get('content', {}).get('name', 'unknown')
                        logger.debug(f"Tool use: {tool_name}")
            except json.JSONDecodeError:
                # Not JSON, skip
                pass

        # Wait for process to complete
        process.wait(timeout=timeout)

        # Close JSONL file handle
        if jsonl_file_handle:
            jsonl_file_handle.close()

            # Rename temp file to include session_id
            if session_id:
                final_jsonl = os.path.join(agent_dir, f"{session_id}.jsonl")
                os.rename(temp_jsonl, final_jsonl)
                if logger:
                    logger.debug(f"Saved JSONL output to: {final_jsonl}")

        # Check return code
        if process.returncode != 0:
            stderr = process.stderr.read() if process.stderr else ""
            error_msg = f"Claude command failed with code {process.returncode}: {stderr}"
            if logger:
                logger.error(error_msg)
            return False, error_msg, None

        if logger:
            logger.debug(f"Command succeeded. Session ID: {session_id}")
            logger.debug(f"Output length: {len(output_text)} chars")

        return True, output_text, session_id

    except subprocess.TimeoutExpired:
        error_msg = f"Claude command timed out after {timeout} seconds"
        if logger:
            logger.error(error_msg)
        return False, error_msg, None
    except Exception as e:
        error_msg = f"Error executing Claude command: {str(e)}"
        if logger:
            logger.error(error_msg)
        return False, error_msg, None


def execute_slash_command(
    slash_command: str,
    args: List[str],
    adw_id: str,
    model: str = "sonnet",
    agent_name: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> AgentPromptResponse:
    """Execute a Claude Code slash command.

    Args:
        slash_command: The slash command to execute (e.g., "/feature", "/implement")
        args: Arguments to pass to the slash command
        adw_id: The ADW workflow ID
        model: Claude model to use ("sonnet" or "opus")
        agent_name: Optional agent name for organizing JSONL logs
        logger: Optional logger instance

    Returns:
        AgentPromptResponse: Response containing output and success status
    """
    # Build the command
    # Format: claude --print --model <model> "<slash_command> <args>"
    prompt = f"{slash_command} {' '.join(args)}"

    command = [
        "claude",
        "--print",
        "--model", model,
        "--dangerously-skip-permissions",  # Skip approval prompts for automated execution
        prompt,
    ]

    if logger:
        logger.debug(f"Full command: {' '.join(command)}")
        logger.debug(f"Args: {args}")

    # Use slash command name (without /) as agent name if not provided
    if not agent_name:
        agent_name = slash_command.lstrip('/').replace(':', '_')

    success, output, session_id = execute_claude_command(
        command=command,
        adw_id=adw_id,
        agent_name=agent_name,
        logger=logger
    )

    if logger:
        logger.debug(f"Response success: {success}")
        logger.debug(f"Response session_id: {session_id}")
        logger.debug(f"Response output (first 500 chars): {output[:500]}...")

    return AgentPromptResponse(
        output=output,
        success=success,
        session_id=session_id
    )


def execute_prompt(
    prompt: str,
    adw_id: str,
    model: str = "sonnet",
    session_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> AgentPromptResponse:
    """Execute a direct prompt with Claude Code.

    Args:
        prompt: The prompt to send to Claude
        adw_id: The ADW workflow ID
        model: Claude model to use ("sonnet" or "opus")
        session_id: Optional session ID for multi-turn conversations
        agent_name: Optional agent name for organizing JSONL logs
        logger: Optional logger instance

    Returns:
        AgentPromptResponse: Response containing output and success status
    """
    command = [
        "claude",
        "--print",
        "--model", model,
        "--dangerously-skip-permissions",  # Skip approval prompts for automated execution
    ]

    # Add session ID if provided for multi-turn
    if session_id:
        command.extend(["--resume", session_id])

    # Add prompt as the last positional argument
    command.append(prompt)

    if logger:
        logger.info("Executing Claude prompt")
        logger.debug(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else prompt)

    success, output, new_session_id = execute_claude_command(
        command=command,
        adw_id=adw_id,
        agent_name=agent_name or "prompt",
        logger=logger
    )

    return AgentPromptResponse(
        output=output,
        success=success,
        session_id=new_session_id or session_id
    )


def check_slash_command_exists(slash_command: str) -> bool:
    """Check if a slash command exists in the Claude Code configuration.

    This function uses Claude CLI's actual command resolution rather than
    checking for file existence, which ensures we only use commands that
    Claude Code actually recognizes.

    Args:
        slash_command: The slash command to check (e.g., "/feature")

    Returns:
        bool: True if the command exists, False otherwise
    """
    # For now, always return False for base commands to force SDLC plugin usage
    # This ensures consistent behavior across different repositories
    if not slash_command.startswith('/sdlc:'):
        return False

    # Check if SDLC plugin command file exists
    command_name = slash_command.replace('/sdlc:', '')

    # Check in the installed SDLC plugin location
    # The plugin files are in the claude-sdlc repo, not the current directory
    import pathlib
    sdlc_root = pathlib.Path(__file__).parent.parent.parent  # Go up to claude-sdlc root
    command_file = sdlc_root / 'plugins' / 'sdlc' / 'commands' / f'{command_name}.md'

    return command_file.exists()


def resolve_slash_command(base_command: str) -> str:
    """Resolve a slash command, checking for user-defined first, then falling back to SDLC plugin.

    Args:
        base_command: The base command (e.g., "/feature", "/bug", "/chore")

    Returns:
        str: The resolved command (either base_command or /sdlc:<command>)
    """
    # Check if user-defined command exists
    if check_slash_command_exists(base_command):
        return base_command

    # Fall back to SDLC plugin command
    command_name = base_command.lstrip('/')
    sdlc_command = f"/sdlc:{command_name}"

    # Verify the plugin command exists
    if check_slash_command_exists(sdlc_command):
        return sdlc_command

    # If neither exists, return the original (will likely fail, but let it fail gracefully)
    return base_command
