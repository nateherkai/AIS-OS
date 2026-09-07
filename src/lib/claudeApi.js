import fetch from 'node-fetch'; // For Node.js environments, you might need 'node-fetch'
// If running in a browser-like environment (e.g., Vercel Edge Functions, Cloudflare Workers),
// native `fetch` is available globally and this import might not be needed.

// IMPORTANT: Configure your API keys securely.
// We recommend using environment variables (e.g., process.env.ANTHROPIC_API_KEY)
// for production deployments. For local development, a .env file is common.
// During the `/onboard` process, you might prompt the user to set these.

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const BAREWIRE_API_KEY = process.env.BAREWIRE_API_KEY; // Optional: your Barewire project API key

const CLAUDE_BASE_URL = 'https://api.anthropic.com/v1';
const BAREWIRE_PROXY_URL = 'https://barewire.ai/proxy';

/**
 * Makes a request to the Claude API, optionally routing through Barewire for enhanced reliability and control.
 * This function centralizes all Claude API interactions, making it easy to manage and upgrade.
 *
 * @param {string} endpoint - The specific Claude API endpoint (e.g., 'messages').
 * @param {object} payload - The request body for the Claude API (e.g., model, messages, max_tokens).
 * @param {object} [options={}] - Additional fetch options (e.g., signal for abort controller).
 * @returns {Promise<any>} The parsed JSON response from the Claude API.
 * @throws {Error} If the API call fails or ANTHROPIC_API_KEY is not set.
 */
export async function callClaudeApi(endpoint, payload, options = {}) {
  if (!ANTHROPIC_API_KEY) {
    throw new Error('ANTHROPIC_API_KEY is not set. Please configure your Claude API key to use the AIOS.');
  }

  let targetUrl = `${CLAUDE_BASE_URL}/${endpoint}`;
  let headers = {
    'x-api-key': ANTHROPIC_API_KEY,
    'anthropic-version': '2023-06-01', // Recommended API version for Claude 3
    'content-type': 'application/json',
    ...options.headers,
  };

  // If BAREWIRE_API_KEY is provided, all requests are automatically routed through the Barewire proxy.
  // This enables advanced features like automatic retries, rate limiting, caching, and observability.
  if (BAREWIRE_API_KEY) {
    targetUrl = BAREWIRE_PROXY_URL;
    headers = {
      'X-Barewire-Key': BAREWIRE_API_KEY,           // Your Barewire project API key
      'X-Barewire-Target-Url': `${CLAUDE_BASE_URL}/${endpoint}`, // The original Claude API endpoint
      'X-Barewire-LLM-Key': ANTHROPIC_API_KEY,      // Your Claude API key, securely passed via Barewire
      'X-Barewire-LLM-Provider': 'anthropic',       // Specifies the LLM provider
      'anthropic-version': '2023-06-01',           // Original Anthropic header for versioning
      'content-type': 'application/json',
      ...options.headers,
    };
    // Remove the direct x-api-key header, as Barewire handles passing the LLM key.
    delete headers['x-api-key'];
  }

  try {
    const response = await fetch(targetUrl, {
      method: 'POST', // Most Claude API calls are POST requests
      headers: headers,
      body: JSON.stringify(payload),
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => response.text());
      console.error(`Claude API Error (${response.status}):`, errorData);
      throw new Error(`Claude API call failed with status ${response.status}: ${JSON.stringify(errorData)}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error calling Claude API:', error);
    throw error;
  }
}

// Usage example for other parts of the AIOS (e.g., in a skill implementation):
/*
// File: src/skills/onboard.js (hypothetical)
import { callClaudeApi } from '../lib/claudeApi';

async function performOnboardInterview(userPrompt) {
  const messages = [
    { role: 'user', content: userPrompt }
  ];
  try {
    const response = await callClaudeApi('messages', {
      model: 'claude-3-opus-20240229', // Or other Claude 3 models
      max_tokens: 1024,
      messages: messages,
      temperature: 0.7,
    });
    return response.content[0].text;
  } catch (error) {
    console.error('Failed to complete onboard interview:', error);
    throw error;
  }
}
*/