"use client";

import { useState, useTransition } from "react";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  updateProfile,
} from "firebase/auth";
import { ArrowRight, LoaderCircle } from "lucide-react";
import { auth } from "@/lib/firebase";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type AuthMode = "login" | "signup";

const copyByMode: Record<
  AuthMode,
  {
    title: string;
    description: string;
    submitLabel: string;
  }
> = {
  login: {
    title: "Welcome back",
    description: "Use your email and password to continue into Archibot.",
    submitLabel: "Log in",
  },
  signup: {
    title: "Create your account",
    description: "Start with Firebase auth now and layer Firestore data on top.",
    submitLabel: "Sign up",
  },
};

export function AuthPopover({ mode }: { mode: AuthMode }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const copy = copyByMode[mode];

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    startTransition(async () => {
      try {
        if (mode === "login") {
          await signInWithEmailAndPassword(auth, email, password);
        } else {
          const credentials = await createUserWithEmailAndPassword(
            auth,
            email,
            password,
          );

          if (name.trim()) {
            await updateProfile(credentials.user, { displayName: name.trim() });
          }
        }

        setOpen(false);
        setName("");
        setEmail("");
        setPassword("");
      } catch (submitError) {
        const message =
          submitError instanceof Error
            ? submitError.message.replace("Firebase: ", "")
            : "Authentication failed. Check your Firebase configuration.";

        setError(message);
      }
    });
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant={mode === "login" ? "ghost" : "default"}>
          {mode === "login" ? "Log in" : "Sign up"}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-[360px] p-0">
        <div className="space-y-5 p-6">
          <div className="space-y-1">
            <h3 className="text-lg font-semibold">{copy.title}</h3>
            <p className="text-sm text-muted-foreground">{copy.description}</p>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {mode === "signup" ? (
              <div className="space-y-2">
                <Label htmlFor={`${mode}-name`}>Full name</Label>
                <Input
                  id={`${mode}-name`}
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Amina Bennani"
                />
              </div>
            ) : null}

            <div className="space-y-2">
              <Label htmlFor={`${mode}-email`}>Email</Label>
              <Input
                id={`${mode}-email`}
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@archibot.app"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`${mode}-password`}>Password</Label>
              <Input
                id={`${mode}-password`}
                type="password"
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 6 characters"
                minLength={6}
                required
              />
            </div>

            {error ? (
              <p className="text-sm text-destructive">{error}</p>
            ) : null}

            <Button className="w-full" type="submit" disabled={isPending}>
              {isPending ? (
                <LoaderCircle className="size-4 animate-spin" />
              ) : (
                <ArrowRight className="size-4" />
              )}
              {copy.submitLabel}
            </Button>
          </form>
        </div>
      </PopoverContent>
    </Popover>
  );
}
