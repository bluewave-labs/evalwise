import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/contexts/auth-context'
import OrganizationCheck from '@/components/organization-check'
import LayoutWrapper from '@/components/layout-wrapper'

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
            <LayoutWrapper>
              {children}
            </LayoutWrapper>
          </OrganizationCheck>
        </AuthProvider>
      </body>
    </html>
  )
}