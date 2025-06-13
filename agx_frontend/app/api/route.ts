import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
    const body = await request.text();
    const apiURL = process.env.NEXT_PUBLIC_API_URL;

    // Get client IP from Next.js (Vercel) edge runtime
    const clientIP = request.headers.get("x-forwarded-for") || request.headers.get("x-real-ip") || "";

    const backendRes = await fetch(`${apiURL}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-forwarded-for": clientIP, // Forward the client IP
        },
        body,
    });
    const text = await backendRes.text();
    return new NextResponse(text, {
        status: backendRes.status,
        headers: { "Content-Type": "text/plain" },
    });
}