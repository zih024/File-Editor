import { backendRequest } from "@/lib/api-utils";
import { NextRequest } from "next/server";


export async function GET(request: NextRequest) {
    return backendRequest(request, {
        path: "/files/",
        requiresAuth: true,
    });
}

export async function POST(request: NextRequest) {
    const formData = await request.formData();
    return backendRequest(request, {
        path: "/files/",
        requiresAuth: true,
        method: "POST",
        body: formData,
    });
}