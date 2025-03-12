// MongoDB schema design for Pyunto Intelligence API usage tracking
// This example demonstrates how to model data in MongoDB for a NoSQL approach

// Connect to MongoDB and use the pyunto_intelligence database
db = db.getSiblingDB('pyunto_intelligence');

// Create collections with validation schemas
db.createCollection('assistants', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'featureType', 'featuresCount', 'configuration', 'createdAt'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Name of the assistant'
        },
        description: {
          bsonType: 'string',
          description: 'Description of the assistant'
        },
        featureType: {
          enum: ['IMAGE', 'TEXT', 'AUDIO'],
          description: 'Type of data the assistant processes'
        },
        featuresCount: {
          bsonType: 'int',
          minimum: 1,
          description: 'Number of features configured'
        },
        configuration: {
          bsonType: 'object',
          description: 'Configuration details of the assistant'
        },
        outputSchema: {
          bsonType: 'object',
          description: 'JSON schema for assistant output format'
        },
        createdAt: {
          bsonType: 'date',
          description: 'Creation timestamp'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'Last update timestamp'
        },
        isActive: {
          bsonType: 'bool',
          description: 'Whether the assistant is active'
        }
      }
    }
  }
});

db.createCollection('apiKeys', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['keyHash', 'keyName', 'createdAt'],
      properties: {
        keyHash: {
          bsonType: 'string',
          description: 'Hashed API key for security'
        },
        keyName: {
          bsonType: 'string',
          description: 'Name of the API key'
        },
        createdAt: {
          bsonType: 'date',
          description: 'Creation timestamp'
        },
        expiresAt: {
          bsonType: 'date',
          description: 'Expiration timestamp'
        },
        lastUsedAt: {
          bsonType: 'date',
          description: 'Last usage timestamp'
        },
        isActive: {
          bsonType: 'bool',
          description: 'Whether the API key is active'
        }
      }
    }
  }
});

db.createCollection('apiUsage', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['apiKeyId', 'assistantId', 'requestTimestamp', 'inputType'],
      properties: {
        apiKeyId: {
          bsonType: 'objectId',
          description: 'Reference to the API key'
        },
        assistantId: {
          bsonType: 'objectId',
          description: 'Reference to the assistant'
        },
        requestTimestamp: {
          bsonType: 'date',
          description: 'Request timestamp'
        },
        responseTimestamp: {
          bsonType: 'date',
          description: 'Response timestamp'
        },
        latencyMs: {
          bsonType: 'int',
          description: 'Request-response latency in milliseconds'
        },
        statusCode: {
          bsonType: 'int',
          description: 'HTTP status code'
        },
        inputType: {
          enum: ['IMAGE', 'TEXT', 'AUDIO'],
          description: 'Type of input data'
        },
        inputSizeBytes: {
          bsonType: 'int',
          description: 'Size of input data in bytes'
        },
        ipAddress: {
          bsonType: 'string',
          description: 'Client IP address'
        },
        userAgent: {
          bsonType: 'string',
          description: 'Client user agent'
        },
        requestId: {
          bsonType: 'string',
          description: 'Unique request ID'
        },
        errorMessage: {
          bsonType: 'string',
          description: 'Error message if any'
        },
        isBillable: {
          bsonType: 'bool',
          description: 'Whether this usage is billable'
        },
        result: {
          bsonType: 'object',
          description: 'API result data'
        }
      }
    }
  }
});

db.createCollection('subscriptions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['plan', 'status', 'startDate'],
      properties: {
        customerId: {
          bsonType: 'string',
          description: 'Customer ID from subscription service'
        },
        plan: {
          enum: ['STANDARD', 'PRO', 'ENTERPRISE'],
          description: 'Subscription plan'
        },
        status: {
          enum: ['ACTIVE', 'CANCELED', 'EXPIRED', 'PENDING', 'SUSPENDED'],
          description: 'Subscription status'
        },
        startDate: {
          bsonType: 'date',
          description: 'Subscription start date'
        },
        endDate: {
          bsonType: 'date',
          description: 'Subscription end date'
        },
        autoRenew: {
          bsonType: 'bool',
          description: 'Whether subscription auto-renews'
        },
        monthlyApiLimit: {
          bsonType: 'int',
          description: 'Monthly API call limit'
        },
        concurrentApiLimit: {
          bsonType: 'int',
          description: 'Concurrent API call limit'
        },
        isCustomExportEnabled: {
          bsonType: 'bool',
          description: 'Whether custom export is enabled'
        }
      }
    }
  }
});

db.createCollection('billing', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['monthYear', 'apiCallsCount', 'totalAmount'],
      properties: {
        monthYear: {
          bsonType: 'string',
          description: 'Month and year in YYYY-MM format'
        },
        apiCallsCount: {
          bsonType: 'int',
          description: 'Total API calls in this period'
        },
        totalAmount: {
          bsonType: 'decimal',
          description: 'Total billing amount'
        },
        subscriptionPlan: {
          bsonType: 'string',
          description: 'Subscription plan'
        },
        subscriptionId: {
          bsonType: 'string',
          description: 'Subscription ID'
        },
        isPaid: {
          bsonType: 'bool',
          description: 'Whether this bill is paid'
        },
        invoiceNumber: {
          bsonType: 'string',
          description: 'Invoice number'
        },
        invoiceDate: {
          bsonType: 'date',
          description: 'Invoice date'
        },
        dueDate: {
          bsonType: 'date',
          description: 'Payment due date'
        },
        createdAt: {
          bsonType: 'date',
          description: 'Creation timestamp'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'Last update timestamp'
        }
      }
    }
  }
});

// Create indexes for better query performance
db.assistants.createIndex({ name: 1 }, { unique: true });
db.assistants.createIndex({ featureType: 1 });
db.assistants.createIndex({ isActive: 1 });

db.apiKeys.createIndex({ keyHash: 1 }, { unique: true });
db.apiKeys.createIndex({ keyName: 1 });
db.apiKeys.createIndex({ isActive: 1 });
db.apiKeys.createIndex({ lastUsedAt: 1 });

db.apiUsage.createIndex({ requestTimestamp: 1 });
db.apiUsage.createIndex({ apiKeyId: 1 });
db.apiUsage.createIndex({ assistantId: 1 });
db.apiUsage.createIndex({ statusCode: 1 });
db.apiUsage.createIndex({ 
  requestTimestamp: 1,
  apiKeyId: 1,
  assistantId: 1
});
db.apiUsage.createIndex({ 
  "requestTimestamp": 1,
  "inputType": 1,
  "statusCode": 1 
});

db.subscriptions.createIndex({ customerId: 1 });
db.subscriptions.createIndex({ status: 1 });
db.subscriptions.createIndex({ endDate: 1 });

db.billing.createIndex({ monthYear: 1 }, { unique: true });
db.billing.createIndex({ isPaid: 1 });

// Sample data insertion
db.assistants.insertMany([
  {
    name: 'Product Analyzer',
    description: 'Analyzes product images to extract features',
    featureType: 'IMAGE',
    featuresCount: 5,
    configuration: {
      extractBrand: true,
      extractColor: true,
      extractSize: true,
      extractMaterial: true,
      extractStyle: true
    },
    outputSchema: {
      type: 'object',
      properties: {
        brand: { type: 'string' },
        color: { type: 'string' },
        size: { type: 'string' },
        material: { type: 'string' },
        style: { type: 'string' }
      }
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    isActive: true
  },
  {
    name: 'Menu Item Recognizer',
    description: 'Recognizes food items in menu images',
    featureType: 'IMAGE',
    featuresCount: 3,
    configuration: {
      extractDishName: true,
      extractPrice: true,
      extractIngredients: true
    },
    outputSchema: {
      type: 'object',
      properties: {
        dishName: { type: 'string' },
        price: { type: 'number' },
        ingredients: { type: 'array', items: { type: 'string' } }
      }
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    isActive: true
  },
  {
    name: 'Text Extractor',
    description: 'Extracts structured information from text',
    featureType: 'TEXT',
    featuresCount: 2,
    configuration: {
      extractEntities: true,
      extractSentiment: true
    },
    outputSchema: {
      type: 'object',
      properties: {
        entities: { type: 'array', items: { type: 'object' } },
        sentiment: { type: 'string', enum: ['positive', 'neutral', 'negative'] }
      }
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    isActive: true
  }
]);

// Insert subscription plan configurations
db.subscriptionPlans.insertMany([
  {
    code: 'STANDARD',
    price: 50000, // 50,000 JPY
    monthlyApiLimit: 3000,
    concurrentApiLimit: 1,
    maxInputSizeBytes: 5 * 1024 * 1024, // 5MB
    isCustomExportEnabled: false,
    createdAt: new Date()
  },
  {
    code: 'PRO',
    price: 250000, // 250,000 JPY
    monthlyApiLimit: 40000,
    concurrentApiLimit: 5,
    maxInputSizeBytes: 10 * 1024 * 1024, // 10MB
    isCustomExportEnabled: false,
    createdAt: new Date()
  },
  {
    code: 'ENTERPRISE',
    price: 1800000, // 1,800,000 JPY
    monthlyApiLimit: 300000,
    concurrentApiLimit: 20,
    maxInputSizeBytes: 50 * 1024 * 1024, // 50MB
    isCustomExportEnabled: true,
    createdAt: new Date()
  }
]);

// Sample queries for common use cases
// 1. Get daily API usage for the last 30 days
function getDailyApiUsage() {
  return db.apiUsage.aggregate([
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
      $project: {
        _id: 0,
        date: {
          $dateFromParts: {
            year: "$_id.year",
            month: "$_id.month",
            day: "$_id.day"
          }
        },
        totalCalls: 1,
        successfulCalls: 1,
        errorCalls: 1,
        avgLatencyMs: { $round: ["$avgLatencyMs", 2] },
        errorRate: {
          $multiply: [
            { $divide: ["$errorCalls", "$totalCalls"] },
            100
          ]
        }
      }
    },
    {
      $sort: { date: 1 }
    }
  ]).toArray();
}

// 2. Get usage statistics by assistant
function getAssistantUsage() {
  return db.apiUsage.aggregate([
    {
      $match: {
        requestTimestamp: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
      }
    },
    {
      $lookup: {
        from: "assistants",
        localField: "assistantId",
        foreignField: "_id",
        as: "assistant"
      }
    },
    {
      $unwind: "$assistant"
    },
    {
      $group: {
        _id: "$assistantId",
        assistantName: { $first: "$assistant.name" },
        featureType: { $first: "$assistant.featureType" },
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
        avgLatencyMs: { $avg: "$latencyMs" },
        totalDataProcessedBytes: { $sum: "$inputSizeBytes" }
      }
    },
    {
      $project: {
        _id: 0,
        assistantId: "$_id",
        assistantName: 1,
        featureType: 1,
        totalCalls: 1,
        successfulCalls: 1,
        errorCalls: 1,
        avgLatencyMs: { $round: ["$avgLatencyMs", 2] },
        totalDataProcessedMB: { 
          $round: [{ $divide: ["$totalDataProcessedBytes", 1048576] }, 2] 
        },
        errorRate: {
          $round: [
            { $multiply: [{ $divide: ["$errorCalls", "$totalCalls"] }, 100] },
            2
          ]
        }
      }
    },
    {
      $sort: { totalCalls: -1 }
    }
  ]).toArray();
}

// 3. Get usage by input type (IMAGE, TEXT, AUDIO)
function getUsageByInputType() {
  return db.apiUsage.aggregate([
    {
      $match: {
        requestTimestamp: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }
      }
    },
    {
      $group: {
        _id: "$inputType",
        totalCalls: { $sum: 1 },
        avgLatencyMs: { $avg: "$latencyMs" },
        totalDataProcessedBytes: { $sum: "$inputSizeBytes" }
      }
    },
    {
      $project: {
        _id: 0,
        inputType: "$_id",
        totalCalls: 1,
        avgLatencyMs: { $round: ["$avgLatencyMs", 2] },
        totalDataProcessedMB: { 
          $round: [{ $divide: ["$totalDataProcessedBytes", 1048576] }, 2] 
        },
        percentageOfTotal: { $literal: null } // Will be calculated in code
      }
    },
    {
      $sort: { totalCalls: -1 }
    }
  ]).toArray();
}

// 4. Get monthly billing summary
function getMonthlyBillingInfo() {
  return db.billing.find({}, {
    _id: 0,
    monthYear: 1,
    apiCallsCount: 1,
    totalAmount: 1,
    subscriptionPlan: 1,
    isPaid: 1,
    invoiceNumber: 1,
    invoiceDate: 1,
    dueDate: 1
  }).sort({ monthYear: -1 }).toArray();
}

// 5. Get API keys status and usage
function getApiKeysStatus() {
  return db.apiKeys.aggregate([
    {
      $lookup: {
        from: "apiUsage",
        localField: "_id",
        foreignField: "apiKeyId",
        as: "usage"
      }
    },
    {
      $project: {
        _id: 0,
        keyId: "$_id",
        keyName: 1,
        isActive: 1,
        createdAt: 1,
        expiresAt: 1,
        lastUsedAt: 1,
        totalCalls: { $size: "$usage" },
        isExpired: {
          $cond: [
            { $and: [
              { $ne: ["$expiresAt", null] },
              { $lt: ["$expiresAt", new Date()] }
            ]},
            true,
            false
          ]
        },
        daysSinceLastUsed: {
          $cond: [
            { $eq: ["$lastUsedAt", null] },
            null,
            {
              $divide: [
                { $subtract: [new Date(), "$lastUsedAt"] },
                86400000 // milliseconds in a day
              ]
            }
          ]
        }
      }
    },
    {
      $sort: { totalCalls: -1 }
    }
  ]).toArray();
}

// 6. Get error summary by type
function getErrorSummary() {
  return db.apiUsage.aggregate([
    {
      $match: {
        requestTimestamp: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
        statusCode: { $gte: 400 }
      }
    },
    {
      $group: {
        _id: "$statusCode",
        count: { $sum: 1 },
        firstOccurrence: { $min: "$requestTimestamp" },
        lastOccurrence: { $max: "$requestTimestamp" },
        errorMessages: { $addToSet: "$errorMessage" }
      }
    },
    {
      $project: {
        _id: 0,
        statusCode: "$_id",
        count: 1,
        firstOccurrence: 1,
        lastOccurrence: 1,
        errorMessages: { $slice: ["$errorMessages", 5] }, // Show max 5 unique error messages
        percentage: { $literal: null } // Will be calculated in code
      }
    },
    {
      $sort: { count: -1 }
    }
  ]).toArray();
}

// 7. Get active subscriptions summary
function getActiveSubscriptionsSummary() {
  return db.subscriptions.aggregate([
    {
      $match: {
        status: "ACTIVE",
        endDate: { $gt: new Date() }
      }
    },
    {
      $group: {
        _id: "$plan",
        count: { $sum: 1 },
        totalMonthlyApiLimit: { $sum: "$monthlyApiLimit" }
      }
    },
    {
      $project: {
        _id: 0,
        plan: "$_id",
        count: 1,
        totalMonthlyApiLimit: 1
      }
    },
    {
      $sort: { count: -1 }
    }
  ]).toArray();
}

// 8. Get usage vs limit statistics for active subscriptions
function getUsageVsLimitStats() {
  const now = new Date();
  const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  
  return db.subscriptions.aggregate([
    {
      $match: {
        status: "ACTIVE",
        endDate: { $gt: now }
      }
    },
    {
      $lookup: {
        from: "apiUsage",
        let: { customerId: "$customerId" },
        pipeline: [
          {
            $match: {
              $expr: {
                $and: [
                  { $eq: ["$customerId", "$$customerId"] },
                  { $gte: ["$requestTimestamp", firstDayOfMonth] }
                ]
              }
            }
          }
        ],
        as: "usage"
      }
    },
    {
      $project: {
        _id: 0,
        customerId: 1,
        plan: 1,
        monthlyApiLimit: 1,
        apiCallsUsed: { $size: "$usage" },
        apiCallsRemaining: { 
          $subtract: ["$monthlyApiLimit", { $size: "$usage" }] 
        },
        usagePercentage: {
          $multiply: [
            { $divide: [{ $size: "$usage" }, "$monthlyApiLimit"] },
            100
          ]
        },
        isAboutToReachLimit: {
          $gte: [
            { $multiply: [
              { $divide: [{ $size: "$usage" }, "$monthlyApiLimit"] },
              100
            ]},
            80 // 80% threshold
          ]
        }
      }
    },
    {
      $sort: { usagePercentage: -1 }
    }
  ]).toArray();
}

// 9. Get usage trends by time of day (for capacity planning)
function getUsageByTimeOfDay() {
  return db.apiUsage.aggregate([
    {
      $match: {
        requestTimestamp: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) }
      }
    },
    {
      $group: {
        _id: { $hour: "$requestTimestamp" },
        totalCalls: { $sum: 1 },
        avgLatencyMs: { $avg: "$latencyMs" },
        maxLatencyMs: { $max: "$latencyMs" },
        errorRate: {
          $avg: {
            $cond: [
              { $gte: ["$statusCode", 400] },
              1,
              0
            ]
          }
        }
      }
    },
    {
      $project: {
        _id: 0,
        hourOfDay: "$_id",
        totalCalls: 1,
        avgLatencyMs: { $round: ["$avgLatencyMs", 2] },
        maxLatencyMs: 1,
        errorRate: { $round: [{ $multiply: ["$errorRate", 100] }, 2] }
      }
    },
    {
      $sort: { hourOfDay: 1 }
    }
  ]).toArray();
}

// 10. Get large input size trends (for performance analysis)
function getLargeInputSizeTrends() {
  return db.apiUsage.aggregate([
    {
      $match: {
        requestTimestamp: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
        inputSizeBytes: { $gt: 1 * 1024 * 1024 } // Over 1MB
      }
    },
    {
      $group: {
        _id: {
          year: { $year: "$requestTimestamp" },
          month: { $month: "$requestTimestamp" },
          day: { $dayOfMonth: "$requestTimestamp" }
        },
        count: { $sum: 1 },
        avgSizeBytes: { $avg: "$inputSizeBytes" },
        maxSizeBytes: { $max: "$inputSizeBytes" },
        avgLatencyMs: { $avg: "$latencyMs" }
      }
    },
    {
      $project: {
        _id: 0,
        date: {
          $dateFromParts: {
            year: "$_id.year",
            month: "$_id.month",
            day: "$_id.day"
          }
        },
        count: 1,
        avgSizeMB: { $round: [{ $divide: ["$avgSizeBytes", 1048576] }, 2] },
        maxSizeMB: { $round: [{ $divide: ["$maxSizeBytes", 1048576] }, 2] },
        avgLatencyMs: { $round: ["$avgLatencyMs", 2] }
      }
    },
    {
      $sort: { date: 1 }
    }
  ]).toArray();
}

// Example Node.js implementation to use these MongoDB functions
function nodeJsExample() {
  return `
const { MongoClient } = require('mongodb');
const moment = require('moment');

// Connection URI
const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/pyunto_intelligence';

// Create a new MongoClient
const client = new MongoClient(uri);

// Function to generate usage reports
async function generateUsageReports() {
  try {
    // Connect to the MongoDB server
    await client.connect();
    console.log('Connected to MongoDB');
    
    // Get database and collections
    const db = client.db();
    
    // Get daily API usage for the last 30 days
    const dailyUsage = await db.collection('apiUsage').aggregate([
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
        $project: {
          _id: 0,
          date: {
            $dateFromParts: {
              year: "$_id.year",
              month: "$_id.month",
              day: "$_id.day"
            }
          },
          totalCalls: 1,
          successfulCalls: 1,
          errorCalls: 1,
          avgLatencyMs: { $round: ["$avgLatencyMs", 2] },
          errorRate: {
            $multiply: [
              { $divide: ["$errorCalls", "$totalCalls"] },
              100
            ]
          }
        }
      },
      {
        $sort: { date: 1 }
      }
    ]).toArray();
    
    console.log('Daily API Usage Report:');
    dailyUsage.forEach(day => {
      console.log(
        \`\${moment(day.date).format('YYYY-MM-DD')}: \${day.totalCalls} calls, \` +
        \`\${day.errorRate.toFixed(2)}% error rate, \${day.avgLatencyMs}ms avg latency\`
      );
    });
    
    // Get usage by assistant
    const assistantUsage = await getAssistantUsage(db);
    console.log('\\nAssistant Usage Report:');
    assistantUsage.forEach(assistant => {
      console.log(
        \`\${assistant.assistantName} (\${assistant.featureType}): \${assistant.totalCalls} calls, \` +
        \`\${assistant.errorRate}% error rate, \${assistant.totalDataProcessedMB}MB processed\`
      );
    });
    
    // Get usage by input type
    const typeUsage = await getUsageByInputType(db);
    console.log('\\nUsage by Input Type:');
    const totalCalls = typeUsage.reduce((sum, type) => sum + type.totalCalls, 0);
    typeUsage.forEach(type => {
      // Calculate percentage of total
      type.percentageOfTotal = ((type.totalCalls / totalCalls) * 100).toFixed(2);
      console.log(
        \`\${type.inputType}: \${type.totalCalls} calls (\${type.percentageOfTotal}%), \` +
        \`\${type.avgLatencyMs}ms avg latency, \${type.totalDataProcessedMB}MB processed\`
