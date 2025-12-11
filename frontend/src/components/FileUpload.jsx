import { useCallback, useState } from 'react'
import { Upload, X, Image, FileText, Loader2 } from 'lucide-react'

export default function FileUpload({ onFilesUploaded, maxFiles = 5 }) {
    const [isDragging, setIsDragging] = useState(false)
    const [isUploading, setIsUploading] = useState(false)
    const [uploadedFiles, setUploadedFiles] = useState([])

    const handleDragOver = useCallback((e) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e) => {
        e.preventDefault()
        setIsDragging(false)
    }, [])

    const handleDrop = useCallback(async (e) => {
        e.preventDefault()
        setIsDragging(false)

        const files = Array.from(e.dataTransfer.files)
        await uploadFiles(files)
    }, [])

    const handleFileSelect = useCallback(async (e) => {
        const files = Array.from(e.target.files)
        await uploadFiles(files)
    }, [])

    const uploadFiles = async (files) => {
        if (uploadedFiles.length + files.length > maxFiles) {
            alert(`Maximum ${maxFiles} files allowed`)
            return
        }

        setIsUploading(true)
        const uploaded = []

        for (const file of files) {
            const formData = new FormData()
            formData.append('file', file)

            try {
                const response = await fetch('http://localhost:8000/upload', {
                    method: 'POST',
                    body: formData
                })
                const data = await response.json()

                uploaded.push({
                    ...data,
                    preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
                })
            } catch (error) {
                console.error('Upload failed:', error)
            }
        }

        const newFiles = [...uploadedFiles, ...uploaded]
        setUploadedFiles(newFiles)
        onFilesUploaded?.(newFiles)
        setIsUploading(false)
    }

    const removeFile = (index) => {
        const newFiles = uploadedFiles.filter((_, i) => i !== index)
        setUploadedFiles(newFiles)
        onFilesUploaded?.(newFiles)
    }

    return (
        <div className="space-y-3">
            {/* Drop zone */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
          border-2 border-dashed rounded-xl p-6 text-center transition-all
          ${isDragging
                        ? 'border-cyan-400 bg-cyan-500/10'
                        : 'border-slate-600 hover:border-slate-500'
                    }
        `}
            >
                <input
                    type="file"
                    id="file-upload"
                    multiple
                    accept="image/*,.pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                    {isUploading ? (
                        <Loader2 className="w-8 h-8 text-cyan-400 mx-auto mb-2 animate-spin" />
                    ) : (
                        <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                    )}
                    <p className="text-sm text-slate-300">
                        {isDragging ? 'Drop files here' : 'Drag & drop or click to upload'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                        Images and PDFs supported
                    </p>
                </label>
            </div>

            {/* Uploaded files */}
            {uploadedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2">
                    {uploadedFiles.map((file, index) => (
                        <div
                            key={index}
                            className="glass-card-light rounded-lg overflow-hidden flex items-center"
                        >
                            {file.preview ? (
                                <img
                                    src={file.preview}
                                    alt=""
                                    className="w-12 h-12 object-cover"
                                />
                            ) : (
                                <div className="w-12 h-12 flex items-center justify-center bg-purple-500/20">
                                    <FileText className="w-5 h-5 text-purple-400" />
                                </div>
                            )}
                            <div className="px-3 py-2 max-w-32">
                                <p className="text-xs text-slate-300 truncate">{file.original_name}</p>
                            </div>
                            <button
                                onClick={() => removeFile(index)}
                                className="p-2 hover:bg-slate-600/50 transition-colors"
                            >
                                <X className="w-4 h-4 text-slate-400" />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
