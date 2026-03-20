import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function POST() {
  const cookieStore = await cookies();
  const rawToken = cookieStore.get('better-auth.session_token')?.value;
  if (!rawToken) {
    return NextResponse.json({ error: 'No session' }, { status: 401 });
  }

  // Better Auth cookie format is "token.signature" — extract just the token
  const sessionToken = rawToken.split('.')[0];

  const apiUrl = process.env.API_URL || 'http://localhost:8000';
  const res = await fetch(`${apiUrl}/api/v1/auth/session-exchange`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_token: sessionToken }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return NextResponse.json(
      { error: err.detail || 'Exchange failed' },
      { status: res.status }
    );
  }

  const data = await res.json();
  return NextResponse.json(data);
}
