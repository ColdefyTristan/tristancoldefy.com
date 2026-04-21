import { useCallback, useEffect, useState } from "react";

import { getChampData, getDailyGame } from "../api/client";
import type { ChampDataResponse, DailyGameResponse } from "../types";

export type UseDailyGameResult = {
  dailyGame: DailyGameResponse | null;
  champOfTheDay: ChampDataResponse | null;
  isLoading: boolean;
  error: unknown | null;
  reload: () => void;
};

export function useDailyGame(): UseDailyGameResult {
  const [dailyGame, setDailyGame] = useState<DailyGameResponse | null>(null);
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
        const game = await getDailyGame();
        if (cancelled) return;

        const champData = await getChampData(game.champ_name);
        if (cancelled) return;

        setDailyGame(game);
        setChampOfTheDay(champData);
      } catch (caughtError) {
        if (cancelled) return;
        setDailyGame(null);
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

  return { dailyGame, champOfTheDay, isLoading, error, reload };
}
