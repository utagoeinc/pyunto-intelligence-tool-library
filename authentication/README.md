# Pyunto Intelligence Authentication

This directory contains sample implementations for API key management and user authentication when working with the Pyunto Intelligence platform.

## Contents

The authentication module provides:

- **[api-key-management](./api-key-management)**: Utilities for generating, validating, and securely storing API keys
- **[user-auth](./user-auth)**: Sample code for implementing user authentication and authorization

## API Key Management

The API key management module provides tools to help you securely handle Pyunto Intelligence API keys in your applications. These utilities help with:

- Generating and validating API keys
- Securely storing API keys in various environments
- Rotating API keys according to best practices
- Managing API key permissions and scopes

### Example Usage

```python
from api_key_manager import ApiKeyManager

# Initialize the manager with your API key
manager = ApiKeyManager(master_key="YOUR_MASTER_API_KEY")

# Generate a new API key with specific permissions
new_key = manager.generate_key(
    name="App Integration Key",
    permissions=["read:image", "analyze:image"],
    expires_in_days=90
)

# Save the key (only shown once)
print(f"New API Key: {new_key['key']}")
print(f"Key ID: {new_key['id']}")

# Later, validate an API key
is_valid = manager.validate_key(
    key_to_validate="API_KEY_TO_CHECK",
    required_permissions=["read:image"]
)

if is_valid:
    print("API key is valid and has required permissions")
else:
    print("API key is invalid or missing required permissions")
```

## User Authentication

The user authentication module provides sample implementations for managing user access to Pyunto Intelligence through your application. These examples demonstrate:

- User registration with secure password handling
- Login/logout flows with Pyunto Intelligence API
- Token-based authentication for web applications
- Role-based access control for different user types
- Session management and token refresh

### Example Usage

```python
from pyunto_auth import PyuntoAuth

# Initialize the authentication client
auth = PyuntoAuth(
    api_key="YOUR_PYUNTO_API_KEY",
    redirect_uri="https://your-app.com/callback"
)

# Generate a login URL for your user
login_url = auth.get_login_url(
    state="random-state-value",
    scope=["read", "analyze"]
)

# Direct user to this URL to login
print(f"Login URL: {login_url}")

# After redirect, exchange code for tokens
tokens = auth.exchange_code_for_tokens(
    code="AUTHORIZATION_CODE_FROM_REDIRECT"
)

# Use the access token for API calls
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# Later, refresh the token when it expires
new_tokens = auth.refresh_token(refresh_token)
```

## Best Practices

### API Key Security

1. **Never hardcode API keys** directly in your source code
2. **Store API keys as environment variables** or in a secure key vault
3. **Restrict API key permissions** to only what's needed
4. **Rotate API keys regularly** (every 90 days recommended)
5. **Use separate API keys** for different environments (development, staging, production)

### User Authentication

1. **Always use HTTPS** for authentication requests
2. **Implement proper CSRF protection** for web applications
3. **Set appropriate token expiration times** (short for access tokens, longer for refresh tokens)
4. **Validate permissions** on the server side for each API request
5. **Implement secure token storage** on client devices

## Integration with Identity Providers

For production applications, we recommend integrating with established identity providers:

- OAuth 2.0 providers (Google, Microsoft, etc.)
- OpenID Connect
- Auth0, Okta, or similar identity platforms

The samples in this repository can be adapted to work with these providers while maintaining the connection to Pyunto Intelligence.

## Environment-Specific Configurations

### Server-Side Applications

For server-side applications, store API keys securely using environment variables:

```bash
# .env file (don't commit to version control)
PYUNTO_API_KEY=your_api_key_here
```

### Single-Page Applications (SPAs)

For SPAs, use token-based authentication and avoid storing API keys in client-side code:

```javascript
// Use an authentication service
const authService = new PyuntoAuthService({
  authUrl: 'https://your-auth-server.com/auth',
  clientId: 'YOUR_CLIENT_ID'
});

// Get tokens after user login
const tokens = await authService.login(username, password);

// Use tokens for API requests
const result = await pyuntoClient.analyzeImage({
  accessToken: tokens.accessToken,
  imageData: imageBase64
});
```

### Mobile Applications

For mobile applications, use secure storage for tokens:

```swift
// Swift example
import Security

func saveApiKey(_ apiKey: String) {
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: "PyuntoApiKey",
        kSecValueData as String: apiKey.data(using: .utf8)!,
        kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    ]
    
    SecItemDelete(query as CFDictionary)
    SecItemAdd(query as CFDictionary, nil)
}
```

## Requirements

- Python 3.6+ (for Python examples)
- Node.js 14+ (for JavaScript examples)
- Standard security libraries depending on your platform

## License

This code is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
