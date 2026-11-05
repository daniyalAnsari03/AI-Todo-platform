import { NextRequest } from "next/server";
import { toNextJsHandler } from "better-auth/next-js";

import { auth } from "../../../../../auth";
import { handleAuthPost } from "../../../../../src/lib/auth-handler";

const { GET } = toNextJsHandler(auth);

export { GET };

export async function POST(request: NextRequest) {
  return handleAuthPost(auth, request);
}