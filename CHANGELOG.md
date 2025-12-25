# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-12-25

### Added
- Optional `port` parameter to `save_server` tool for specifying custom SSH ports
- Port validation and storage support in host store configuration

### Changed
- Enhanced `save_server` tool to accept optional port parameter (defaults to 22)
- Updated host store to persist and manage port configuration for saved servers

## [1.1.0] - 2025-12-24

### Added
- Parameter descriptions for all MCP tools using pydantic Field annotations
- Enhanced tool metadata for better IDE/MCP client integration

### Changed
- Improved tool descriptions format:
  - Removed redundant "Purpose" prefix from all tool descriptions
  - Added proper paragraph separation with `\n\n` for better readability
  - Updated example formatting to use double quotes consistently
- Improved README formatting and clarity (#6)

## [1.0.0] - 2025-12-23

### Changed
- **Major refactor**: Completely redesigned MCP tool surface and persistence layer
- Moved configuration persistence from `~/.remoteShell/config.json` to `~/.config/remoteshell/hosts.json`
- Replaced 6 old tools with new streamlined set: `list_servers`, `save_server`, `remove_server`, `execute_command`, `upload_file`, `download_file`
- Added connection status caching with `last_connected` timestamp tracking
- Enhanced error messages with machine-readable error codes (e.g., `auth_failed`) for better LLM recovery
- Implemented automatic local path generation for file transfer tools when paths are omitted
- Simplified configuration to single `uvx` setup method
- Updated to use FastMCP 2.x features for richer tool descriptions and parameter validation

### Removed
- `create_connection`, `list_connections`, `close_connection` tools (replaced with new tool set)
- `--connections` CLI argument support
- Legacy configuration file path and format

## [0.1.0] - 2025-11-13

### Added
- Initial release of Remote Shell MCP Server
- SSH connection management with persistent connections
- Support for multiple authentication methods (password and SSH key)
- Six MCP tools:
  - `create_connection`: Create new SSH connections
  - `execute_command`: Execute commands on remote hosts
  - `upload_file`: Upload files to remote hosts
  - `download_file`: Download files from remote hosts
  - `list_connections`: List all available connections
  - `close_connection`: Close active connections
- Three configuration methods:
  - Global config file (`~/.remoteShell/config.json`)
  - MCP client configuration (Claude Code/Cursor)
  - Dynamic connection creation
- Cross-platform support using Paramiko
- Comprehensive documentation and examples
- Test suite for configuration loader
- Support for both Claude Code and Cursor

### Features
- Multi-connection support (manage multiple remote hosts simultaneously)
- Auto-reconnect on connection failure
- Independent command execution (no persistent working directory state)
- Secure credential handling
- File transfer with progress validation
- Detailed error messages and status reporting

### Documentation
- README with installation and configuration instructions
- Quick Start Guide for common tasks
- Example configuration file
- Usage examples for all tools
- Security best practices
- Troubleshooting guide
