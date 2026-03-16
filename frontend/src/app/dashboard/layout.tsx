"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from '../lib/auth-client.js';
import { Providers } from '../Providers';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { data: session, isPending } = useSession();

  useEffect(() => {
    if (!isPending && !session) {
      router.replace('/login');
    }
  }, [isPending, session, router]);

  if (isPending) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#fafafa' }}>
        <p>Loading...</p>
      </div>
    );
  }

  if (!session) return null;

  return <>{children}</>;
}
