'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { createClient } from '@supabase/supabase-js'
import toast from 'react-hot-toast'

interface Report {
  id: string
  user_id: string
  year: number
  status: string
  file_path: string
  file_type: string
  created_at: string
  updated_at: string
  overall_score?: number
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export default function Dashboard() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'processing' | 'completed' | 'failed'>('all')
  const supabase = createClient(supabaseUrl, supabaseAnonKey)

  useEffect(() => {
    fetchReports()
  }, [filter])

  const fetchReports = async () => {
    try {
      setLoading(true)
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        toast.error('Not authenticated')
        return
      }

      let query = supabase
        .from('reports')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })

      if (filter !== 'all') {
        query = query.eq('status', filter)
      }

      const { data, error } = await query

      if (error) throw error
      setReports(data || [])
    } catch (error) {
      toast.error(`Failed to fetch reports: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const deleteReport = async (reportId: string) => {
    if (!confirm('Are you sure you want to delete this report?')) return

    try {
      const { error } = await supabase
        .from('reports')
        .delete()
        .eq('id', reportId)

      if (error) throw error
      toast.success('Report deleted')
      setReports(reports.filter(r => r.id !== reportId))
    } catch (error) {
      toast.error(`Failed to delete report: ${error}`)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'review':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
        return '⏳'
      case 'completed':
        return '✓'
      case 'failed':
        return '✕'
      case 'review':
        return '⚠'
      default:
        return '○'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Manage your financial statement reports</p>
        </div>
        <Link
          href="/upload"
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
        >
          + New Report
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        {(['all', 'processing', 'completed', 'failed'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              filter === f
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Reports Table */}
      {loading ? (
        <div className="text-center py-12">
          <p className="text-gray-600">Loading reports...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-600 mb-4">No reports found</p>
          <Link
            href="/upload"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Create your first report
          </Link>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Year</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">File Type</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Score</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Created</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">{report.year}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(report.status)}`}>
                        {getStatusIcon(report.status)} {report.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{report.file_type}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {report.overall_score ? `${Math.round(report.overall_score)}%` : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex gap-2">
                        <Link
                          href={`/report/${report.id}`}
                          className="text-blue-600 hover:text-blue-700 font-medium"
                        >
                          View
                        </Link>
                        <button
                          onClick={() => deleteReport(report.id)}
                          className="text-red-600 hover:text-red-700 font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
