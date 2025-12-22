import { useRef } from 'react'
import { Send, Paperclip, Loader2, X, ChevronDown, FileText, Brain, Zap } from 'lucide-react'

const MODELS = [
    { id: 'gpt-4o', label: 'GPT-4o', icon: Brain, description: 'High Intelligence' },
    { id: 'gpt-4o-mini', label: 'GPT-4o Mini', icon: Zap, description: 'High Speed' }
]

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
    FOCUS_MODES,
    selectedModel,
    onSelectModel,
    showModelMenu,
    setShowModelMenu
}) {
    return (
        <div className={`w-full ${centered ? 'max-w-3xl mx-auto' : ''}`}>
            {/* ... existing upload preview code ... */}
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
                        <div className="flex items-center gap-2">
                            {/* Focus Selection Responsive Wrapper */}
                            <div className="flex items-center">
                                {/* ... Focus Mode Mobile ... */}
                                <div className="relative lg:hidden">
                                    <button
                                        type="button"
                                        onClick={() => setShowFocusMenu(!showFocusMenu)}
                                        className="flex items-center gap-2 px-3 py-1.5 rounded-full hover:bg-zinc-900 text-xs font-medium text-pplx-text transition-colors"
                                    >
                                        {(() => {
                                            const mode = FOCUS_MODES.find(m => m.id === focusMode) || FOCUS_MODES[0]
                                            const ModeIcon = mode.icon
                                            return <ModeIcon className="w-5 h-5 text-pplx-accent" />
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
                                            <div className={`absolute ${centered ? 'top-full mt-2' : 'bottom-full mb-2'} left-0 -ml-2 w-48 bg-black border border-zinc-800 rounded-xl shadow-xl z-30 overflow-hidden py-1 animate-fade-in`}>
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

                                {/* ... Focus Mode Desktop ... */}
                                <div className="hidden lg:flex items-center gap-1">
                                    {FOCUS_MODES.map((mode) => (
                                        <button
                                            key={mode.id}
                                            type="button"
                                            onClick={() => setFocusMode(mode.id)}
                                            className={`
                                            group/mode relative flex items-center justify-center w-8 h-8 rounded-full text-xs font-medium transition-all duration-200
                                            ${focusMode === mode.id
                                                    ? 'text-pplx-accent bg-pplx-accent/10'
                                                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                                                }
                                        `}
                                        >
                                            <mode.icon className={`w-5 h-5 ${focusMode === mode.id ? 'text-pplx-accent' : 'text-current'}`} />

                                            {/* Hover Tooltip */}
                                            <div className={`absolute ${centered ? 'top-full mt-2' : 'bottom-full mb-2'} left-0 w-max max-w-[250px] px-3 py-2 bg-zinc-950 border border-white/10 rounded-lg shadow-xl opacity-0 group-hover/mode:opacity-100 invisible group-hover/mode:visible transition-all duration-200 z-50 pointer-events-none transform ${centered ? '-translate-y-1' : 'translate-y-1'} group-hover/mode:translate-y-0`}>
                                                <div className="text-left">
                                                    <span className="font-semibold block mb-0.5 text-pplx-accent text-base">{mode.label}</span>
                                                    <span className="text-xs text-zinc-300 font-normal leading-normal block">{mode.description}</span>
                                                </div>
                                                {/* Arrow visual */}
                                                <div className={`absolute ${centered ? '-top-1 border-t' : '-bottom-1 border-b'} left-4 w-2 h-2 bg-zinc-950 border-l border-white/10 rotate-45`}></div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Separator */}
                            <div className="h-4 w-px bg-zinc-800 mx-1 hidden lg:block" />

                            {/* Model Selector (New) */}
                            <div className="relative">
                                <button
                                    type="button"
                                    onClick={() => setShowModelMenu(!showModelMenu)}
                                    className="flex items-center gap-2 px-3 py-1.5 rounded-full hover:bg-zinc-900 text-xs font-medium text-pplx-text transition-colors group/model"
                                >
                                    {(() => {
                                        const model = MODELS.find(m => m.id === selectedModel) || MODELS[0]
                                        const ModelIcon = model.icon
                                        return <ModelIcon className="w-4 h-4 text-pplx-accent" />
                                    })()}
                                    <span className="hidden sm:inline text-sm">{(MODELS.find(m => m.id === selectedModel) || MODELS[0]).label}</span>
                                    <ChevronDown className={`w-3 h-3 opacity-50 transition-transform ${showModelMenu ? 'rotate-180' : ''}`} />
                                </button>

                                {showModelMenu && (
                                    <>
                                        <div
                                            className="fixed inset-0 z-10"
                                            onClick={() => setShowModelMenu(false)}
                                        />
                                        <div className={`absolute ${centered ? 'top-full mt-2' : 'bottom-full mb-2'} left-0 w-48 bg-black border border-zinc-800 rounded-xl shadow-xl z-30 overflow-hidden py-1 animate-fade-in`}>
                                            {MODELS.map((model) => (
                                                <button
                                                    key={model.id}
                                                    type="button"
                                                    onClick={() => {
                                                        onSelectModel(model.id)
                                                        setShowModelMenu(false)
                                                    }}
                                                    className={`
                                                      w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-zinc-900 transition-colors
                                                      ${selectedModel === model.id ? 'text-pplx-accent bg-zinc-900' : 'text-zinc-400'}
                                                    `}
                                                >
                                                    <model.icon className="w-4 h-4" />
                                                    <div className="flex flex-col">
                                                        <span className="text-sm font-medium">{model.label}</span>
                                                        <span className="text-[10px] opacity-60">{model.description}</span>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </>
                                )}
                            </div>
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
