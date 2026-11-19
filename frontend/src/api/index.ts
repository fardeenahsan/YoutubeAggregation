import { createMockAnalysisService } from '../mock/mockAnalysisService';
import type { AnalysisService } from './service';
import { createHttpAnalysisService } from './httpAnalysisService';

export type { AnalysisService } from './service';
export { AnalysisError, type AnalysisErrorCode } from './errors';

/** Set VITE_API_BASE_URL to use the live FastAPI service; otherwise use demo data. */
export function createAnalysisService(): AnalysisService {
  return import.meta.env.VITE_API_BASE_URL
    ? createHttpAnalysisService()
    : createMockAnalysisService();
}
