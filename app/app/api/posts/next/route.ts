import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Proxy the request to Django backend
    const response = await fetch('http://localhost:8000/api/posts/next/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching next post:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch next post' },
      { status: 500 }
    );
  }
} 