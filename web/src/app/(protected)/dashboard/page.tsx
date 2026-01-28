"use client";
import { useAuth } from "@/components/auth/AuthProvider";
import { Button } from "@/components/ui/Button";
export default function Dashboard() {
    const { user, status, refreshMe, logout } = useAuth();

    return(
        <div>
            dashboard
            <Button
                    variant="secondary"
                    onClick={() =>
                    logout()
                    }
                >
                    Logout
            </Button>
        </div>
    );

};