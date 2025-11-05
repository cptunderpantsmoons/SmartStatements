import './globals.css'
import { Inter } from 'next/font/google'
import { SupabaseClient } from '@supabase/supabase-js'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

// Initialize Supabase client
const supabase = new SupabaseClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export const metadata = {
  title: 'AI Financial Statement Generator',
  description: 'Generate accurate financial statements with AI-powered processing and verification',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <h1 className="text-xl font-semibold text-gray-900">
                    AI Financial Statements
                  </h1>
                </div>
                <nav className="flex items-center space-x-4">
                  <a
                    href="/dashboard"
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Dashboard
                  </a>
                  <a
                    href="/upload"
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Upload
                  </a>
                  <button
                    onClick={() => supabase.auth.signOut()}
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Sign Out
                  </button>
                </nav>
              </div>
            </div>
          </header>

          <main className="flex-1">
            {children}
          </main>
        </div>
        <Toaster position="top-right" />
      </body>
    </html>
  )
}
