export type AuthMail = {
    primary: string | null;
    pending: string | null;
    verification_sent_at: string | null;
}

export type AuthUser = {
  id: string;
  username: string;
  email: AuthMail;
  is_family:boolean;
};