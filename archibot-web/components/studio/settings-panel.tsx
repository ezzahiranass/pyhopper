"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { useStudio } from "@/components/studio/studio-context";

export function StudioSettingsPanel() {
  const {
    settings: { optimizeCanvasEmbeds },
    setOptimizeCanvasEmbeds,
  } = useStudio();

  return (
    <div className="studio-panel-page">
      <header className="studio-panel-page__header">
        <h1 className="studio-panel-page__title">Settings</h1>
        <p className="studio-panel-page__subtitle">
          Configure workspace behavior and studio preferences.
        </p>
      </header>

      <section className="studio-settings-card">
        <div className="studio-settings-card__copy">
          <span className="studio-settings-card__eyebrow">Workspace Canvas</span>
          <h2 className="studio-settings-card__title">Optimize canvas embeds</h2>
          <p className="studio-settings-card__description">
            Keep only one heavy embed active at a time. Turn this off to keep every map, model,
            and future viewer live by default.
          </p>
        </div>

        <div
          className={`studio-settings-card__toggle${optimizeCanvasEmbeds ? " is-enabled" : ""}`}
          onClick={() => setOptimizeCanvasEmbeds(!optimizeCanvasEmbeds)}
          onKeyDown={(event) => {
            if (event.key !== "Enter" && event.key !== " ") return;
            event.preventDefault();
            setOptimizeCanvasEmbeds(!optimizeCanvasEmbeds);
          }}
          aria-pressed={optimizeCanvasEmbeds}
          role="button"
          tabIndex={0}
        >
          <span className="studio-settings-card__toggle-copy">
            <span className="studio-settings-card__toggle-label">
              {optimizeCanvasEmbeds ? "Enabled" : "Disabled"}
            </span>
            <span className="studio-settings-card__toggle-hint">
              {optimizeCanvasEmbeds
                ? "Single-active viewer mode"
                : "All canvas embeds stay active"}
            </span>
          </span>
          <Checkbox
            checked={optimizeCanvasEmbeds}
            onCheckedChange={setOptimizeCanvasEmbeds}
            onClick={(event) => event.stopPropagation()}
            aria-label="Toggle optimize canvas embeds"
          />
        </div>
      </section>
    </div>
  );
}
