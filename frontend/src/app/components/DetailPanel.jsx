'use client';

import React from 'react';
import { Building2, ChevronLeft } from 'lucide-react';
import Tabs from './ui/Tabs.jsx';
import { PipelineStepper } from './ui/Progress.jsx';
import EmptyState from './ui/EmptyState.jsx';
import useResizable from '../hooks/useResizable.js';

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'policies', label: 'Policies' },
  { id: 'infrastructure', label: 'Infrastructure' },
  { id: 'chat', label: 'Chat' },
  { id: 'documents', label: 'Documents' },
];

const TAB_TO_NAV = {
  overview: 'overview',
  policies: 'policies',
  infrastructure: 'infrastructure',
  documents: 'documents',
};

function derivePipelineSteps(pipelineStatus) {
  if (!pipelineStatus) {
    return [
      { label: 'Search', status: 'pending' },
      { label: 'Analyze', status: 'pending' },
      { label: 'Infrastructure', status: 'pending' },
      { label: 'Complete', status: 'pending' },
    ];
  }
  return [
    { label: 'Search', status: pipelineStatus.search || 'pending' },
    { label: 'Analyze', status: pipelineStatus.analyze || 'pending' },
    { label: 'Infrastructure', status: pipelineStatus.infrastructure || 'pending' },
    { label: 'Complete', status: pipelineStatus.complete || 'pending' },
  ];
}

export default function DetailPanel({
  activeTab = 'overview',
  onTabChange,
  isOpen = true,
  onToggle,
  parcel,
  pipelineStatus,
  chatPanelProps,
  policyPanelProps,
  renderPolicyContent,
  renderChatContent,
}) {
  const { size, handleProps } = useResizable({
    defaultSize: 380,
    minSize: 300,
    maxSize: 500,
    axis: 'horizontal',
    reverse: true,
    cssVar: '--panel-width',
  });

  const steps = derivePipelineSteps(pipelineStatus);

  // Collapsed state — thin reopen bar
  if (!isOpen) {
    return (
      <div
        className="detail-panel-reopen"
        onClick={onToggle}
        title="Open detail panel"
      >
        <ChevronLeft size={14} />
      </div>
    );
  }

  return (
    <div
      className="detail-panel"
      style={{ width: size }}
    >
      {/* Resize handle */}
      <div {...handleProps} style={{ ...handleProps.style, left: 0 }} />

      {/* Pipeline stepper — only when a parcel is selected */}
      {parcel && (
        <div className="detail-panel-stepper">
          <PipelineStepper steps={steps} style={{ justifyContent: 'center' }} />
        </div>
      )}

      {/* Tab bar */}
      <Tabs
        tabs={TABS}
        active={activeTab}
        onChange={onTabChange}
        style={{ paddingInline: 'var(--space-sm)', flexShrink: 0 }}
      />

      {/* Content area */}
      <div className={`detail-panel-content${activeTab === 'chat' ? ' detail-panel-content--chat' : ''}`}>
        {!parcel ? (
          <EmptyState
            icon={Building2}
            title="Select a parcel"
            description="Choose a parcel from the sidebar or search to view details"
          />
        ) : activeTab === 'chat' ? (
          renderChatContent ? renderChatContent() : null
        ) : (
          renderPolicyContent ? renderPolicyContent(TAB_TO_NAV[activeTab] || activeTab) : null
        )}
      </div>
    </div>
  );
}
