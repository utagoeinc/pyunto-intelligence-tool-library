/**
 * Save results to file
 * 
 * @param {Object} results - API response data
 * @param {string} outputFile - Output file path
 */
async function saveResults(results, outputFile) {
  if (!outputFile) return;
  
  try {
    await fs.promises.writeFile(
      outputFile,
      JSON.stringify(results, null, 2)
    );
    console.log(`\nResults saved to ${outputFile}`);
  } catch (error) {
    console.error(`Error saving results to file: ${error.message}`);
  }
}

/**
 * Main function
 */
async function main() {
  // Parse command line arguments
  const argv = yargs(hideBin(process.argv))
    .option('file', {
      alias: 'f',
      description: 'Path to the file to analyze',
      type: 'string',
      demandOption: true
    })
    .option('api-key', {
      alias: 'k',
      description: 'Pyunto Intelligence API key',
      type: 'string',
      demandOption: true
    })
    .option('assistant-id', {
      alias: 'a',
      description: 'Assistant ID to use',
      type: 'string',
      demandOption: true
    })
    .option('output', {
      alias: 'o',
      description: 'Output file to save results (optional)',
      type: 'string'
    })
    .help()
    .argv;

  try {
    console.log('Analyzing file with Pyunto Intelligence...');
    
    // Analyze file
    const results = await analyzeFile(
      argv.apiKey,
      argv.assistantId,
      argv.file
    );
    
    // Display results
    console.log('\nAPI Response:');
    console.log(JSON.stringify(results, null, 2));
    
    // Save results if output file is specified
    if (argv.output) {
      await saveResults(results, argv.output);
    }
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run the main function
main().catch(error => {
  console.error(`Unexpected error: ${error.message}`);
  process.exit(1);
});
/**
 * Upload and analyze file using Pyunto Intelligence API
 * 
 * @param {string} apiKey - Pyunto Intelligence API key
 * @param {string} assistantId - Assistant ID to use
 * @param {string} filePath - Path to the file
 * @returns {Promise<Object>} API response
 */
async function analyzeFile(apiKey, assistantId, filePath) {
  // Validate inputs
  if (!apiKey) throw new Error('API key is required');
  if (!assistantId) throw new Error('Assistant ID is required');
  if (!filePath) throw new Error('File path is required');
  
  // Check if file exists
  try {
    await fs.promises.access(filePath, fs.constants.F_OK);
  } catch (error) {
    throw new Error(`File not found: ${filePath}`);
  }
  
  // Get file type and MIME type
  const { type, mimeType } = getFileType(filePath);
  if (type === 'unknown') {
    throw new Error(`Unsupported file type: ${path.extname(filePath)}`);
  }
  
  // Encode file to base64
  const encodedData = await encodeFileToBase64(filePath);
  
  // Prepare API request
  const url = 'https://a.pyunto.com/api/i/v1';
  const headers = {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
  };
  
  const payload = {
    assistantId,
    type,
    data: encodedData,
    mimeType
  };
  
  // Make API request
  try {
    const response = await axios.post(url, payload, { headers });
    return response.data;
  } catch (error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      throw new Error(`API request failed with status ${error.response.status}: ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error('No response received from API server');
    } else {
      // Something happened in setting up the request
      throw new Error(`Error setting up request: ${error.message}`);
    }
  }
}/**
 * Pyunto Intelligence - Node.js Upload Example
 * 
 * This script demonstrates how to upload data to Pyunto Intelligence API
 * using Node.js and process the results.
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

/**
 * Encode file to base64
 * 
 * @param {string} filePath - Path to the file
 * @returns {Promise<string>} Base64 encoded string
 */
async function encodeFileToBase64(filePath) {
  try {
    const buffer = await fs.promises.readFile(filePath);
    return buffer.toString('base64');
  } catch (error) {
    console.error(`Error encoding file: ${error.message}`);
    throw error;
  }
}

/**
 * Determine file type and MIME type from file extension
 * 
 * @param {string} filePath - Path to the file
 * @returns {Object} Object containing file type and MIME type
 */
function getFileType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  
  // Image types
  if (['.jpg', '.jpeg', '.png', '.webp', '.gif'].includes(ext)) {
    const mimeType = {
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.webp': 'image/webp',
      '.gif': 'image/gif'
    }[ext] || 'image/jpeg';
    
    return { type: 'image', mimeType };
  }
  
  // Audio types
  if (['.mp3', '.wav', '.ogg', '.m4a', '.flac'].includes(ext)) {
    const mimeType = {
      '.mp3': 'audio/mp3',
      '.wav': 'audio/wav',
      '.ogg': 'audio/ogg',
      '.m4a': 'audio/mp4',
      '.flac': 'audio/flac'
    }[ext] || 'audio/mp3';
    
    return { type: 'audio', mimeType };
  }
  
  // Text types
  if (['.txt', '.md', '.csv', '.json', '.xml', '.html'].includes(ext)) {
    const mimeType = {
      '.txt': 'text/plain',
      '.md': 'text/markdown',
      '.csv': 'text/csv',
      '.json': 'application/json',
      '.xml': 'application/xml',
      '.html': 'text/html'
    }[ext] || 'text/plain';
    
    return { type: 'text', mimeType };
  }
  
  // Default for unknown types
  return { type: 'unknown', mimeType: 'application/octet-stream' };
}
