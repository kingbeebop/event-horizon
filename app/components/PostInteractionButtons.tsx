'use client';

import { Post } from '@/types';

interface PostInteractionButtonsProps {
  post: Post;
}

export default function PostInteractionButtons({ post }: PostInteractionButtonsProps) {
  const handleInteraction = async (liked: boolean) => {
    try {
      const response = await fetch('http://localhost:8000/api/posts/interact/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_cid: post.cid,
          liked: liked
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to record interaction');
      }
    } catch (error) {
      console.error('Error recording interaction:', error);
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
    </div>
  );
} 