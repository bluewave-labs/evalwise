import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/contexts/auth-context'
import Sidebar from '@/components/sidebar'
import OrganizationCheck from '@/components/organization-check'

export const metadata: Metadata = {
  title: 'EvalWise - LLM Red Teaming & Evaluation Platform',
  description: 'Developer-friendly platform for LLM evaluation and red teaming',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900" suppressHydrationWarning={true}>
        <AuthProvider>
          <OrganizationCheck>
            <div className="flex min-h-screen">
              <Sidebar />
              <main className="flex-1 p-6">
                {children}
              </main>
            </div>
          </OrganizationCheck>
        </AuthProvider>
      </body>
    </html>
  )
}