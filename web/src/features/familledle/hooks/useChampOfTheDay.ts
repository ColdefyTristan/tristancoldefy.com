import { useCallback, useEffect, useState } from "react";
import { getChampOfTheDay } from "../api/client";
import type { ChampDataResponse } from "../types";

export type UseChampOfTheDayResult = {
  champOfTheDay: ChampDataResponse | null;
  isLoading: boolean;
  error: unknown | null;
  reload: () => void;
};

export function useChampOfTheDay(): UseChampOfTheDayResult {
  const [champOfTheDay, setChampOfTheDay] = useState<ChampDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<unknown | null>(null);
  const [reloadToken, setReloadToken] = useState<number>(0);

  const reload = useCallback(() => {
    setReloadToken((previous) => previous + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setIsLoading(true);
      setError(null);

      try {
        const fetchedChampOfTheDay = await getChampOfTheDay();
        if (cancelled) return;
        setChampOfTheDay(fetchedChampOfTheDay);
      } catch (caughtError) {
        if (cancelled) return;
        setChampOfTheDay(null);
        setError(caughtError);
      } finally {
        if (cancelled) return;
        setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  return { champOfTheDay, isLoading, error, reload };
}