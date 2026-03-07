const PLAN_FROM_UPLOAD_RE = /^(generate|create|build)\s+(?:a\s+)?plan\s+from\s+upload\s*$/i;
const RESPONSE_FROM_UPLOAD_RE = /^(generate|create|build)\s+(?:a\s+)?response\s+from\s+upload\s*$/i;
const PLAN_RE = /^(generate|create|build)\s+(?:a\s+)?plan\s+(?:for\s+)?(.+)$/i;
export const MODEL_RE = /^(build|model|show|make|create)\s+(me\s+)?(?:a\s+)?(.+)$/i;

export function parseChatCommand(input) {
  const text = input.trim();
  if (!text) return { type: 'none' };
  if (PLAN_FROM_UPLOAD_RE.test(text)) return { type: 'plan_from_upload' };
  if (RESPONSE_FROM_UPLOAD_RE.test(text)) return { type: 'response_from_upload' };

  const planMatch = text.match(PLAN_RE);
  if (planMatch) {
    return {
      type: 'plan',
      query: (planMatch[2] || text).trim(),
    };
  }

  const modelMatch = text.match(MODEL_RE);
  if (modelMatch) {
    return {
      type: 'model',
      query: text,
    };
  }

  return { type: 'none' };
}
