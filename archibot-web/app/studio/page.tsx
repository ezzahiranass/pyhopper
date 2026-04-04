import { redirect } from "next/navigation";
import { DEFAULT_STUDIO_TAB, getStudioTabHref } from "@/components/studio/studio-tabs";

export default function StudioPage() {
  redirect(getStudioTabHref(DEFAULT_STUDIO_TAB));
}
