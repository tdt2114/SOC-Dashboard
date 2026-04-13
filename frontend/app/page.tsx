import { redirect } from "next/navigation";

import { getCurrentUserFromCookies } from "@/lib/auth";

export default async function HomePage() {
  const currentUser = await getCurrentUserFromCookies();
  redirect(currentUser ? "/alerts" : "/login");
}
