import { backendRequest } from "@/lib/api-utils";
import { NextRequest } from "next/server";


export async function GET(request: NextRequest) {
  return backendRequest(request, {
    path: "/users/me",
    method: "GET",
    requiresAuth: true,
  })
}
