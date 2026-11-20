import { AnalysisError, toAnalysisError } from './errors';
import type { AnalysisService, RequestOptions, RunAnalysisOptions } from './service';
import type { AnalysisRequest, AnalysisResult, CommentFilter, CommentPage } from './types';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

type AnalysisJobResponse = {
  key: string;
  status: 'queued' | 'running' | 'done' | 'error';
  progress: number;
  step: string;
  result: AnalysisResult | null;
  error: { code: string; message: string } | null;
};

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

function reportProgress(job: AnalysisJobResponse, options: RunAnalysisOptions): void {
  options.onProgress?.({
    status: job.status,
    progress: job.progress,
    step: job.step,
  });
}

export function createHttpAnalysisService(): AnalysisService {
  return {
    source: 'youtube',
    async runAnalysis(input: AnalysisRequest, options: RunAnalysisOptions = {}): Promise<AnalysisResult> {
      options.onProgress?.({ status: 'running', progress: 2, step: 'Submitting analysis' });

      try {
        let job = await request<AnalysisJobResponse>(
          '/analyses',
          { method: 'POST', body: JSON.stringify(input), signal: options.signal },
        );
        reportProgress(job, options);

        // The API returns a job immediately. Poll until it reaches a terminal state.
        const deadline = Date.now() + 10 * 60 * 1000;
        while (job.status === 'queued' || job.status === 'running') {
          if (options.signal?.aborted) {
            throw new DOMException('Analysis cancelled.', 'AbortError');
          }
          if (Date.now() >= deadline) {
            throw new AnalysisError('UNKNOWN', 'Analysis timed out after 10 minutes. Try a shorter date range.');
          }

          await new Promise<void>((resolve) => window.setTimeout(resolve, 1000));
          job = await request<AnalysisJobResponse>(
            `/analyses/${encodeURIComponent(job.key)}`,
            { signal: options.signal },
          );
          reportProgress(job, options);
        }

        if (job.status === 'error') {
          throw new AnalysisError('UNKNOWN', job.error?.message ?? 'The analysis failed.');
        }
        if (!job.result) {
          throw new AnalysisError('UNKNOWN', 'The analysis finished without returning a result.');
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
