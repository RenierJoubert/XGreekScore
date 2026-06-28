import { NextRequest, NextResponse } from "next/server";
import { queryPosts } from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const result = queryPosts({
    q:       searchParams.get("q")       ?? undefined,
    from:    searchParams.get("from")    ?? undefined,
    to:      searchParams.get("to")      ?? undefined,
    page:    Number(searchParams.get("page") ?? 1),
    cluster: searchParams.get("cluster") ?? undefined,
  });
  return NextResponse.json(result);
}
