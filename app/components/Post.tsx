import { Post as PostType } from '@/types';
import PostInteractionButtons from './PostInteractionButtons';

export default function Post({ post }: { post: PostType }) {
  return (
    <div className="border rounded-lg p-4 mb-4 bg-white shadow">
      <div className="flex items-center mb-4">
        <div className="w-12 h-12 bg-blue-200 rounded-full flex items-center justify-center">
          <span className="text-blue-600 font-bold">
            {post.author_did.slice(0, 2).toUpperCase()}
          </span>
        </div>
        <div className="ml-4">
          <h3 className="font-semibold text-gray-800">{post.author_did}</h3>
          <p className="text-sm text-gray-500">{post.uri}</p>
        </div>
        <span className="ml-auto text-sm text-gray-400">
          {new Date(post.created_at).toLocaleString()}
        </span>
      </div>
      <p className="text-gray-700 text-lg mb-4">{post.text}</p>
      <PostInteractionButtons post={post} />
    </div>
  );
} 