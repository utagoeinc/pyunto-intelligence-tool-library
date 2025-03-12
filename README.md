# Pyunto Intelligence Tool Library

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A collection of tools, utilities, and sample code to help you integrate and leverage the Pyunto Intelligence smart assistant generation platform in your projects.

## Overview

Pyunto Intelligence is a smart assistant generation platform that helps extract strategic insights from various data sources. This repository contains sample code, libraries, and utilities to help you integrate Pyunto Intelligence into your applications, process various data types, and build custom solutions on top of the platform.

## Repository Structure

This repository is organized by functionality:

- **[document-processing](./document-processing)**: Tools for extracting text from PDF and Word documents
- **[video-processing](./video-processing)**: Utilities for video frame extraction, audio extraction, and format conversion
- **[api-integration](./api-integration)**: Sample code for third-party integrations and plugins
- **[data-samples](./data-samples)**: Example data upload interfaces and visualization components
- **[authentication](./authentication)**: Sample implementations for API key management and user authentication
- **[database-examples](./database-examples)**: Database schema and integration examples
- **[system-monitoring](./system-monitoring)**: Components for monitoring performance, detecting errors, and system backup

## Getting Started

To get started with Pyunto Intelligence, you'll need:

1. A subscription to Pyunto Intelligence - [Sign up here](https://i.pyunto.com/)
2. Your API key (available in your dashboard after subscription)
3. The appropriate sample code from this repository for your use case

For detailed instructions on getting started, visit our [Getting Started Guide](./docs/getting-started.md).

## Installation

Each tool or utility in this repository may have specific installation requirements. Please refer to the README.md file in each directory for specific installation and usage instructions.

## Examples

Here's a quick example using the Python client for image analysis:

```python
import pyunto_client

# Initialize the client with your API key
client = pyunto_client.PyuntoClient(api_key="YOUR_API_KEY")

# Analyze an image with a specific feature
result = client.analyze_image(
    image_path="./sample_image.jpg",
    feature="identify_food_items"
)

print(result)
```

For more examples, check the [examples directory](./docs/examples).

## Contributing

We welcome contributions to this library! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for details on how to contribute.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](./LICENSE) file for details.

```
Copyright 2025 Utagoe Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Support

For support with this library, please open an issue in this repository.

For questions about your Pyunto Intelligence subscription or account, please contact: pyunto@utagoe.com

## Related Resources

- [Pyunto Intelligence Official Website](https://i.pyunto.com)
