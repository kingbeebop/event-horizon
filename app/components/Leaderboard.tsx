'use client';

import { useEffect, useState, useImperativeHandle, forwardRef } from 'react';
import { Post } from '@/types';

interface LeaderboardPost extends Post {
  likes: number;
  dislikes: number;
  double_dislikes: number;
}

export interface LeaderboardRef {
  refresh: () => Promise<void>;
}

const Leaderboard = forwardRef<LeaderboardRef>((_, ref) => {
  const [posts, setPosts] = useState<LeaderboardPost[]>([]);

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/posts/leaderboard/');
      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }
      const data = await response.json();
      if (data.success && Array.isArray(data.posts)) {
        setPosts(data.posts);
      }
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  useImperativeHandle(ref, () => ({
    refresh: fetchLeaderboard
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-semibold mb-4">Top Posts</h2>
      <div className="space-y-4">
        {posts.map((post, index) => (
          <div key={post.cid} className="border-b last:border-b-0 pb-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-bold text-lg text-blue-600">#{index + 1}</span>
              <span className="text-sm text-gray-500">{post.author_did}</span>
            </div>
            <p className="text-gray-700 mb-2">{post.text}</p>
            <div className="flex gap-4 text-sm text-gray-500">
              <span>👍 {post.likes}</span>
              <span>👎 {post.dislikes}</span>
              <span>👎👎 {post.double_dislikes}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

Leaderboard.displayName = 'Leaderboard';

export default Leaderboard; 