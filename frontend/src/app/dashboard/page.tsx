"use client";

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardView from '../components/DashboardView';

function DashboardContent() {
  const searchParams = useSearchParams();
  const address = searchParams.get('address');
  return <DashboardView initialAddress={address || undefined} />;
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#fafafa' }}><p>Loading...</p></div>}>
      <DashboardContent />
    </Suspense>
  );
}
