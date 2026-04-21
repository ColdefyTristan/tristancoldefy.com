export type TechArticle = {
  id: number;
  url: string;
  title: string;
  source: string;
  priority: number;
  interest_score: number | null;
  published_at: string | null;
  summary: string | null;
  summarized: boolean;
  tags: string[] | null;
  created_at: string;
};

export type TagStat = {
  name: string;
  count: number;
};
