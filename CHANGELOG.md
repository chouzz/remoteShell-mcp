# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-11-13

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

