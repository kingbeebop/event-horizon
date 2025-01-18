"use client";

import { useState, useEffect } from 'react';
import { BrowserOAuthClient } from '@atproto/oauth-client-browser';

// Initialize the OAuth client for development using loopback configuration
const oauthClient = new BrowserOAuthClient({
  handleResolver: 'https://bsky.social',
  // For development, we use undefined clientMetadata to enable loopback mode
  clientMetadata: undefined,
});

// Initialize the Bluesky agent

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userDid, setUserDid] = useState<string | null>(null);
  const [handle, setHandle] = useState<string>('');

  // Initialize OAuth client and check for existing session
  useEffect(() => {
    const initOAuth = async () => {
      try {
        // Ensure we're using the loopback IP instead of localhost
        if (window.location.hostname === 'localhost') {
          window.location.replace(window.location.href.replace('localhost', '127.0.0.1'));
          return;
        }

        const result = await oauthClient.init();
        if (result?.session) {
          setIsAuthenticated(true);
          setUserDid(result.session.sub);
          console.log('Session initialized for:', result.session.sub);
        }
      } catch (error) {
        console.error('OAuth initialization error:', error);
        setError(error instanceof Error ? error.message : 'Failed to initialize OAuth');
      }
    };

    initOAuth();
  }, []);

  const handleLogin = async () => {
    if (!handle) {
      setError('Please enter your Bluesky handle');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    try {
      await oauthClient.signIn(handle, {
        state: Math.random().toString(36).substring(7),
      });
      // Note: This won't execute as signIn redirects the page
    } catch (error) {
      console.error('Login failed:', error);
      setError(error instanceof Error ? error.message : 'Login failed');
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      // Clear all browser storage
      await window.indexedDB.deleteDatabase('atproto-oauth');
      localStorage.clear();
      sessionStorage.clear();

      // Clear cookies
      document.cookie.split(';').forEach(cookie => {
        const [name] = cookie.split('=');
        document.cookie = `${name.trim()}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
      });

      // Reset state
      setIsAuthenticated(false);
      setUserDid(null);
      setHandle('');

      // Force reload to clear any in-memory state
      window.location.href = window.location.origin;
    } catch (error) {
      console.error('Logout failed:', error);
      setError(error instanceof Error ? error.message : 'Failed to logout');
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          {!isAuthenticated ? (
            <div className="flex flex-col items-center space-y-4">
              <input
                type="text"
                placeholder="Your handle (e.g. you.bsky.social)"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                className="w-64 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <button
                onClick={handleLogin}
                disabled={isLoading || !handle}
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Connecting...' : 'Login with Bluesky'}
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center space-y-4">
              <p>Logged in as: {userDid}</p>
              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 w-full flex flex-col items-center justify-center">
        {isAuthenticated ? (
          <p className="text-gray-600">Successfully authenticated with Bluesky!</p>
        ) : (
          <p className="text-gray-600">Please log in to continue</p>
        )}
      </div>
    </main>
  );
}
