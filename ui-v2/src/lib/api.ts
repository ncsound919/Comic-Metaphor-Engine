/**
 * API client for the Comic Metaphor Engine backend.
 *
 * The backend URL is configurable via VITE_API_URL (defaults to the local
 * FastAPI server on :8000). On Vercel, set VITE_API_URL to the deployed API.
 */

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

export interface ProtocolSummary {
  id: string;
  protocol_type: string;
  archetype: string;
  business_logic: string;
  themes: string[];
  risk_categories: string[];
  tone_compatibility: string[];
}

export interface ProtocolDetail extends ProtocolSummary {
  application: string;
  narrative: string;
  business_translation: string;
  dimensions: Dimension[];
  vector_entry: Record<string, unknown>;
}

export interface Dimension {
  id: string;
  title: string;
  science_concept: string;
  character_anchor: string;
  analysis: string;
  lesson: string;
  metric: string;
}

export interface SearchResult {
  protocol_id: string;
  similarity: number;
  archetype: string;
  business_logic: string;
  themes: string[];
  protocol_type: string;
}

export interface Mapping {
  id: string;
  topic: string;
  domain: string;
  target_format: string;
  target_tone: string;
  protocol_id: string;
  core_tension: string;
  target_emotion: string;
  mappings: Array<{ real_world: string; comic_analog: string; explanation: string; confidence: number }>;
  narrative_pattern: string;
  beat_structure: string[];
  trueness_score: number;
  flow_score: number;
  pcs_score: number;
  overall_fit: number;
  tap_score: number;
}

export interface Explanation {
  mapping_id: string;
  audience: string;
  tone: string;
  summary: string;
  detailed_explanation: string;
  key_takeaways: string[];
  life_application: string;
  action_items: string[];
}

export interface Lesson {
  lesson_id: string;
  title: string;
  hook: string;
  story: string;
  translation: string;
  takeaways: string[];
  actions: string[];
  tone: string;
  protocol_id: string;
}

export interface Narrative {
  id: string;
  mapping_id: string;
  format_type: string;
  title: string;
  content: string;
  word_count: number;
  codex_scores: Record<string, number>;
}

export interface Health {
  status: string;
  service: string;
  version: string;
  protocols_loaded: number;
}

export interface Comic {
  id: string;
  filename: string;
  status: 'processing' | 'ready' | 'failed' | 'unsupported';
  page_count: number;
  size_bytes: number;
  created_at?: string;
  error?: string;
}

export interface InsightReport {
  report_id: string;
  source_file: string;
  title: string;
  characters: string[];
  themes: string[];
  keywords: string[];
  word_count: number;
  protocol_id: string | null;
  codex_scores: Record<string, number>;
  mappings: Array<{ real_world: string; comic_analog: string; explanation: string; confidence: number }>;
  lessons: Record<string, unknown>;
  takeaways: string[];
  action_items: string[];
  summary: string;
}

export interface MeResponse {
  user: { plan?: string; subscription_status?: string };
}

async function request<T>(path: string, options?: RequestInit, token?: string): Promise<T> {
  const headers: Record<string, string> = { ...(options?.headers as Record<string, string>) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>('/health'),
  listProtocols: (params?: { protocol_type?: string; archetype?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.protocol_type) q.set('protocol_type', params.protocol_type);
    if (params?.archetype) q.set('archetype', params.archetype);
    if (params?.limit) q.set('limit', String(params.limit));
    const qs = q.toString();
    return request<{ count: number; protocols: ProtocolSummary[] }>(
      `/api/protocols${qs ? `?${qs}` : ''}`
    );
  },
  getProtocol: (id: string) => request<ProtocolDetail>(`/api/protocols/${id}`),
  search: (query: string, topK = 5) =>
    request<{ query: string; latency_ms: number; results: SearchResult[] }>('/api/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    }),
  map: (topic: string, format = 'podcast_monologue', tone = 'hopeful', topK = 5) =>
    request<Mapping>('/api/map', {
      method: 'POST',
      body: JSON.stringify({ topic, format, tone, top_k: topK }),
    }),
  explain: (topic: string, format = 'podcast_monologue', tone = 'hopeful', audience = 'general') =>
    request<{ mapping: Mapping; explanation: Explanation }>('/api/explain', {
      method: 'POST',
      body: JSON.stringify({ topic, format, tone, audience }),
    }),
  lesson: (topic: string, format = 'podcast_monologue', tone = 'hopeful') =>
    request<{ mapping: Mapping; lesson: Lesson }>('/api/lesson', {
      method: 'POST',
      body: JSON.stringify({ topic, format, tone }),
    }),
  narrative: (topic: string, format = 'podcast_monologue', tone = 'hopeful', wordCountTarget = 600) =>
    request<{ mapping: Mapping; narrative: Narrative }>('/api/narrative', {
      method: 'POST',
      body: JSON.stringify({ topic, format, tone, word_count_target: wordCountTarget }),
    }),

  // --- SaaS endpoints (authenticated) ---
  me: (token: string) => request<MeResponse>('/api/me', { method: 'GET' }, token),
  uploadComic: async (file: File, token: string) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`API ${res.status}: ${body.slice(0, 200)}`);
    }
    return res.json() as Promise<{ comic: Comic; insight: InsightReport | null; message?: string }>;
  },
  listComics: (token: string) =>
    request<{ comics: Comic[] }>('/api/comics', { method: 'GET' }, token),
  getInsights: (comicId: string, token: string) =>
    request<{ insight: InsightReport }>(`/api/comics/${comicId}/insights`, { method: 'GET' }, token),
  billingCheckout: (token: string) =>
    request<{ url: string }>('/api/billing/checkout', { method: 'POST' }, token),
  billingPortal: (token: string) =>
    request<{ url: string }>('/api/billing/portal', { method: 'POST' }, token),
};
