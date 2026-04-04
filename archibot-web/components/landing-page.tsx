"use client";

import Link from "next/link";
import { Bot, LogOut } from "lucide-react";
import { AuthPopover } from "@/components/auth-popover";
import { useAuth } from "@/components/auth-provider";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

export function LandingPage() {
  const { loading, logout, user } = useAuth();

  const initials =
    user?.displayName
      ?.split(" ")
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() ||
    user?.email?.slice(0, 2).toUpperCase() ||
    "AB";

  return (
    <main className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-white/40 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <Bot className="size-5" />
            </div>
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.25em] text-muted-foreground">
                Archibot
              </p>
              <p className="text-sm text-foreground/80">
                AI agent managed architecture company
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-3">
            {loading ? (
              <span className="text-sm text-muted-foreground">Checking session...</span>
            ) : user ? (
              <>
                <div className="hidden items-center gap-3 rounded-full border bg-card px-3 py-2 sm:flex">
                  <Avatar className="size-9">
                    <AvatarFallback>{initials}</AvatarFallback>
                  </Avatar>
                  <div className="text-sm">
                    <p className="font-medium leading-none">
                      {user.displayName || "Signed in"}
                    </p>
                    <p className="mt-1 text-muted-foreground">{user.email}</p>
                  </div>
                </div>
                <Button variant="outline" onClick={() => void logout()}>
                  <LogOut className="size-4" />
                  Log out
                </Button>
              </>
            ) : (
              <>
                <AuthPopover mode="login" />
                <AuthPopover mode="signup" />
              </>
            )}
          </nav>
        </div>
      </header>

      <section className="flex flex-1 items-center">
        <div className="mx-auto flex w-full max-w-6xl flex-col px-6 py-12">
          <div className="max-w-3xl space-y-6">
            <p className="text-sm font-medium uppercase tracking-[0.3em] text-muted-foreground">
              Archibot
            </p>
            <h1 className="text-5xl font-semibold tracking-tight text-balance sm:text-7xl">
              AI-led architecture, from brief to studio execution.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
              A minimal entry point for an AI agent managed architecture
              company. Auth is live, Firestore is ready, and the studio is one
              click away.
            </p>
          </div>

          <div className="mt-10 flex flex-col gap-4 sm:flex-row text-background">
            <Button asChild size="lg">
              <Link href="/studio">Open Studio</Link>
            </Button>
            {user ? (
              <div className="flex items-center rounded-full border bg-card/70 px-5 py-3 text-sm text-muted-foreground">
                Signed in as {user.email}
              </div>
            ) : (
              <>
                <AuthPopover mode="signup" />
                <AuthPopover mode="login" />
              </>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
