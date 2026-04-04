import { notFound } from "next/navigation";
import { isStudioTab } from "@/components/studio/studio-tabs";

export default async function StudioTabPage(props: PageProps<"/studio/[tab]">) {
  const { tab } = await props.params;

  if (!isStudioTab(tab)) {
    notFound();
  }

  return null;
}
