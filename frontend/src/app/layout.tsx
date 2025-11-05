import './globals.css'
import { Inter } from 'next/font/google'
import { ClientLayout } from './client-layout'

const inter = Inter({ subsets: ['latin'] })

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
        <ClientLayout>
          {children}
        </ClientLayout>
      </body>
    </html>
  )
}
