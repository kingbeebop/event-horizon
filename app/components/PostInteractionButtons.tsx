'use client';

import { Post } from '@/types';
import { RefObject } from 'react';
import { LeaderboardRef } from './Leaderboard';

interface PostInteractionButtonsProps {
  post: Post;
  onNextPost?: (response: { success: boolean; post: Post }) => void;
  leaderboardRef: RefObject<LeaderboardRef>;
}

export default function PostInteractionButtons({ post, onNextPost, leaderboardRef }: PostInteractionButtonsProps) {
  const handleInteraction = async (liked: boolean, double_dislike: boolean = false) => {
    try {
      const response = await fetch('http://localhost:8000/api/posts/interact/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_cid: post.cid,
          post_uri: post.uri,
          author_did: post.author_did,
          post_text: post.text,
          created_at: post.created_at,
          liked: liked,
          double_dislike: double_dislike
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to record interaction');
      }

      const nextPostResponse = await fetch('/api/posts/next');
      if (!nextPostResponse.ok) {
        throw new Error('Failed to fetch next post');
      }

      const nextPostData = await nextPostResponse.json();
      if (nextPostData.success && nextPostData.post) {
        onNextPost?.(nextPostData);
        await leaderboardRef.current?.refresh();
      } else {
        throw new Error('Invalid next post data');
      }
    } catch (error) {
      console.error('Error handling interaction:', error);
    }
  };

  return (
    <div className="flex gap-4 mt-4">
      <button
        onClick={() => handleInteraction(true)}
        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
      >
        Yay 👍
      </button>
      <button
        onClick={() => handleInteraction(false)}
        className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
      >
        Nay 👎
      </button>
      <button
        onClick={() => handleInteraction(false, true)}
        className="px-4 py-2 bg-red-700 text-white rounded hover:bg-red-800 transition-colors"
      >
        Double Nay 👎👎
      </button>
    </div>
  );
} 