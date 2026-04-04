"use client";

import { useEffect, useRef, useState } from "react";
import {
  Check,
  ChevronDown,
  Folder,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  Map,
  MessageSquare,
  PanelLeft,
  PanelLeftClose,
  PanelsTopLeft,
  Plus,
  Settings,
  Users,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { useStudio } from "@/components/studio/studio-context";
import { type StudioTab } from "@/components/studio/studio-tabs";

type SidebarState = "hidden" | "compact" | "full";

const NAV_ITEMS: { id: StudioTab; label: string; icon: React.ElementType }[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "team", label: "Team", icon: Users },
  { id: "projects", label: "Projects", icon: Folder },
  { id: "conversation", label: "Conversation", icon: MessageSquare },
  { id: "workspace", label: "Workspace", icon: PanelsTopLeft },
  { id: "playground", label: "Playground", icon: Map },
];

const BOTTOM_ITEMS: { id?: StudioTab; label: string; icon: React.ElementType }[] = [
  { label: "Help", icon: HelpCircle },
  { id: "settings", label: "Settings", icon: Settings },
];

function getInitials(name: string | null | undefined, email: string | null | undefined) {
  if (name) return name.slice(0, 2).toUpperCase();
  if (email) return email[0].toUpperCase();
  return "?";
}

function getDisplayName(name: string | null | undefined, email: string | null | undefined) {
  return name ?? email ?? "Account";
}

function TeamDropdown({ compact }: { compact: boolean }) {
  const { teams, activeTeamId, selectTeam, addTeam } = useStudio();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const activeTeam = teams.find((t) => t.id === activeTeamId);

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
    <div className="sidebar-team" ref={ref}>
      <button
        className="sidebar-team__trigger"
        onClick={() => setOpen((o) => !o)}
        title={compact ? (activeTeam?.name ?? "Select a team") : undefined}
      >
        <Users size={compact ? 17 : 14} />
        {!compact && (
          <>
            <span className="sidebar-team__name">
              {activeTeam?.name ?? "Select a team"}
            </span>
            <ChevronDown
              size={13}
              className={open ? "sidebar-team__chevron--open" : ""}
            />
          </>
        )}
      </button>

      {open && (
        <div className="sidebar-team__dropdown">
          {teams.length === 0 && !creating && (
            <p className="sidebar-team__empty">No teams yet.</p>
          )}

          {teams.map((team) => (
            <button
              key={team.id}
              className={`sidebar-team__option${team.id === activeTeamId ? " active" : ""}`}
              onClick={() => {
                selectTeam(team.id);
                setOpen(false);
              }}
            >
              <span>{team.name}</span>
              {team.id === activeTeamId && <Check size={13} />}
            </button>
          ))}

          <div className="sidebar-team__divider" />

          {creating ? (
            <div className="sidebar-team__create">
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
                className="sidebar-team__create-btn"
                onClick={handleCreate}
                disabled={!newName.trim()}
              >
                Add
              </button>
            </div>
          ) : (
            <button
              className="sidebar-team__option sidebar-team__option--add"
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

export function Sidebar() {
  const { activeTab, setActiveTab } = useStudio();
  const { user, logout } = useAuth();
  const [state, setState] = useState<SidebarState>("full");

  function cycle() {
    setState((s) => (s === "full" ? "compact" : s === "compact" ? "hidden" : "full"));
  }

  // ── Hidden state: just a floating toggle ──────────────────
  if (state === "hidden") {
    return (
      <button className="sidebar-expand-btn" onClick={cycle} aria-label="Expand sidebar">
        <PanelLeft size={15} />
      </button>
    );
  }

  const compact = state === "compact";

  return (
    <aside className={compact ? "sidebar sidebar--compact" : "sidebar sidebar--full"}>
      {/* Team dropdown + toggle */}
      <div className="sidebar__top">
        <TeamDropdown compact={compact} />
        <button
          className="sidebar__icon-btn"
          onClick={cycle}
          aria-label={compact ? "Expand sidebar" : "Collapse sidebar"}
        >
          {compact ? <PanelLeft size={15} /> : <PanelLeftClose size={15} />}
        </button>
      </div>

      {/* Main nav */}
      <nav className="sidebar__nav">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`sidebar__item${activeTab === id ? " active" : ""}`}
            onClick={() => setActiveTab(id)}
            title={compact ? label : undefined}
          >
            <Icon size={17} />
            {!compact && <span>{label}</span>}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar__footer">
        {BOTTOM_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={label}
            className={`sidebar__item${id && activeTab === id ? " active" : ""}`}
            title={compact ? label : undefined}
            onClick={id ? () => setActiveTab(id) : undefined}
          >
            <Icon size={17} />
            {!compact && <span>{label}</span>}
          </button>
        ))}

        {/* Account */}
        <div className="sidebar__account" title={compact ? getDisplayName(user?.displayName, user?.email) : undefined}>
          <div className="sidebar__avatar">
            {getInitials(user?.displayName, user?.email)}
          </div>
          {!compact && (
            <div className="sidebar__account-info">
              <span className="sidebar__account-name">
                {getDisplayName(user?.displayName, user?.email)}
              </span>
              <button
                className="sidebar__logout-btn"
                onClick={() => logout()}
              >
                <LogOut size={11} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
