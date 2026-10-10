import { useState } from "react";

import { api } from "../api";
import type { Note } from "../types";

interface Props {
  note: Note;
  onSaved: (note: Note) => void;
}

export function NoteEditor({ note, onSaved }: Props) {
  const [title, setTitle] = useState(note.title);
  const [body, setBody] = useState(note.body);
  const [saving, setSaving] = useState(false);

  async function save(): Promise<void> {
    setSaving(true);
    try {
      onSaved(await api.updateNote(note.id, { title, body }));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      className="note-editor"
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <input value={title} onChange={(event) => setTitle(event.target.value)} aria-label="Title" />
      <textarea value={body} onChange={(event) => setBody(event.target.value)} aria-label="Body" />
      <button type="submit" disabled={saving}>
        {saving ? "Saving…" : "Save"}
      </button>
    </form>
  );
}
