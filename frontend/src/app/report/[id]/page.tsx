'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { createClient } from '@supabase/supabase-js'
import toast from 'react-hot-toast'

interface ReportData {
  id: string
  user_id: string
  year: number
  status: string
  file_path: string
  file_type: string
  overall_score?: number
  qa_report?: any
  processing_log?: string[]
  created_at: string
  updated_at: string
  error_message?: string
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export default function ReportDetail() {
  const params = useParams()
  const reportId = params.id as string
  
  const [report, setReport] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'qa' | 'logs'>('overview')
  
  const supabase = createClient(supabaseUrl, supabaseAnonKey)

  useEffect(() => {
    fetchReport()
    const interval = setInterval(() => {
      if (report?.status === 'processing') {
        fetchReport()
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [reportId])

  const fetchReport = async () => {
    try {
      const { data, error } = await supabase
        .from('reports')
        .select('*')
        .eq('id', reportId)
        .single()

      if (error) throw error
      setReport(data)
    } catch (error) {
      toast.error(`Failed to fetch report: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const downloadFile = async (fileType: 'statements' | 'certificate') => {
    try {
      // Construct file path from storage
      const fileName = fileType === 'statements' 
        ? `${report?.user_id}/${reportId}_2025_Final.xlsx`
        : `${report?.user_id}/${reportId}_verification_certificate.html`

      const { data } = supabase.storage.from('outputs').getPublicUrl(fileName)
      window.open(data.publicUrl, '_blank')
    } catch (error) {
      toast.error(`Failed to download file: ${error}`)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-gray-600">Loading report...</p>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-red-600">Report not found</p>
      </div>
    )
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

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Report {reportId.slice(0, 8)}...</h1>
            <p className="text-gray-600 mt-2">Financial Year {report.year}</p>
          </div>
          <span className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(report.status)}`}>
            {report.status.charAt(0).toUpperCase() + report.status.slice(1)}
          </span>
        </div>

        {/* Key Info */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">File Type</p>
            <p className="text-lg font-semibold text-gray-900">{report.file_type}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Score</p>
            <p className="text-lg font-semibold text-gray-900">
              {report.overall_score ? `${Math.round(report.overall_score)}%` : '-'}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Created</p>
            <p className="text-lg font-semibold text-gray-900">
              {new Date(report.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Updated</p>
            <p className="text-lg font-semibold text-gray-900">
              {new Date(report.updated_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        {report.status === 'completed' && (
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => downloadFile('statements')}
              className="btn-primary"
            >
              ⬇️ Download Statements
            </button>
            <button
              onClick={() => downloadFile('certificate')}
              className="btn-secondary"
            >
              ⬇️ Download Certificate
            </button>
          </div>
        )}

        {report.status === 'processing' && (
          <div className="card bg-blue-50 border border-blue-200 mb-6">
            <p className="text-blue-900">⏳ Processing in progress. This page will auto-refresh.</p>
          </div>
        )}

        {report.status === 'failed' && (
          <div className="card bg-red-50 border border-red-200 mb-6">
            <p className="text-red-900 font-semibold">Error</p>
            <p className="text-red-800 text-sm mt-1">{report.error_message || 'Unknown error'}</p>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-4 border-b mb-6">
        {(['overview', 'qa', 'logs'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab === 'qa' ? 'QA Report' : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="card">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Report Details</h3>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Report ID</dt>
                  <dd className="font-mono text-sm text-gray-900">{report.id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Status</dt>
                  <dd className="text-gray-900 capitalize">{report.status}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">File Type</dt>
                  <dd className="text-gray-900">{report.file_type}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Overall Score</dt>
                  <dd className="text-gray-900">
                    {report.overall_score ? `${Math.round(report.overall_score)}%` : 'N/A'}
                  </dd>
                </div>
              </dl>
            </div>

            {report.qa_report && (
              <div className="mt-6 pt-6 border-t">
                <h3 className="font-semibold text-gray-900 mb-2">QA Summary</h3>
                <dl className="space-y-2">
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Overall Status</dt>
                    <dd className="text-gray-900 capitalize">
                      {report.qa_report.overall_status}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Checks Passed</dt>
                    <dd className="text-gray-900">
                      {report.qa_report.summary?.passed_checks || 0}
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        )}

        {activeTab === 'qa' && report.qa_report && (
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Quality Assurance Report</h3>
              {report.qa_report.checks && (
                <div className="space-y-3">
                  {report.qa_report.checks.map((check: any, index: number) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-md">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="font-medium text-gray-900">{check.check_name}</h4>
                        <span className={`text-sm font-medium px-2 py-1 rounded ${
                          check.status === 'PASS' ? 'bg-green-100 text-green-800' :
                          check.status === 'FAIL' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {check.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{check.details}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Processing Logs</h3>
            <div className="bg-gray-50 p-4 rounded-md font-mono text-sm text-gray-700 max-h-96 overflow-auto">
              {report.processing_log && report.processing_log.length > 0 ? (
                <div className="space-y-1">
                  {report.processing_log.map((log: string, index: number) => (
                    <div key={index}>{log}</div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No logs available</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
