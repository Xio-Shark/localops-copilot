import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "LocalOps Copilot",
  description: "MVP",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="page">
          <div className="panel">
            <strong>LocalOps Copilot</strong>
            <div style={{ marginTop: 8 }}>
              <Link href="/">Projects</Link> | <Link href="/planner">Planner</Link>
            </div>
          </div>
          {children}
        </div>
      </body>
    </html>
  );
}
