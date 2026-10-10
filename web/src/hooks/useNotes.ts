import { useCallback, useEffect, useState } from "react";

import { api } from "../api";
import type { Note } from "../types";

interface NotesState {
  notes: Note[];
  total: number;
  loading: boolean;
  error: string | null;
}

export function useNotes(limit = 25) {
  const [page, setPage] = useState(0);
  const [state, setState] = useState<NotesState>({ notes: [], total: 0, loading: true, error: null });

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await api.listNotes(page, limit);
      setState({ notes: result.items, total: result.total, loading: false, error: null });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error: String(error) }));
    }
  }, [page, limit]);

  useEffect(() => {
    void load();
  }, [load]);

  const pageCount = Math.max(1, Math.ceil(state.total / limit));

  return { ...state, page, pageCount, setPage, reload: load };
}
