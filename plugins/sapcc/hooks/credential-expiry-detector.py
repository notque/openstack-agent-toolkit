#!/usr/bin/env python3
"""PostToolUse hook: Detect expired credentials and inject re-auth guidance.

When any MCP tool call returns a 401 Unauthorized or auth-related error,
this hook injects context telling the agent to stop retrying and guide
the user to re-authenticate.

Without this hook, the LLM would retry the same call 2-3 times, waste
API calls on a dead token, and confuse the user with "something went wrong."

Exit codes:
  0 = always (PostToolUse hooks are advisory, never block)

Output:
  JSON with additionalContext when auth failure detected, empty otherwise.
"""
from __future__ import annotations

import json
import sys

# Patterns that indicate credential/auth failure
AUTH_FAILURE_PATTERNS = [
    "401",
    "unauthorized",
    "authentication required",
    "token expired",
    "invalid credentials",
    "could not authenticate",
    "auth_url",
    "keystoneauth",
    "re-authenticate",
    "credential",
]


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_result = data.get("tool_result", "")

    # Only care about MCP tool results
    if not tool_name or not tool_result:
        sys.exit(0)

    # Convert result to string for pattern matching
    result_str = str(tool_result).lower()

    # Check for auth failure patterns
    auth_failure = False
    for pattern in AUTH_FAILURE_PATTERNS:
        if pattern in result_str:
            auth_failure = True
            break

    if not auth_failure:
        # No auth issue — exit silently
        sys.exit(0)

    # Inject guidance
    guidance = {
        "additionalContext": (
            "[credential-expiry-detected] The MCP server returned an authentication error. "
            "STOP retrying the same call — the token is expired or invalid. "
            "Guide the user to re-authenticate:\n"
            "1. Check if OS_APPLICATION_CREDENTIAL_ID and OS_APPCRED_SECRET_CMD are set correctly\n"
            "2. Run the credential-setup skill to reconfigure auth\n"
            "3. Verify the keychain entry hasn't been cleared\n"
            "Do NOT retry API calls until credentials are refreshed."
        )
    }
    print(json.dumps(guidance))
    sys.exit(0)


if __name__ == "__main__":
    main()
