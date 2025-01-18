"use client";

import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    const uri = "wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos";

    const websocket = new WebSocket(uri);

    websocket.onopen = () => {
      console.log("WebSocket connection established.");
    };

    websocket.onmessage = (event) => {
      console.log("Message received:", event.data);
      // Process the incoming data if needed
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    websocket.onclose = () => {
      console.log("WebSocket connection closed.");
    };

    return () => {
      websocket.close();
      console.log("WebSocket connection cleaned up.");
    };
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-50">
      <h1 className="text-2xl font-bold">Firehose Connection</h1>
      <p className="mt-4 text-center">
        The WebSocket connection is active. Check the browser console for events
        received from the firehose.
      </p>
    </div>
  );
}
