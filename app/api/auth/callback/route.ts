import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  const error = searchParams.get('error');
  const errorDescription = searchParams.get('error_description');
  
  // Handle OAuth errors
  if (error) {
    console.error('OAuth error:', error, errorDescription);
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_APP_URL}?error=${error}&description=${errorDescription}`
    );
  }

  // Verify required parameters
  if (!code || !state) {
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_APP_URL}?error=missing_params`
    );
  }
  
  // Verify state parameter using cookies
  const cookieStore = await cookies();
  const storedState = cookieStore.get('bsky_oauth_state')?.value;
  
  if (!state || state !== storedState) {
    return NextResponse.redirect(`${process.env.NEXT_PUBLIC_APP_URL}?error=invalid_state`);
  }
  
  try {
    
    // Exchange the code for an access token
    const tokenResponse = await fetch('https://bsky.social/xrpc/com.atproto.server.createSession', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        identifier: process.env.BSKY_CLIENT_ID,
        password: process.env.BSKY_CLIENT_SECRET,
      }),
    });

    const data = await tokenResponse.json();
    
    if (!tokenResponse.ok) {
      console.error('Token exchange failed:', data);
      throw new Error(data.error || 'Failed to exchange code for token');
    }

    // Store the access token securely
    const cookieOptions = {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax' as const,
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 1 week
    };

    // Create response and set cookies
    const redirectUrl = new URL(`${process.env.NEXT_PUBLIC_APP_URL}?success=true`);
    const response = NextResponse.redirect(redirectUrl);
    
    // Set cookies using the proper Next.js 13+ API
    response.cookies.set('bsky_oauth_state', '', { maxAge: 0 });
    response.cookies.set('bsky_access_token', data.accessJwt, cookieOptions);
    response.cookies.set('bsky_refresh_token', data.refreshJwt, cookieOptions);
    
    return response;
  } catch (error) {
    console.error('OAuth callback error:', error);
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_APP_URL}?error=auth_failed&description=${encodeURIComponent(
        error instanceof Error ? error.message : 'Unknown error'
      )}`
    );
  }
} 