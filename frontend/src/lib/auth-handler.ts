import { NextRequest, NextResponse } from "next/server";

export interface AuthDelegator {
  api: {
    signUpEmail: (...args: any[]) => Promise<any>;
    signInEmail: (...args: any[]) => Promise<any>;
    signOut: (...args: any[]) => Promise<any>;
  };
}

type AuthResult = { token?: string; user?: { id: string; name: string } | null } | undefined;

function error(status: number, message: string): NextResponse {
  return NextResponse.json({ error: message }, { status });
}

async function readBody(request: NextRequest): Promise<{ username?: string; password?: string }> {
  try {
    return (await request.json()) as { username?: string; password?: string };
  } catch {
    return {};
  }
}

const loginEmail = (username: string) => `${username}@todo.local`;

export async function handleAuthPost(
  auth: AuthDelegator,
  request: NextRequest,
): Promise<NextResponse> {
  const action = request.nextUrl.pathname.split("/").pop();
  const body = await readBody(request);

  if (action === "register") {
    const username = typeof body.username === "string" ? body.username.trim() : "";
    const password = typeof body.password === "string" ? body.password : "";
    if (!username) {
      return error(400, "Username cannot be blank");
    }
    if (password === "") {
      return error(400, "Password cannot be blank");
    }
    try {
      const result = (await auth.api.signUpEmail({
        body: { name: username, email: loginEmail(username), password },
      })) as AuthResult;
      if (!result?.user) {
        return error(409, "Username already exists");
      }
      return NextResponse.json(
        { id: result.user.id, username: result.user.name },
        { status: 201 },
      );
    } catch {
      return error(409, "Username already exists");
    }
  }

  if (action === "login") {
    const username = typeof body.username === "string" ? body.username.trim() : "";
    const password = typeof body.password === "string" ? body.password : "";
    if (!username || password === "") {
      return error(401, "Invalid username or password");
    }
    try {
      const result = (await auth.api.signInEmail({
        body: { email: loginEmail(username), password },
      })) as AuthResult;
      if (!result?.user) {
        return error(401, "Invalid username or password");
      }
      return NextResponse.json(
        { id: result.user.id, username: result.user.name },
        { status: 200 },
      );
    } catch {
      return error(401, "Invalid username or password");
    }
  }

  if (action === "logout") {
    await auth.api.signOut({ headers: request.headers });
    return new NextResponse(null, { status: 204 });
  }

  return error(404, "Not found");
}