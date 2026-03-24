'use client';
import { useEffect, useCallback } from 'react';

export default function useKeyboardShortcuts(shortcuts) {
  const handler = useCallback((e) => {
    const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);
    const hasMeta = e.metaKey || e.ctrlKey;

    for (const s of shortcuts) {
      const keyMatch = e.key.toLowerCase() === s.key.toLowerCase();
      const metaMatch = s.meta ? hasMeta : !hasMeta;
      const shiftMatch = s.shift ? e.shiftKey : true;

      if (keyMatch && metaMatch && shiftMatch) {
        if (isInput && !hasMeta) continue;
        e.preventDefault();
        s.action();
        return;
      }
    }
  }, [shortcuts]);

  useEffect(() => {
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [handler]);
}
