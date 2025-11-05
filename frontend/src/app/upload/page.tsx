'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { createClient } from '@supabase/supabase-js'
import toast from 'react-hot-toast'
import axios from 'axios'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export default function Upload() {
  const router = useRouter()
  const supabase = createClient(supabaseUrl, supabaseAnonKey)
  
  const [files, setFiles] = useState<File[]>([])
  const [year, setYear] = useState<number>(2025)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const supportedFormats = ['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']
    
    const validFiles = acceptedFiles.filter(file => {
      if (!supportedFormats.includes(file.type)) {
        toast.error(`${file.name} - Unsupported file format`)
        return false
      }
      if (file.size > 50 * 1024 * 1024) {
        toast.error(`${file.name} - File too large (max 50MB)`)
        return false
      }
      return true
    })

    setFiles(prev => [...prev, ...validFiles])
    toast.success(`${validFiles.length} file(s) added`)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
  })

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Please select at least one file')
      return
    }

    try {
      setUploading(true)
      const { data: { user } } = await supabase.auth.getUser()

      if (!user) {
        toast.error('Not authenticated')
        return
      }

      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        setProgress(Math.round((i / files.length) * 100))

        // Upload file to Supabase storage
        const fileName = `${user.id}/${Date.now()}_${file.name}`
        const { error: uploadError } = await supabase.storage
          .from('uploads')
          .upload(fileName, file)

        if (uploadError) throw uploadError

        // Get public URL
        const { data } = supabase.storage.from('uploads').getPublicUrl(fileName)
        
        // Submit for processing
        const response = await axios.post('/api/process', {
          file_path: data.publicUrl,
          user_id: user.id,
          year: year,
        })

        if (response.status === 200) {
          toast.success(`${file.name} submitted for processing`)
        }
      }

      setProgress(100)
      toast.success('All files uploaded successfully!')
      setFiles([])
      setProgress(0)
      
      // Redirect to dashboard
      setTimeout(() => {
        router.push('/dashboard')
      }, 1500)
    } catch (error) {
      toast.error(`Upload failed: ${error}`)
      setUploading(false)
      setProgress(0)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Upload Financial Statements</h1>
        <p className="text-gray-600 mt-2">Upload 2024 PDF templates and 2025 financial data</p>
      </div>

      <div className="card">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <div className="text-4xl mb-2">📄</div>
          {isDragActive ? (
            <p className="text-lg font-medium text-blue-600">Drop files here...</p>
          ) : (
            <>
              <p className="text-lg font-medium text-gray-900">Drag and drop files here</p>
              <p className="text-sm text-gray-600 mt-1">or click to select files</p>
            </>
          )}
          <p className="text-xs text-gray-500 mt-4">
            Supported formats: PDF, Excel (.xlsx, .xls) | Max size: 50MB
          </p>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-8">
            <h3 className="font-semibold text-gray-900 mb-4">Selected Files ({files.length})</h3>
            <div className="space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">
                      {file.type === 'application/pdf' ? '📕' : '📊'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    disabled={uploading}
                    className="text-red-600 hover:text-red-700 disabled:text-gray-400"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Year Selection */}
        <div className="mt-8">
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Financial Year
          </label>
          <select
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
            disabled={uploading}
            className="input-field"
          >
            <option value={2024}>2024 (Template)</option>
            <option value={2025}>2025 (Data)</option>
            <option value={2026}>2026</option>
          </select>
        </div>

        {/* Progress Bar */}
        {uploading && (
          <div className="mt-8">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium text-gray-900">Uploading...</p>
              <p className="text-sm text-gray-600">{progress}%</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex gap-3">
          <button
            onClick={handleUpload}
            disabled={uploading || files.length === 0}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? 'Uploading...' : 'Start Processing'}
          </button>
          <button
            onClick={() => {
              setFiles([])
              setProgress(0)
            }}
            disabled={uploading}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-8 card bg-blue-50 border border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-2">ℹ️ How it works</h4>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>Upload 2024 PDF template to establish format</li>
          <li>Upload 2025 Excel file with financial data</li>
          <li>System will process and generate matching statements</li>
          <li>Review results in your dashboard</li>
        </ol>
      </div>
    </div>
  )
}
