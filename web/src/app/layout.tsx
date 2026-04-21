import "./globals.css";
import "mana-font/css/mana.css";

import { getMeServer } from "@/components/auth/server";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";

import { Providers } from "./providers";
export const metadata = {
  title: "TristanColdefy",
  description: "Portfolio",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const me = await getMeServer();
  return (
    <html lang="fr">
      <body>
        <Providers initialUser={me}>
          <Header />
          <main className="container">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
