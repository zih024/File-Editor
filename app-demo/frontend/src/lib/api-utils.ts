import { NextRequest, NextResponse } from "next/server";


export const BACKEND_URL = "http://backend:8000"


type BackendRequestOptions = {
  path: string;
  method?: string;
  requiresAuth?: boolean;
  body?: Record<string, unknown>;
  additionalHeaders?: Record<string, string>;
};

/**
 * Makes a request to the backend and handles common patterns like auth and error handling
 */
export async function backendRequest(
  request: NextRequest,
  options: BackendRequestOptions
) {
  const {
    path,
    method = "GET",
    requiresAuth = true,
    body,
    additionalHeaders = {},
  } = options;

  try {
    const headers: Record<string, string> = {
      ...additionalHeaders,
    };

    // Handle authentication if required
    if (requiresAuth) {
      const token = request.cookies.get("auth_token");
      
      if (!token || !token.value) {
        return NextResponse.json(
          { detail: "Not authenticated" },
          { status: 401 }
        );
      }
      
      headers["Authorization"] = `Bearer ${token.value}`;
    }

    // Add content type for JSON requests
    if (body && typeof body === 'object' && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    // Make the request to the backend
    const response = await fetch(`${BACKEND_URL}${path}`, {
      method,
      headers,
      ...(body ? { body: JSON.stringify(body) } : {}),
    });

    // Get response data
    const data = response.status !== 204 ? await response.json() : null;

    // If the request was not successful, return the error
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    // Return the data
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Error in backend request to ${path}:`, error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
} 