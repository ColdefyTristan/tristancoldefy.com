"use client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Dialog, DialogTrigger, DialogContent, DialogClose } from "@/components/ui/Dialog";
import { useToast } from "@/components/ui/Toast";
import type { ApiError } from "@/lib/api/errors";

type State =
  | { kind: "loading" }
  | { kind: "error"; error: ApiError }
  | { kind: "empty" }
  | { kind: "success"; data: unknown };



export default function Playground() {
    const { toast } = useToast();

    return (
        <div>
            <div style={{ padding: 24, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button loading>Loading</Button>
            <Button disabled>Disabled</Button>
            </div>
            <div style={{ display: "grid", gap: 16, maxWidth: 360 }}>
                <Input label="Email" placeholder="you@example.com" />
                <Input label="Password" type="password" hint="8 caractères minimum" />
                <Input label="Username" error="Ce nom est déjà pris" />
                <Input label="Disabled" disabled placeholder="..." />
            </div>
            <div style={{ padding: 24 }}>
                <Dialog>
                    <DialogTrigger asChild>
                    <Button>Open dialog</Button>
                    </DialogTrigger>

                    <DialogContent title="Example dialog">
                    <p>Contenu de la modale.</p>
                    <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
                        <DialogClose asChild>
                        <Button variant="secondary">Cancel</Button>
                        </DialogClose>
                        <Button>Confirm</Button>
                    </div>
                    </DialogContent>
                </Dialog>
            </div>
            <div style={{ padding: 24, display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Button
                    onClick={() =>
                    toast({ variant: "info", title: "Info", message: "Hello toast 👋" })
                    }
                >
                    Toast info
                </Button>

                <Button
                    variant="secondary"
                    onClick={() =>
                    toast({ variant: "success", title: "Saved", message: "OK." })
                    }
                >
                    Toast success
                </Button>

                <Button
                    onClick={() =>
                    toast({ variant: "error", title: "Error", message: "Something failed." })
                    }
                >
                    Toast error
                </Button>
            </div>
        </div>
    );
}
