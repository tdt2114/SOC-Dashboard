import { Inter } from "next/font/google";
import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SOC Dashboard",
  description: "Repo B MVP for Wazuh alert and agent consumption."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var localTheme = localStorage.getItem('soc-theme');
                  var theme = localTheme || 'dark';
                  document.documentElement.setAttribute('data-theme', theme);
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
