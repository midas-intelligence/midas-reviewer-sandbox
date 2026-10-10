import type { Note } from "../types";

interface Props {
  notes: Note[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function NoteList({ notes, selectedId, onSelect }: Props) {
  if (notes.length === 0) {
    return <p className="empty">No notes yet.</p>;
  }

  return (
    <ul className="note-list">
      {notes.map((note) => (
        <li key={note.id} className={note.id === selectedId ? "note selected" : "note"}>
          <button type="button" onClick={() => onSelect(note.id)}>
            <span className="title">{note.title}</span>
            <span className="meta">
              {note.visibility} · {new Date(note.updated_at).toLocaleDateString()}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
