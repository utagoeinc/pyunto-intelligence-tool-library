# API Integration Library

This directory contains samples and utilities for integrating Pyunto Intelligence with various third-party services and platforms.

## Contents

- **plugins/** - Ready-to-use plugins for popular platforms
  - WordPress plugin
  - Shopify app
  - Node.js Express middleware
  - Python Flask extension
  
- **security/** - Security best practices and utilities
  - Rate limiting implementation
  - API key rotation utilities
  - Request validation helpers
  - IP allowlisting

## Getting Started

Each subdirectory contains its own README with specific installation and usage instructions.

### Prerequisites

- Pyunto Intelligence API key (obtain from your account dashboard)
- Basic understanding of the Pyunto Intelligence API endpoints
- Development environment for your platform of choice

### General Usage Pattern

Most integrations follow this general pattern:

```python
# Initialize the client
from pyunto_integration import PyuntoClient

client = PyuntoClient(api_key="your_api_key")

# Configure your assistant
assistant_id = "your_assistant_id"

# Process data
result = client.process_image(
    assistant_id=assistant_id,
    image_path="path/to/image.jpg"
)

# Use the results
print(result)
```

## Contributing

If you've created an integration for a platform not listed here, we welcome your contribution! Please see our main [CONTRIBUTING.md](../../CONTRIBUTING.md) file for guidelines.
