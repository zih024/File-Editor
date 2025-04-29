import { NextRequest, NextResponse } from "next/server";

const protectedRoutes = ["/files", "/chat"];
const publicRoutes = ["/login", "/signup"];

export default function middleware(request: NextRequest) {
    const path = request.nextUrl.pathname;
    const isProtectedRoute = protectedRoutes.includes(path);
    const isPublicRoute = publicRoutes.includes(path);

    const token = request.cookies.get("auth_token");
    if (isProtectedRoute && !token) {
        return NextResponse.redirect(new URL("/login", request.url));
    }
    if (isPublicRoute && token) {
        return NextResponse.redirect(new URL("/chat", request.url));
    }

    return NextResponse.next();

}