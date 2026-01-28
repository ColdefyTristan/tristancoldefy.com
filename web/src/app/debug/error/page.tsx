"use client";
import { ApiError } from "@/lib/api/errors";

export default function DebugErrorPage() {
  return (
    <button
      onClick={() => {
        throw new ApiError({ status: 500, code: "DEBUG", message: "Debug error" });
      }}
    >
      Throw error !
    </button>
  );
}