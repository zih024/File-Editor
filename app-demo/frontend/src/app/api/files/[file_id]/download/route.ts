import { NextRequest } from "next/server";
import { backendRequest } from "@/lib/api-utils";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ file_id: string }> },
) {
  const { file_id } = await params;
  return backendRequest(request, {
    path: `/files/${file_id}/download/`,
    requiresAuth: true,
    responseType: "blob",
  });
}
