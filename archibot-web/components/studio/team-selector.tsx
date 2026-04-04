"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, Plus, Users } from "lucide-react";
import { useStudio } from "@/components/studio/studio-context";

export function TeamSelector() {
  const { teams, activeTeamId, selectTeam, addTeam } = useStudio();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const activeTeam = teams.find((t) => t.id === activeTeamId);

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setCreating(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  async function handleCreate() {
    const trimmed = newName.trim();
    if (!trimmed) return;
    await addTeam(trimmed);
    setNewName("");
    setCreating(false);
    setOpen(false);
  }

  return (
    <div className="team-selector" ref={ref}>
      <button
        className="team-selector__trigger"
        onClick={() => setOpen((o) => !o)}
      >
        <Users size={14} />
        <span>{activeTeam?.name ?? "Select a team"}</span>
        <ChevronDown size={13} className={open ? "team-selector__chevron--open" : ""} />
      </button>

      {open && (
        <div className="team-selector__dropdown">
          {teams.length === 0 && !creating && (
            <p className="team-selector__empty">No teams yet.</p>
          )}

          {teams.map((team) => (
            <button
              key={team.id}
              className={`team-selector__option${team.id === activeTeamId ? " active" : ""}`}
              onClick={() => {
                selectTeam(team.id);
                setOpen(false);
              }}
            >
              <span>{team.name}</span>
              {team.id === activeTeamId && <Check size={13} />}
            </button>
          ))}

          <div className="team-selector__divider" />

          {creating ? (
            <div className="team-selector__create">
              <input
                autoFocus
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreate();
                  if (e.key === "Escape") {
                    setCreating(false);
                    setNewName("");
                  }
                }}
                placeholder="Team name"
              />
              <button
                className="team-selector__create-btn"
                onClick={handleCreate}
                disabled={!newName.trim()}
              >
                Add
              </button>
            </div>
          ) : (
            <button
              className="team-selector__option team-selector__option--add"
              onClick={() => setCreating(true)}
            >
              <Plus size={14} />
              <span>New team</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
