import { NextRequest } from "next/server";
import { backendRequest } from "@/lib/api-utils";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ file_id: string }> },
) {
  const { file_id } = await params;
  return backendRequest(request, {
    path: `/files/${file_id}/`,
    requiresAuth: true,
  });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ file_id: string }> },
) {
  const { file_id } = await params;
  return backendRequest(request, {
    path: `/files/${file_id}/`,
    requiresAuth: true,
    method: "DELETE",
  });
}
