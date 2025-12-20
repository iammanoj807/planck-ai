import { useState } from 'react'
import { ChevronDown, ChevronRight, Search, Code, Image, FileText, Clock, CheckCircle2, Loader2, BrainCircuit, Bot } from 'lucide-react'

const TOOL_ICONS = {
    web_search: Search,
    code_executor: Code,
    image_analyzer: Image,
    document_reader: FileText,
    thinking: BrainCircuit
}

const TOOL_LABELS = {
    web_search: 'Searched Web',
    code_executor: 'Executed Code',
    image_analyzer: 'Analyzed Image',
    document_reader: 'Read Document',
    thinking: 'Thinking...'
}

export default function ReasoningPanel({ toolCalls, model }) {
    const [isExpanded, setIsExpanded] = useState(false)
    const [expandedTools, setExpandedTools] = useState({})

    const toggleTool = (index) => {
        setExpandedTools(prev => ({
            ...prev,
            [index]: !prev[index]
        }))
    }

    // Always render if model is present, even without tools
    if ((!toolCalls || toolCalls.length === 0) && !model) return null

    const safeToolCalls = toolCalls || []
    const runningCount = safeToolCalls.filter(t => t.status === 'running').length
    const isRunning = runningCount > 0

    return (
        <div className="my-2 animate-fade-in">
            <div className="flex items-center justify-between">
                {/* Left: Tools Toggle */}
                {safeToolCalls.length > 0 ? (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="flex items-center gap-2 px-1 py-1 group hover:bg-white/5 rounded-md transition-colors"
                        title={isExpanded ? "Collapse reasoning" : "View reasoning"}
                    >
                        <div className="relative">
                            {isRunning ? (
                                <Loader2 className="w-4 h-4 text-pplx-accent animate-spin" />
                            ) : (
                                <BrainCircuit className="w-4 h-4 text-pplx-accent" />
                            )}
                        </div>
                        <span className="text-sm font-medium text-slate-300 group-hover:text-pplx-accent transition-colors">
                            {isRunning
                                ? 'Thinking...'
                                : `${safeToolCalls.length} step${safeToolCalls.length !== 1 ? 's' : ''}`
                            }
                        </span>
                        {isExpanded ? (
                            <ChevronDown className="w-3 h-3 text-slate-500" />
                        ) : (
                            <ChevronRight className="w-3 h-3 text-slate-500" />
                        )}
                    </button>
                ) : <div />}

                {/* Right: Model Badge */}
                {model && (
                    <div className="flex items-center gap-1.5 opacity-60 hover:opacity-100 transition-opacity select-none">
                        <Bot className="w-3.5 h-3.5 text-cyan-400" />
                        <span className={`text-[11px] font-medium tracking-wide ${model === 'gpt-4o' ? 'text-cyan-100' : 'text-zinc-400'}`}>
                            {model === 'gpt-4o' ? 'GPT-4o' : 'GPT-4o Mini'}
                        </span>
                    </div>
                )}
            </div>

            {/* Content (Collapsible) */}
            {isExpanded && safeToolCalls.length > 0 && (
                <div className="mt-2 ml-1 pl-4 border-l border-white/10 space-y-3">
                    {safeToolCalls.map((toolCall, index) => {
                        const Icon = TOOL_ICONS[toolCall.tool] || Code
                        const isToolRunning = toolCall.status === 'running'
                        const isToolExpanded = expandedTools[index]

                        if (toolCall.tool === 'thinking') {
                            const isThinkingRunning = toolCall.status === 'running'
                            return (
                                <div key={index} className="group">
                                    <button
                                        onClick={() => toggleTool(index)}
                                        className="w-full flex items-center justify-between text-left hover:bg-white/5 p-1.5 rounded transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <BrainCircuit className={`w-3.5 h-3.5 ${isThinkingRunning ? 'text-pplx-accent animate-pulse' : 'text-slate-400'}`} />
                                            <span className="text-sm text-slate-300 font-medium">Thinking Process</span>
                                        </div>
                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            {isToolExpanded ? (
                                                <ChevronDown className="w-3 h-3 text-slate-500" />
                                            ) : (
                                                <ChevronRight className="w-3 h-3 text-slate-500" />
                                            )}
                                        </div>
                                    </button>

                                    {isToolExpanded && (
                                        <div className="mt-1.5 ml-6">
                                            <div className="text-sm text-slate-300 border-l-2 border-slate-700 pl-3 py-1 italic">
                                                {toolCall.input?.thought || "Analyzing request..."}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )
                        }

                        return (
                            <div key={index} className="group">
                                {/* Tool Header */}
                                <button
                                    onClick={() => toggleTool(index)}
                                    className="w-full flex items-center justify-between text-left hover:bg-white/5 p-1.5 rounded transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Icon className={`w-3.5 h-3.5 ${isToolRunning ? 'text-pplx-accent animate-pulse' : 'text-slate-400'}`} />
                                        <span className="text-sm text-slate-300">
                                            {TOOL_LABELS[toolCall.tool] || toolCall.tool}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        {toolCall.duration && (
                                            <span className="text-xs text-slate-500">{toolCall.duration}ms</span>
                                        )}
                                        {isToolExpanded ? (
                                            <ChevronDown className="w-3 h-3 text-slate-500" />
                                        ) : (
                                            <ChevronRight className="w-3 h-3 text-slate-500" />
                                        )}
                                    </div>
                                </button>

                                {/* Tool Details */}
                                {isToolExpanded && (
                                    <div className="mt-1.5 ml-6 space-y-2 text-xs">
                                        {/* Custom Input Renderer */}
                                        {toolCall.input && (
                                            <div className="bg-[#1e1e1e] p-2 rounded border border-white/10">
                                                <div className="text-slate-500 mb-1">Input</div>
                                                {toolCall.tool === 'web_search' && toolCall.input.query ? (
                                                    <div className="flex items-center gap-2">
                                                        <Search className="w-3 h-3 text-pplx-accent" />
                                                        <span className="text-slate-300">Query:</span>
                                                        <span className="text-white font-medium">{toolCall.input.query}</span>
                                                    </div>
                                                ) : toolCall.tool === 'document_reader' && toolCall.input.source ? (
                                                    <div className="flex items-center gap-2">
                                                        <FileText className="w-3 h-3 text-blue-400" />
                                                        <span className="text-slate-300">Source:</span>
                                                        <a href={toolCall.input.source} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline truncate max-w-[300px]">
                                                            {toolCall.input.source}
                                                        </a>
                                                    </div>
                                                ) : toolCall.tool === 'code_executor' && toolCall.input.code ? (
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2 text-[10px] text-slate-500 mb-1">
                                                            <Code className="w-3 h-3" />
                                                            <span>Language:</span>
                                                            <span className="text-pplx-accent font-medium uppercase">{toolCall.input.language || 'python'}</span>
                                                        </div>
                                                        <div className="relative">
                                                            <pre className="text-slate-300 font-mono text-[10px] whitespace-pre-wrap overflow-x-auto custom-scrollbar bg-black/30 p-2 rounded max-h-48">
                                                                {toolCall.input.code}
                                                            </pre>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <code className="text-slate-300 whitespace-pre-wrap font-mono">
                                                        {JSON.stringify(toolCall.input, null, 2)}
                                                    </code>
                                                )}
                                            </div>
                                        )}

                                        {/* Custom Result Renderer */}
                                        {toolCall.result && (
                                            <div className="bg-[#1e1e1e] p-2 rounded border border-white/10">
                                                <div className="text-slate-500 mb-1">Result</div>
                                                {toolCall.tool === 'web_search' && typeof toolCall.result === 'string' ? (
                                                    <div className="space-y-2">
                                                        {toolCall.result.split('Title: ').slice(1).map((item, i) => {
                                                            const parts = item.split('\n')
                                                            const title = parts[0]
                                                            const urlLine = parts.find(p => p.trim().startsWith('URL: '))
                                                            const url = urlLine ? urlLine.replace('URL: ', '').trim() : '#'
                                                            const descLine = parts.find(p => p.trim().startsWith('Description: '))
                                                            const desc = descLine ? descLine.replace('Description: ', '').trim() : ''

                                                            return (
                                                                <div key={i} className="bg-white/5 p-2 rounded border border-white/5 hover:border-white/20 transition-colors">
                                                                    <a href={url} target="_blank" rel="noopener noreferrer" className="block font-medium text-pplx-accent hover:underline mb-0.5 truncate">
                                                                        {title}
                                                                    </a>
                                                                    <div className="text-[10px] text-slate-500 truncate mb-1">{url}</div>
                                                                    <div className="text-slate-300 line-clamp-2">{desc}</div>
                                                                </div>
                                                            )
                                                        })}
                                                        {/* Fallback if parsing fails or result is empty */}
                                                        {(!toolCall.result.includes('Title: ')) && (
                                                            <code className="text-slate-300 whitespace-pre-wrap font-mono block max-h-40 overflow-y-auto custom-scrollbar">
                                                                {toolCall.result}
                                                            </code>
                                                        )}
                                                    </div>
                                                ) : toolCall.tool === 'document_reader' && typeof toolCall.result === 'string' ? (
                                                    <div className="text-slate-300">
                                                        <div className="flex items-center gap-2 mb-2 text-green-400">
                                                            <CheckCircle2 className="w-3 h-3" />
                                                            <span>Content extracted successfully</span>
                                                        </div>
                                                        <div className="bg-black/20 p-2 rounded text-slate-400 font-mono text-[10px] max-h-32 overflow-y-auto custom-scrollbar">
                                                            {toolCall.result.slice(0, 500)}
                                                            {toolCall.result.length > 500 && '...'}
                                                        </div>
                                                    </div>
                                                ) : toolCall.tool === 'code_executor' ? (
                                                    (() => {
                                                        try {
                                                            // Result is often a JSON string, try to parse it
                                                            const parsed = typeof toolCall.result === 'string' ? JSON.parse(toolCall.result) : toolCall.result

                                                            // Check if result is empty or effectively empty
                                                            const hasOutput = parsed.stdout || parsed.stderr || parsed.error

                                                            if (!hasOutput && parsed.success) {
                                                                return (
                                                                    <div className="font-mono text-[10px] text-zinc-500 italic px-2">
                                                                        No output returned (Success)
                                                                    </div>
                                                                )
                                                            }

                                                            return (
                                                                <div className="font-mono text-[10px]">
                                                                    {/* STDOUT */}
                                                                    {parsed.stdout && (
                                                                        <div className="mb-2">
                                                                            <div className="text-slate-500 text-[9px] mb-0.5 uppercase tracking-wider">Output</div>
                                                                            <div className="bg-black/40 p-2 rounded text-green-400 border-l-2 border-green-500/50 whitespace-pre-wrap">
                                                                                {parsed.stdout}
                                                                            </div>
                                                                        </div>
                                                                    )}

                                                                    {/* STDERR */}
                                                                    {parsed.stderr && (
                                                                        <div className="mb-2">
                                                                            <div className="text-red-400/80 text-[9px] mb-0.5 uppercase tracking-wider">Standard Error</div>
                                                                            <div className="bg-red-950/20 p-2 rounded text-red-300 border-l-2 border-red-500/50 whitespace-pre-wrap">
                                                                                {parsed.stderr}
                                                                            </div>
                                                                        </div>
                                                                    )}

                                                                    {/* General Error */}
                                                                    {parsed.error && (
                                                                        <div className="bg-red-500/10 p-2 rounded text-red-400 border border-red-500/20 flex gap-2 items-start mt-2">
                                                                            <span className="font-bold">Error:</span> {parsed.error}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            )
                                                        } catch (e) {
                                                            // If parsing fails, showing the raw string is better than nothing, but let's try to prettify it if it looks like JSON
                                                            return (
                                                                <code className="text-slate-300 whitespace-pre-wrap font-mono max-h-40 overflow-y-auto block custom-scrollbar text-[10px]">
                                                                    {toolCall.result}
                                                                </code>
                                                            )
                                                        }
                                                    })()
                                                ) : (
                                                    <code className="text-slate-300 whitespace-pre-wrap font-mono max-h-40 overflow-y-auto block custom-scrollbar">
                                                        {toolCall.result}
                                                    </code>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
