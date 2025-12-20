import { useRef } from 'react'
import { Send, Paperclip, Loader2, X, ChevronDown, FileText } from 'lucide-react'

export default function InputArea({
    centered = false,
    input,
    setInput,
    handleSubmit,
    uploadedFiles,
    removeFile,
    fileInputRef,
    handleFileUpload,
    isLoading,
    showFocusMenu,
    setShowFocusMenu,
    focusMode,
    setFocusMode,
    FOCUS_MODES
}) {
    return (
        <div className={`w-full ${centered ? 'max-w-3xl mx-auto' : ''}`}>
            {/* Uploaded files preview */}
            {uploadedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                    {uploadedFiles.map((file, index) => (
                        <div key={index} className="glass-card-light p-2 pr-3 flex items-center gap-2 rounded-lg">
                            {file.preview ? (
                                <img src={file.preview} alt="" className="w-8 h-8 rounded object-cover" />
                            ) : (
                                <FileText className="w-5 h-5 text-pplx-accent" />
                            )}
                            <span className="text-sm text-pplx-text max-w-32 truncate">
                                {file.original_name}
                            </span>
                            <button
                                onClick={() => removeFile(index)}
                                className="p-1 hover:bg-pplx-hover rounded"
                            >
                                <X className="w-3 h-3 text-pplx-muted" />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <form onSubmit={handleSubmit} className="relative group z-10">
                <div className={`
          relative flex flex-col p-2 rounded-2xl transition-all duration-300
          ${centered
                        ? 'bg-pplx-card shadow-2xl shadow-black/20'
                        : 'bg-pplx-card'
                    }
        `}>
                    <textarea
                        ref={(el) => {
                            // Combine ref with auto-resize logic
                            if (el) {
                                el.style.height = 'auto'
                                el.style.height = el.scrollHeight + 'px'
                            }
                        }}
                        value={input}
                        onChange={(e) => {
                            setInput(e.target.value)
                            e.target.style.height = 'auto'
                            e.target.style.height = e.target.scrollHeight + 'px'
                        }}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                handleSubmit(e)
                            }
                        }}
                        placeholder={
                            centered
                                ? (focusMode !== 'all' ? `Ask anything with ${FOCUS_MODES.find(m => m.id === focusMode)?.label}...` : "Ask anything...")
                                : "Message Planck AI..."
                        }
                        rows={1}
                        className={`
              w-full bg-transparent border-0 text-pplx-text placeholder-pplx-muted 
              focus:ring-0 focus:outline-none resize-none py-3 px-2
              max-h-[200px] overflow-y-auto custom-scrollbar
              ${centered ? 'text-base text-left font-medium' : 'text-base md:text-sm'}
            `}
                        style={{ minHeight: centered ? '50px' : '44px' }}
                    />

                    <div className="flex flex-wrap items-center justify-between px-2 pb-1 gap-y-2">
                        {/* Focus Dropdown */}
                        <div className="relative">
                            <button
                                type="button"
                                onClick={() => setShowFocusMenu(!showFocusMenu)}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-full hover:bg-zinc-900 text-xs font-medium text-pplx-text transition-colors"
                            >
                                {(() => {
                                    const mode = FOCUS_MODES.find(m => m.id === focusMode) || FOCUS_MODES[0]
                                    const ModeIcon = mode.icon
                                    return <ModeIcon className="w-4 h-4 text-pplx-accent" />
                                })()}
                                <span>{(FOCUS_MODES.find(m => m.id === focusMode) || FOCUS_MODES[0]).label}</span>
                                <ChevronDown className="w-3 h-3 opacity-50" />
                            </button>

                            {showFocusMenu && (
                                <>
                                    <div
                                        className="fixed inset-0 z-10"
                                        onClick={() => setShowFocusMenu(false)}
                                    />
                                    <div className="absolute bottom-full left-0 mb-4 -ml-8 w-48 bg-black border border-zinc-800 rounded-xl shadow-xl z-30 overflow-hidden py-1">
                                        {FOCUS_MODES.map((mode) => (
                                            <button
                                                key={mode.id}
                                                type="button"
                                                onClick={() => {
                                                    setFocusMode(mode.id)
                                                    setShowFocusMenu(false)
                                                }}
                                                className={`
                          w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-zinc-900 transition-colors
                          ${focusMode === mode.id ? 'text-pplx-accent bg-zinc-900' : 'text-zinc-400'}
                        `}
                                            >
                                                <mode.icon className="w-4 h-4" />
                                                <span className="text-sm font-medium">{mode.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>

                        <div className="flex items-center gap-2">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                accept="image/*,.pdf"
                                className="hidden"
                                disabled={isLoading}
                            />
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isLoading}
                                className={`p-2 rounded-lg transition-colors ${isLoading ? 'text-zinc-600 cursor-not-allowed' : 'hover:bg-pplx-hover text-pplx-muted hover:text-pplx-accent'}`}
                            >
                                <Paperclip className="w-5 h-5" />
                            </button>

                            <button
                                type="submit"
                                disabled={isLoading || (!input.trim() && uploadedFiles.length === 0)}
                                className={`
                  p-2 rounded-full transition-all
                  ${isLoading || (!input.trim() && uploadedFiles.length === 0)
                                        ? 'bg-pplx-hover text-pplx-muted cursor-not-allowed'
                                        : 'bg-pplx-accent hover:bg-cyan-600 text-white shadow-lg shadow-black/20'
                                    }
                `}
                            >
                                {isLoading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Send className="w-4 h-4" />
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </form>
        </div>
    )
}
