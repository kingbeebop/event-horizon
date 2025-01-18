"use client";

import { useState, useEffect } from 'react';
import { BrowserOAuthClient } from '@atproto/oauth-client-browser';

// Initialize the OAuth client for development using loopback configuration
const oauthClient = new BrowserOAuthClient({
  handleResolver: 'https://bsky.social',
  // For development, we use undefined clientMetadata to enable loopback mode
  clientMetadata: undefined,
});

// Define the post type based on the API structure
interface Post {
  cid: string;
  uri: string;
  author_did: string;
  text: string;
  created_at: string;
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userDid, setUserDid] = useState<string | null>(null);
  const [handle, setHandle] = useState<string>('');
  const [currentPost, setCurrentPost] = useState<Post | null>(null);
  const [isLoadingPost, setIsLoadingPost] = useState(false);

  // Fetch the next post from the firehose
  const fetchNextPost = async () => {
    setIsLoadingPost(true);
    try {
      const response = await fetch('/api/posts/next/');
      const data = await response.json();
      if (data.success && data.post) {
        setCurrentPost(data.post);
      }
    } catch (error) {
      console.error('Failed to fetch post:', error);
    } finally {
      setIsLoadingPost(false);
    }
  };

  // Initialize OAuth client and check for existing session
  useEffect(() => {
    const initOAuth = async () => {
      // Only run on client side
      if (typeof window === 'undefined') return;
      
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

  // Fetch initial post on component mount
  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;
    fetchNextPost();
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
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-50">
      {/* Title Section */}
      <h1 className="text-4xl font-bold text-blue-600 mb-12 mt-8">Yaynaysky</h1>

      {/* Main Content Area */}
      <div className="w-full max-w-2xl mx-auto">
        {/* Real Post Display */}
        {isLoadingPost ? (
          <div className="bg-white p-6 rounded-lg shadow-lg mb-8 flex justify-center items-center h-48">
            <div className="text-gray-500">Loading post...</div>
          </div>
        ) : currentPost ? (
          <div className="bg-white p-6 rounded-lg shadow-lg mb-8">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-blue-200 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-bold">
                  {currentPost.author_did.slice(0, 2).toUpperCase()}
                </span>
              </div>
              <div className="ml-4">
                <h3 className="font-semibold text-gray-800">{currentPost.author_did}</h3>
                <p className="text-sm text-gray-500">{currentPost.uri}</p>
              </div>
              <span className="ml-auto text-sm text-gray-400">
                {new Date(currentPost.created_at).toLocaleString()}
              </span>
            </div>
            <p className="text-gray-700 text-lg mb-4">{currentPost.text}</p>
            <div className="flex items-center justify-between text-gray-500 text-sm">
              <button 
                onClick={fetchNextPost}
                className="bg-blue-100 hover:bg-blue-200 text-blue-600 font-semibold py-2 px-4 rounded-lg transition duration-200 ease-in-out"
              >
                Next Post →
              </button>
              <span className="text-xs text-gray-400">CID: {currentPost.cid.slice(0, 10)}...</span>
            </div>
          </div>
        ) : (
          <div className="bg-white p-6 rounded-lg shadow-lg mb-8 flex justify-center items-center h-48">
            <div className="text-gray-500">No post available</div>
          </div>
        )}

        {/* Auth Section */}
        <div className="w-full flex flex-col items-center bg-white p-8 rounded-lg shadow-lg">
          {!isAuthenticated ? (
            <div className="flex flex-col items-center space-y-4 w-full max-w-md">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">Join the conversation</h2>
              <input
                type="text"
                placeholder="Your handle (e.g. you.bsky.social)"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
              />
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <button
                onClick={handleLogin}
                disabled={isLoading || !handle}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Connecting...' : 'Login with Bluesky'}
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center space-y-4">
              <p className="text-gray-700">Logged in as: <span className="font-semibold">{userDid}</span></p>
              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-6 rounded-lg transition duration-200 ease-in-out"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
