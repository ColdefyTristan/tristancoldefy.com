import { notFound } from 'next/navigation';

import MtgDokuPage, { Difficulty } from '@/features/mtgdoku/ui/MtgDokuPage';

const VALID: Difficulty[] = ['easy', 'medium', 'hard'];

export default async function Page({ params }: { params: Promise<{ difficulty: string }> }) {
  const { difficulty } = await params;
  if (!VALID.includes(difficulty as Difficulty)) notFound();
  return <MtgDokuPage difficulty={difficulty as Difficulty} />;
}
