# Remote Plugin Repository Guide

Janito supports loading plugins from remote repositories, specifically from the official `ikignosis/janito-plugins` repository on GitHub.

## Overview

The `ikignosis/janito-plugins` repository serves as a centralized location for community-contributed and official plugins that extend janito's functionality. This allows users to access a curated collection of plugins without manually downloading or managing individual plugin files.

## Repository Location

- **GitHub URL**: https://github.com/ikignosis/janito-plugins
- **Git URL**: `https://github.com/ikignosis/janito-plugins.git`
- **SSH URL**: `git@github.com:ikignosis/janito-plugins.git`

## Available Plugins

The remote repository contains various plugin categories:

- **Data Analysis**: Plugins for statistical analysis, data visualization, and dataset manipulation
- **Development Tools**: Code quality checkers, formatters, and development workflow tools
- **API Integrations**: Connectors for popular services (GitHub, AWS, Google Cloud, etc.)
- **File Operations**: Enhanced file management and processing capabilities
- **System Utilities**: System monitoring, process management, and diagnostic tools

## Usage

### Automatic Loading

Janito can automatically discover and load plugins from the remote repository when configured:

```json
{
  "plugins": {
    "remote": {
      "enabled": true,
      "repository": "https://github.com/ikignosis/janito-plugins.git",
      "branch": "main",
      "auto_update": true
    }
  }
}
```

### Manual Installation

To manually install plugins from the remote repository:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ikignosis/janito-plugins.git ~/.janito/remote-plugins/
   ```

2. **Enable specific plugins**:
   ```json
   {
     "plugins": {
       "paths": ["~/.janito/remote-plugins/plugins"],
       "load": {
         "github_tools": true,
         "data_analyzer": {"verbose": true}
       }
     }
   }
   ```

### Plugin Discovery

List available remote plugins:

```bash
# List all available plugins from remote repository
janito --list-remote-plugins

# Show plugin details
janito --plugin-info github_tools
```

## Plugin Categories

### Official Plugins

Maintained by the janito core team:

- `github_tools`: GitHub repository management and PR tools
- `aws_tools`: AWS resource management and deployment helpers
- `data_analyzer`: Statistical analysis and data processing tools
- `docker_tools`: Container management and orchestration utilities

### Community Plugins

Contributed by the janito community:

- `slack_notifier`: Slack integration for notifications
- `excel_processor`: Advanced Excel file operations
- `json_validator`: JSON schema validation and formatting
- `system_monitor`: Real-time system resource monitoring

## Configuration

### Remote Repository Settings

```json
{
  "plugins": {
    "remote": {
      "enabled": true,
      "repository": "https://github.com/ikignosis/janito-plugins.git",
      "branch": "main",
      "local_path": "~/.janito/remote-plugins",
      "auto_update": true,
      "update_interval": "24h"
    }
  }
}
```

### Plugin-Specific Configuration

Each remote plugin can be configured individually:

```json
{
  "plugins": {
    "load": {
      "github_tools": {
        "token": "ghp_your_github_token",
        "default_repo": "user/repo"
      },
      "aws_tools": {
        "region": "us-east-1",
        "profile": "default"
      }
    }
  }
}
```

## Security Considerations

- **Repository Verification**: Plugins are sourced from the official `ikignosis` organization
- **Code Review**: All plugins undergo review before inclusion in the repository
- **Sandboxing**: Remote plugins run with the same permissions as local plugins
- **Token Management**: Use environment variables for sensitive configuration like API keys

## Best Practices

1. **Regular Updates**: Enable auto-update to receive the latest plugin versions
2. **Selective Loading**: Only enable plugins you actually need to minimize startup time
3. **Configuration Management**: Store sensitive configuration in environment variables
4. **Version Pinning**: Pin to specific plugin versions for production deployments

## Troubleshooting

### Common Issues

- **Plugin Not Found**: Verify the remote repository is accessible with `git ls-remote https://github.com/ikignosis/janito-plugins.git`, check that the plugin name matches exactly (case-sensitive), and ensure the plugin exists in the repository

- **Authentication Issues**: For private repositories, configure SSH keys or access tokens, and use HTTPS with personal access tokens for private repos

- **Update Failures**: Check network connectivity to GitHub, verify the local plugin cache directory permissions, and review git configuration for proxy settings

### Debug Commands

```bash
# Check remote repository status
janito --debug --list-remote-plugins

# Force update remote plugins
janito --update-remote-plugins

# Verify plugin integrity
janito --verify-plugins
```

## Contributing

To contribute plugins to the remote repository:

1. **Fork the repository**: https://github.com/ikignosis/janito-plugins
2. **Create your plugin**: Follow the standard plugin development guidelines
3. **Add documentation**: Include README and usage examples
4. **Submit a pull request**: Include tests and documentation

### Contribution Guidelines

- Follow the existing code style and structure
- Include comprehensive tests for your plugin
- Provide clear documentation and usage examples
- Ensure compatibility with the latest janito version
- Tag your plugin with appropriate categories

## Support

For issues with remote plugins:

- **Repository Issues**: https://github.com/ikignosis/janito-plugins/issues
- **General Support**: Use the main janito repository issues
- **Community**: Join discussions in the janito community forums