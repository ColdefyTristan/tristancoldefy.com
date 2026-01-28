import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Providers } from "./providers";
import { getMeServer } from "@/components/auth/server";
export const metadata = {
  title: "Mon site",
  description: "Site pro",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const me = await getMeServer();
  return (
    <html lang="fr">
      <body>
        <Providers initialUser={me}>
          <Header />
          <main className="container">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
