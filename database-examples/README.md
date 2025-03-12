# Pyunto Intelligence Database Examples

This directory contains database schema examples and integration code for storing and managing Pyunto Intelligence data in various database systems. These examples demonstrate how to structure your database to efficiently store API usage, results, and configuration data.

## Contents

The database examples are organized by database type:

- **[sql](./sql)**: SQL database schema and integration examples (PostgreSQL, MySQL)
- **[nosql](./nosql)**: NoSQL database schema and integration examples (MongoDB, DynamoDB)

## Overview

When integrating Pyunto Intelligence into your applications, you'll likely need to store various types of data:

1. **API Configuration**: API keys, smart assistant definitions, and user settings
2. **Usage Tracking**: API call history, rate limiting data, and billing information
3. **Processing Results**: Results from Pyunto Intelligence API calls for further analysis
4. **User Management**: User accounts, permissions, and authentication data

These examples provide recommended schemas and implementation patterns for each database type.

## SQL Database Examples

The SQL examples include schema definitions for PostgreSQL and MySQL that you can adapt to your needs.

### Schema Highlights

- **Users and Authentication**: Tables for storing user information and API credentials
- **Smart Assistants**: Tables for storing assistant configurations
- **API Usage**: Tables for tracking API requests, responses, and billing information
- **Results Storage**: Efficient structures for storing various result types

### PostgreSQL Example

The PostgreSQL example (`sql/pyunto_intelligence_schema.sql`) includes:

- Table definitions with appropriate types and constraints
- Indexes for performance optimization
- Foreign key relationships for data integrity
- Sample queries for common operations
- Migrations for schema evolution

### Usage Example

```sql
-- Create a new assistant configuration
INSERT INTO assistants (name, feature_type, features_count, configuration, status)
VALUES (
    'Product Analyzer',
    'IMAGE',
    5,
    '{"extractBrand": true, "extractColor": true, "extractSize": true, "extractMaterial": true, "extractStyle": true}',
    'ACTIVE'
);

-- Track API usage
INSERT INTO api_usage (api_key_id, assistant_id, request_timestamp, input_type, status_code, input_size_bytes)
VALUES (
    'f7e2a6b0-d8c7-4e5a-9f0e-8d3b1d6c1e2a', -- API key ID
    'a1b2c3d4-e5f6-7890-abcd-1234567890ab', -- Assistant ID
    CURRENT_TIMESTAMP,
    'IMAGE',
    200,
    1024000
);

-- Query usage statistics by month
SELECT 
    DATE_TRUNC('month', request_timestamp) AS month,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) AS successful_requests,
    AVG(latency_ms) AS avg_latency
FROM api_usage
GROUP BY DATE_TRUNC('month', request_timestamp)
ORDER BY month DESC;
```

## NoSQL Database Examples

The NoSQL examples include schema designs for document-based (MongoDB) and key-value (DynamoDB) databases.

### MongoDB Example

The MongoDB example (`nosql/mongodb_schema.js`) includes:

- Collection schemas with validation
- Indexes for query optimization
- Sample data creation
- Common query patterns
- Aggregation pipelines for analytics

### MongoDB Usage Example

```javascript
// Query daily API usage
db.apiUsage.aggregate([
  {
    $match: {
      requestTimestamp: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
    }
  },
  {
    $group: {
      _id: {
        year: { $year: "$requestTimestamp" },
        month: { $month: "$requestTimestamp" },
        day: { $dayOfMonth: "$requestTimestamp" }
      },
      totalCalls: { $sum: 1 },
      successfulCalls: {
        $sum: {
          $cond: [
            { $and: [
              { $gte: ["$statusCode", 200] },
              { $lt: ["$statusCode", 300] }
            ]},
            1,
            0
          ]
        }
      },
      errorCalls: {
        $sum: {
          $cond: [
            { $gte: ["$statusCode", 400] },
            1,
            0
          ]
        }
      },
      avgLatencyMs: { $avg: "$latencyMs" }
    }
  },
  {
    $sort: { "_id.year": -1, "_id.month": -1, "_id.day": -1 }
  }
]);
```

### DynamoDB Example

The DynamoDB example includes:

- Table designs with appropriate partition and sort keys
- Secondary indexes for flexible querying
- Time-to-live (TTL) settings for data expiration
- Access patterns optimized for DynamoDB's model

## Integration Examples

Each database example includes integration code showing how to use the schema with common programming languages:

- Python with SQLAlchemy (SQL) and PyMongo (MongoDB)
- Node.js with Sequelize (SQL) and Mongoose (MongoDB)
- Java with JDBC (SQL) and MongoDB Java Driver

## Data Migration

The examples also include utilities for data migration between different database systems:

- SQL to SQL migration (e.g., MySQL to PostgreSQL)
- SQL to NoSQL migration (e.g., PostgreSQL to MongoDB)
- NoSQL to SQL migration (e.g., MongoDB to PostgreSQL)

## Performance Considerations

### SQL Performance Tips

- Use appropriate indexes for query patterns
- Consider partitioning large tables (e.g., api_usage)
- Implement regular maintenance (VACUUM, ANALYZE)
- Use connection pooling in application code

### NoSQL Performance Tips

- Design around access patterns
- Use appropriate sharding keys
- Consider data compression for large datasets
- Implement appropriate caching strategies

## Security Best Practices

All database examples follow security best practices:

- Sensitive data encryption
- Proper access control
- Password hashing
- Input validation and sanitization
- Protection against SQL/NoSQL injection

## Scaling Considerations

The examples include recommendations for scaling your database as your usage grows:

- Read replicas configuration
- Sharding strategies
- Connection pooling
- Query optimization

## Requirements

- PostgreSQL 12+ or MySQL 8+ for SQL examples
- MongoDB 4.4+ for MongoDB examples
- Amazon DynamoDB for DynamoDB examples
- Python 3.6+ or Node.js 14+ for integration examples

## License

This code is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
