import { NextRequest, NextResponse } from "next/server";

import { handleApiError, requirePermission } from "@/app/api/bff/utils";
import { inboxApiClient } from "@/lib/api/inboxApiClient";
import type { components } from "@/lib/api/types.generated";

import { toTask } from "../../../route";

type TaskUpdatePayload = components["schemas"]["TaskUpdateRequest"];

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest, { params }: { params: { taskId: string } }) {
  const permission = await requirePermission("inbox", "configure");
  if (!permission.ok) {
    return permission.response;
  }

  let payload: TaskUpdatePayload | null = null;
  try {
    payload = (await request.json()) as TaskUpdatePayload;
  } catch {
    payload = null;
  }

  try {
    const response = await inboxApiClient.applyTask(params.taskId, payload);
    return NextResponse.json({ data: toTask(response) });
  } catch (error) {
    return handleApiError(error, "Unable to apply inbox task.");
  }
}
