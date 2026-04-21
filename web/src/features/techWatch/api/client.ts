import { api } from '@/lib/api/client';

import type { TagStat,TechArticle } from '../types';

export async function getFeaturedArticles(limit = 20): Promise<TechArticle[]> {
  return api.get<TechArticle[]>(`/tech-watch/articles/featured?limit=${limit}`);
}

export async function getTagStats(): Promise<TagStat[]> {
  return api.get<TagStat[]>('/tech-watch/tags/stats');
}
