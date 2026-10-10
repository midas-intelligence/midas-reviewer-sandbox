export type Visibility = "private" | "shared" | "public";

export interface Note {
  id: number;
  owner_id: number;
  title: string;
  body: string;
  visibility: Visibility;
  created_at: string;
  updated_at: string;
}

export interface NotePage {
  items: Note[];
  total: number;
  limit: number;
  offset: number;
}

export interface Session {
  token: string;
  user: { id: number; email: string; role: string };
}
