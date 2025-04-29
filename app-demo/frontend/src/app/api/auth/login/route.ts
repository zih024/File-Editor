import { NextRequest, NextResponse } from "next/server"
import { BACKEND_URL } from "@/lib/api-utils"


export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()

    const body = new URLSearchParams()
    body.append("username", formData.get("username") as string)
    body.append("password", formData.get("password") as string)

    const response = await fetch(`${BACKEND_URL}/auth/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    const cookieResponse = NextResponse.json(
      { success: true },
      { status: 200 }
    )

    cookieResponse.cookies.set({
      name: "auth_token",
      value: data.access_token,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 1800,
      path: "/",
    })

    return cookieResponse
  } catch (error) {
    console.error("Login error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
