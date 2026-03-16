"use client";

import { use } from 'react';
import DashboardView from '../../components/DashboardView';

export default function ParcelDashboardPage({ params }: { params: Promise<{ parcelId: string }> }) {
  const { parcelId } = use(params);
  return <DashboardView initialAddress={undefined} parcelId={parcelId} />;
}
