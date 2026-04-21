import {AuthUser} from "@/lib/api/services/users"

import { api } from "../client";
import { endpoints } from "../endpoints";

export async function getMe(): Promise<AuthUser> {
  return api.get<AuthUser>("/auth/me", { 
    cache: "no-store",
  });
}

export type LoginRequest = { identifier: string; password: string; remember_me?:boolean| null }; 
export async function login(body: LoginRequest): Promise<void> {
  await api.post("/auth/login", body);
}

export type RegisterRequest = { email?: string | null;username: string; password: string; remember_me?:boolean| null }; 
export async function register(body: RegisterRequest): Promise<void> {
  await api.post("/auth/register", body );
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}