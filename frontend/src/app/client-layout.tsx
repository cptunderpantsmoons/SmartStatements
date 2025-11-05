'use client'

import { createClient } from '@supabase/supabase-js'
import { Toaster } from 'react-hot-toast'
import { useEffect, useState } from 'react'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() => createClient(supabaseUrl, supabaseAnonKey))

  return (
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

      <Toaster position="top-right" />
    </div>
  )
}
