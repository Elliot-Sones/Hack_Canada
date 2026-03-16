"use client";

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import LandingPage from './components/LandingPage';

export default function Home() {
  const router = useRouter();

  const handleNavigate = useCallback((address?: string) => {
    if (address) {
      router.push(`/dashboard?address=${encodeURIComponent(address)}`);
    } else {
      router.push('/dashboard');
    }
  }, [router]);

  return <LandingPage onNavigate={handleNavigate} />;
}
