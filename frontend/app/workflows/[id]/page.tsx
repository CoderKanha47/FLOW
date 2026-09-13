"use client";

import { useParams } from "next/navigation";

import WorkflowEditor from "@/components/WorkflowEditor";

export default function EditorPage() {
  const params = useParams<{ id: string }>();
  return <WorkflowEditor workflowId={params.id} />;
}