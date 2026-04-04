"use client";

import { useEffect, useRef, useState } from "react";
import { Handle, NodeProps, Position } from "@xyflow/react";
import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { getJobDescription } from "@/components/studio/data";
import { useStudio } from "@/components/studio/studio-context";
import { OrgChartFlowNode } from "@/components/studio/types";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

function OrgChartNode({ data, selected }: NodeProps<OrgChartFlowNode>) {
  const { jobs } = useStudio();
  const [nameDraft, setNameDraft] = useState(data.name);
  const [jobDraft, setJobDraft] = useState(data.job);
  const [descriptionDraft, setDescriptionDraft] = useState(data.description);
  const [personalityDraft, setPersonalityDraft] = useState(data.personality);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!data.isEditing) return;

    requestAnimationFrame(() => {
      nameRef.current?.focus();
      nameRef.current?.select();
    });
  }, [data.isEditing]);

  function stopCanvasEvent(event: React.SyntheticEvent) {
    event.stopPropagation();
  }

  function handleSave() {
    const nextName = nameDraft.trim();
    const nextDescription = descriptionDraft.trim();
    const resolvedName = nextName || data.name;

    setNameDraft(resolvedName);
    setDescriptionDraft(nextDescription);

    data.onSubmitEdit({
      name: resolvedName,
      job: jobDraft,
      description: nextDescription,
      personality: personalityDraft,
    });
    data.onStopEdit();
  }

  function handleCancel() {
    setNameDraft(data.name);
    setJobDraft(data.job);
    setDescriptionDraft(data.description);
    setPersonalityDraft(data.personality);
    data.onStopEdit();
  }

  return (
    <div
      className={`studio-node${data.isEditing ? " studio-node--editing" : ""}`}
      data-selected={selected ? "true" : "false"}
      onMouseDown={stopCanvasEvent}
      onClick={(event) => {
        stopCanvasEvent(event);
        data.onSelect();
      }}
    >
      {!data.isRoot && (
        <Handle className="studio-handle" type="target" position={Position.Top} />
      )}

      <div className="studio-node__header">
        <div className="studio-node__content">
          <p className="studio-node__eyebrow">{data.name || "Unnamed agent"}</p>
          <h3 className="studio-node__title">{data.job}</h3>
        </div>
        <div className="studio-node__actions">
          {data.isEditing ? (
            <>
              <button
                type="button"
                className="studio-node__icon-button nodrag nopan"
                aria-label={`Submit changes for ${data.name || data.job}`}
                onClick={(event) => {
                  stopCanvasEvent(event);
                  handleSave();
                }}
              >
                <Check size={14} />
              </button>
              <button
                type="button"
                className="studio-node__icon-button nodrag nopan"
                aria-label={`Close editor for ${data.name || data.job}`}
                onClick={(event) => {
                  stopCanvasEvent(event);
                  handleCancel();
                }}
              >
                <X size={14} />
              </button>
            </>
          ) : (
            <button
              type="button"
              className="studio-node__icon-button nodrag nopan"
              aria-label={`Edit ${data.name || data.job}`}
              onClick={(event) => {
                stopCanvasEvent(event);
                setNameDraft(data.name);
                setJobDraft(data.job);
                setDescriptionDraft(data.description);
                setPersonalityDraft(data.personality);
                data.onStartEdit();
              }}
            >
              <Pencil size={14} />
            </button>
          )}
          {!data.isEditing && (
            <>
              <button
                type="button"
                className="studio-node__icon-button nodrag nopan"
                aria-label={`Add child to ${data.name || data.job}`}
                onClick={(event) => {
                  stopCanvasEvent(event);
                  data.onAddChild();
                }}
              >
                <Plus size={14} />
              </button>
              {!data.isRoot && (
                <button
                  type="button"
                  className="studio-node__icon-button studio-node__icon-button--danger nodrag nopan"
                  aria-label={`Delete ${data.name || data.job}`}
                  onClick={(event) => {
                    stopCanvasEvent(event);
                    data.onDelete();
                  }}
                >
                  <Trash2 size={14} />
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {data.isEditing ? (
        <div className="studio-node__editor">
          <div className="studio-node__field">
            <label className="studio-node__field-label" htmlFor={`node-name-${data.name}`}>
              Name
            </label>
            <Input
              id={`node-name-${data.name}`}
              ref={nameRef}
              className="studio-node__input nodrag nopan"
              value={nameDraft}
              onChange={(event) => setNameDraft(event.target.value)}
              onMouseDown={stopCanvasEvent}
              onClick={stopCanvasEvent}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSave();
                }
                if (event.key === "Escape") {
                  event.preventDefault();
                  handleCancel();
                }
                event.stopPropagation();
              }}
            />
          </div>
          <div className="studio-node__field">
            <label className="studio-node__field-label" htmlFor={`node-job-${data.name}`}>
              Job
            </label>
            <Select
              value={jobDraft}
              onValueChange={(value) => {
                const nextJob = value as typeof data.job;
                setJobDraft(nextJob);
                setDescriptionDraft(getJobDescription(nextJob, jobs));
              }}
            >
              <SelectTrigger
                id={`node-job-${data.name}`}
                className="studio-node__input studio-node__select-trigger nodrag nopan"
                onMouseDown={stopCanvasEvent}
                onClick={stopCanvasEvent}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    handleCancel();
                  }
                  event.stopPropagation();
                }}
              >
                <SelectValue placeholder="Select a job" />
              </SelectTrigger>
              <SelectContent onMouseDown={stopCanvasEvent}>
                {jobs.map((job) => (
                  <SelectItem key={job.slug} value={job.title}>
                    {job.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="studio-node__field">
            <label className="studio-node__field-label" htmlFor={`node-description-${data.name}`}>
              Description
            </label>
            <Textarea
              id={`node-description-${data.name}`}
              className="studio-node__input studio-node__input--textarea nodrag nopan"
              value={descriptionDraft}
              onChange={(event) => setDescriptionDraft(event.target.value)}
              onMouseDown={stopCanvasEvent}
              onClick={stopCanvasEvent}
              onKeyDown={(event) => {
                if ((event.key === "Enter" && (event.metaKey || event.ctrlKey))) {
                  event.preventDefault();
                  handleSave();
                }
                if (event.key === "Escape") {
                  event.preventDefault();
                  handleCancel();
                }
                event.stopPropagation();
              }}
              rows={3}
            />
          </div>
          <div className="studio-node__field">
            <label className="studio-node__field-label" htmlFor={`node-personality-${data.name}`}>
              Personality
            </label>
            <Select
              value={personalityDraft || undefined}
              onValueChange={setPersonalityDraft}
            >
              <SelectTrigger
                id={`node-personality-${data.name}`}
                className="studio-node__input studio-node__select-trigger nodrag nopan"
                onMouseDown={stopCanvasEvent}
                onClick={stopCanvasEvent}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    handleCancel();
                  }
                  event.stopPropagation();
                }}
              >
                <SelectValue placeholder="Select a personality" />
              </SelectTrigger>
              <SelectContent onMouseDown={stopCanvasEvent}>
                {data.personalities.map((personality) => (
                  <SelectItem key={personality.value} value={personality.value}>
                    {personality.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      ) : (
        <p className="studio-node__description">{data.description}</p>
      )}

      <Handle className="studio-handle" type="source" position={Position.Bottom} />
    </div>
  );
}

export default OrgChartNode;
