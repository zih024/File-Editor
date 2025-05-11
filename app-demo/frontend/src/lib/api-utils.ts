import { NextRequest, NextResponse } from "next/server";

export const BACKEND_URL = "http://backend:8000";
export const BACKEND_PUBLIC_URL = "http://localhost:8000";
export const BACKEND_PUBLIC_WS_URL = "ws://localhost:8000";

type BackendRequestOptions = {
  path: string;
  method?: string;
  requiresAuth?: boolean;
  body?: Record<string, unknown> | FormData;
  additionalHeaders?: Record<string, string>;
  responseType?: "json" | "blob";
};

/**
 * Makes a request to the backend and handles common patterns like auth and error handling
 */
export async function backendRequest(
  request: NextRequest,
  options: BackendRequestOptions,
) {
  const {
    path,
    method = "GET",
    requiresAuth = true,
    body,
    additionalHeaders = {},
    responseType = "json",
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
          { status: 401 },
        );
      }

      headers["Authorization"] = `Bearer ${token.value}`;
    }

    let requestBody: string | FormData | undefined = undefined;

    // Handle different body types
    if (body) {
      if (body instanceof FormData) {
        // For FormData, pass it directly without setting Content-Type
        // The browser will set the appropriate Content-Type with boundary
        requestBody = body;
      } else {
        // For JSON data, stringify and set the Content-Type
        headers["Content-Type"] = "application/json";
        requestBody = JSON.stringify(body);
      }
    }

    // Make the request to the backend
    const response = await fetch(`${BACKEND_URL}${path}`, {
      method,
      headers,
      ...(requestBody ? { body: requestBody } : {}),
    });

    // If response is not successful, handle the error consistently
    if (!response.ok) {
      const errorData = response.status !== 204 ? await response.json() : null;
      return NextResponse.json(errorData, { status: response.status });
    }

    // For file downloads, we need to preserve the headers and return the blob
    if (responseType === "blob") {
      // Clone the headers from the original response
      const responseHeaders = new Headers();
      response.headers.forEach((value, key) => {
        responseHeaders.set(key, value);
      });

      // Get the blob data from the response
      const blob = await response.blob();

      // Create a new response with the blob and original headers
      return new NextResponse(blob, {
        status: response.status,
        headers: responseHeaders,
      });
    }

    // For JSON responses, parse and return as before
    const data = response.status !== 204 ? await response.json() : null;
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Error in backend request to ${path}:`, error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
