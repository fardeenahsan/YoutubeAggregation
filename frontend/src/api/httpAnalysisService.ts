import { AnalysisError, toAnalysisError } from './errors';
import type { AnalysisService, RequestOptions, RunAnalysisOptions } from './service';
import type { AnalysisRequest, AnalysisResult, CommentFilter, CommentPage } from './types';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init.headers },
    });
  } catch (error) {
    throw toAnalysisError(error);
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload?.detail?.error ?? payload?.error ?? {};
    const code = detail.code ?? 'UNKNOWN';
    throw new AnalysisError(
      code === 'INVALID_CHANNEL' || code === 'COMMENTS_UNAVAILABLE' || code === 'QUOTA_EXHAUSTED' ? code : 'UNKNOWN',
      detail.message ?? `Request failed (${response.status}).`,
      { retryAt: detail.retryAt ?? null },
    );
  }
  return payload as T;
}

export function createHttpAnalysisService(): AnalysisService {
  return {
    source: 'youtube',
    async runAnalysis(input: AnalysisRequest, options: RunAnalysisOptions = {}): Promise<AnalysisResult> {
      options.onProgress?.({ status: 'running', progress: 5, step: 'Submitting analysis' });
      try {
        const job = await request<{ key: string; status: string; progress: number; step: string; result: AnalysisResult | null; error: {code:string;message:string} | null }>(
          '/analyses',
          { method: 'POST', body: JSON.stringify(input), signal: options.signal },
        );
        options.onProgress?.({ status: job.status as 'running' | 'done' | 'error', progress: job.progress, step: job.step });
        if (job.status !== 'done' || !job.result) {
          throw new AnalysisError('UNKNOWN', job.error?.message ?? 'The analysis did not return a result.');
        }
        return { ...job.result, key: job.key };
      } catch (error) {
        throw toAnalysisError(error);
      }
    },
    async getComments(key: string, filter: CommentFilter, options: RequestOptions = {}): Promise<CommentPage> {
      const params = new URLSearchParams();
      for (const field of ['period', 'sentiment', 'keyword', 'cursor', 'limit'] as const) {
        const value = filter[field];
        if (value !== undefined && value !== null && value !== '') params.set(field, String(value));
      }
      try {
        return await request<CommentPage>(`/analyses/${encodeURIComponent(key)}/comments?${params}`, { signal: options.signal });
      } catch (error) {
        throw toAnalysisError(error);
      }
    },
  };
}
