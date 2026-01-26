import "./globals.css";
import { ToastProvider } from "@/components/ui/Toast";
import { Header } from "@/components/layout/Header";

export const metadata = {
  title: "Mon site",
  description: "Site pro",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>
        <ToastProvider>
          <Header />
          <main className="container">{children}</main>
        </ToastProvider>
      </body>
    </html>
  );
}
