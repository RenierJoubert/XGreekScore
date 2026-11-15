import { NextRequest, NextResponse } from "next/server";
import { queryPosts } from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const get = (key: string) => searchParams.get(key) ?? undefined;

  const result = queryPosts({
    q: get("q"),
    from: get("from"),
    to: get("to"),
    page: Number(get("page") ?? 1),
    cluster: get("cluster"),
    reply_cluster: get("reply_cluster"),
  });
  return NextResponse.json(result);
}
