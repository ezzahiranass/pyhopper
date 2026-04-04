export const STUDIO_TABS = [
  "dashboard",
  "team",
  "projects",
  "conversation",
  "workspace",
  "playground",
  "settings",
] as const;

export type StudioTab = (typeof STUDIO_TABS)[number];

export const DEFAULT_STUDIO_TAB: StudioTab = "dashboard";

export function isStudioTab(value: string): value is StudioTab {
  return STUDIO_TABS.includes(value as StudioTab);
}

export function getStudioTabHref(tab: StudioTab) {
  return `/studio/${tab}`;
}
