import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { User, Bot, AlertCircle, Image, FileText, Clock, Check, Copy, Terminal } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import ReasoningPanel from './ReasoningPanel'
import RateLimitCountdown from './RateLimitCountdown'

/**
 * Message Bubble Component
 * 
 * Renders an individual chat message.
 * Handles:
 * - Markdown rendering for rich text
 * - Syntax highlighting for code blocks
 * - Rate limit countdown timers
 * - Analysis/Thinking visualization (ReasoningPanel)
 * - User vs Assistant styling differences
 */
export default function MessageBubble({ message }) {
    const isUser = message.role === 'user'
    const isError = message.isError
    const isRateLimit = message.isRateLimit
    const toolCalls = message.toolCalls || []

    const [copiedIndex, setCopiedIndex] = useState(null)

    const handleCopyCode = (code, index) => {
        navigator.clipboard.writeText(code)
        setCopiedIndex(index)
        setTimeout(() => setCopiedIndex(null), 2000)
    }

    // Check if effective rate limit (prop or hydrated)
    const rateLimitMatch = message.content && message.content.match(/Retrying allowed in: (\d+)s/)
    const rateLimitSeconds = rateLimitMatch ? parseInt(rateLimitMatch[1]) : 0
    const effectiveRateLimit = isRateLimit || rateLimitSeconds > 0

    // Thinking state analysis
    const isThinkingRunning = Array.isArray(toolCalls) && toolCalls.some(t => t.status === 'running')
    // Show top indicator IF it's running. If finished, we'll show it below the text.
    const showTopReasoning = isThinkingRunning && toolCalls.length > 0
    // Show bottom reasoning IF it's consistent and NOT running (completed)
    const showBottomReasoning = !isThinkingRunning && Array.isArray(toolCalls) && toolCalls.length > 0

    // Unified content processing for both User and Assistant
    const getDisplayContent = () => {
        const content = message.content || ''
        if (content.includes('tokens_limit_reached') || content.includes('413')) {
            return "**Message Limit Reached (Free Tier)**\n\nConversation history exceeds the 8k token limit.\n\n**Solution:** Please start a new chat."
        }
        if (isUser) {
            return content.replace(/^\[Mode: .*?\]\s*/, '')
        }
        return content
    }

    const displayContent = getDisplayContent()

    return (
        <div className={`flex gap-3 group animate-fade-in ${isUser ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`
        w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center
        ${isUser
                    ? 'bg-zinc-700' // Neutral Gray for User
                    : effectiveRateLimit
                        ? 'bg-red-500/20 border border-red-500/30'
                        : isError
                            ? 'bg-red-500/20 border border-red-500/30'
                            : 'bg-cyan-500/20 text-pplx-accent' // Cyan/Teal for AI (Brand Match)
                }
      `}>
                {isUser ? (
                    <User className="w-6 h-6 text-white/90 fill-white/20" />
                ) : effectiveRateLimit ? (
                    <Clock className="w-5 h-5 text-red-400" />
                ) : isError ? (
                    <AlertCircle className="w-5 h-5 text-red-400" />
                ) : (
                    <Bot className="w-5 h-5 text-cyan-400" />
                )}
            </div>

            {/* Message content */}
            <div className={`max-w-[85%] overflow-hidden ${isUser ? 'items-end' : 'items-start w-full'}`}>
                {/* Files preview for user messages */}
                {message.files && message.files.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2">
                        {message.files.map((file, index) => (
                            <div key={index} className="glass-card-light rounded-lg overflow-hidden">
                                {file.preview ? (
                                    <img src={file.preview} alt="" className="max-w-48 max-h-48 object-cover" />
                                ) : (
                                    <div className="p-3 flex items-center gap-2">
                                        <FileText className="w-5 h-5 text-cyan-400" />
                                        <span className="text-sm text-slate-300">{file.original_name}</span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Text content */}
                <div className={`
          px-4 py-3
          ${isUser ? 'message-user' : effectiveRateLimit ? 'bg-red-500/10 border border-red-500/30 rounded-2xl' : isError ? 'bg-red-500/10 border border-red-500/30 rounded-2xl' : 'message-assistant'}
        `}>
                    {!isUser && showTopReasoning && (
                        <div className="-mt-1 mb-3">
                            <ReasoningPanel toolCalls={toolCalls} />
                        </div>
                    )}
                    {isUser ? (
                        <p className="text-white whitespace-pre-wrap break-words">
                            {displayContent}
                        </p>
                    ) : effectiveRateLimit ? (
                        <RateLimitCountdown initialSeconds={rateLimitSeconds} />
                    ) : (
                        <div className={`markdown-content max-w-full overflow-hidden ${isError ? 'text-red-300' : 'text-slate-200'}`}>
                            <ReactMarkdown
                                components={{
                                    code({ node, inline, className, children, ...props }) {
                                        const match = /language-(\w+)/.exec(className || '')
                                        const language = match ? match[1] : ''
                                        const codeString = String(children).replace(/\n$/, '')
                                        // Stable ID based on content length + first 10 chars to prevent re-render mismatches
                                        const index = `code-${codeString.length}-${codeString.substring(0, 10).replace(/\s/g, '')}`

                                        if (inline) {
                                            return <code className="bg-cyan-500/10 px-1.5 py-0.5 rounded text-cyan-300" {...props}>{children}</code>
                                        }

                                        return (
                                            <div className="my-4 rounded-lg overflow-hidden border border-[#2E3030] bg-[#1E1E1E] max-w-full w-full">
                                                {/* Code Header */}
                                                <div className="flex items-center justify-between px-3 py-2 bg-[#252526] border-b border-[#2E3030]">
                                                    <div className="flex items-center gap-2">
                                                        <Terminal className="w-4 h-4 text-slate-400" />
                                                        <span className="text-xs text-slate-400 font-mono">
                                                            {language || 'text'}
                                                        </span>
                                                    </div>
                                                    <button
                                                        onClick={() => handleCopyCode(codeString, index)}
                                                        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                                                    >
                                                        {copiedIndex === index ? (
                                                            <>
                                                                <Check className="w-3.5 h-3.5 text-green-400" />
                                                                <span className="text-green-400">Copied</span>
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Copy className="w-3.5 h-3.5" />
                                                                <span>Copy</span>
                                                            </>
                                                        )}
                                                    </button>
                                                </div>
                                                {/* Code Body */}
                                                <div className="overflow-x-auto text-[15px] bg-[#1E1E1E]" style={{ maxWidth: 'calc(100vw - 6rem)' }}>
                                                    <SyntaxHighlighter
                                                        style={(() => {
                                                            const theme = { ...vscDarkPlus }
                                                            // Remove container-level styles to prevent clashes
                                                            delete theme['pre[class*="language-"]']
                                                            delete theme['code[class*="language-"]']
                                                            return theme
                                                        })()}
                                                        language={language}
                                                        PreTag="div"
                                                        customStyle={{
                                                            margin: 0,
                                                            padding: '1rem',
                                                            background: 'transparent',
                                                            fontSize: '15px',
                                                            lineHeight: '1.6',
                                                            border: 'none',
                                                            boxShadow: 'none'
                                                        }}
                                                        codeTagProps={{
                                                            style: {
                                                                background: 'transparent',
                                                                border: 'none',
                                                                boxShadow: 'none'
                                                            }
                                                        }}
                                                        {...props}
                                                    >
                                                        {codeString}
                                                    </SyntaxHighlighter>
                                                </div>
                                            </div>
                                        )
                                    },
                                    a({ href, children }) {
                                        return (
                                            <a href={href} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
                                                {children}
                                            </a>
                                        )
                                    }
                                }}
                            >
                                {displayContent}
                            </ReactMarkdown>
                            {!isUser && (showBottomReasoning || message.model) && (
                                <div className="mt-4 pt-3">
                                    <ReasoningPanel toolCalls={toolCalls} model={message.model} timestamp={message.timestamp} />
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Copy Button (Option 2: Below the bubble) */}
                {isUser && (
                    <div className="flex justify-end mt-1.5 mr-1 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                        <button
                            onClick={() => handleCopyCode(displayContent, `msg-${message.id}`)}
                            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-white transition-colors px-2 py-1 rounded hover:bg-white/5"
                        >
                            {copiedIndex === `msg-${message.id}` ? (
                                <>
                                    <Check className="w-3.5 h-3.5 text-green-400" />
                                    <span className="text-green-400">Copied</span>
                                </>
                            ) : (
                                <>
                                    <Copy className="w-3.5 h-3.5" />
                                    <span>Copy</span>
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>
        </div >
    )
}
