import { Plus, MessageSquare, Trash2, X, Menu, Sparkles, Zap, Brain } from 'lucide-react'

/**
 * Sidebar Component
 * 
 * Displays:
 * 1. Application Logo (Planck AI)
 * 2. New Chat Button
 * 3. List of recent conversations (with auto-grouped date headers logic inferred)
 * 4. Model Toggle Strategy (GPt-4o vs Mini)
 */
export default function Sidebar({
    isOpen,
    conversations,
    activeConversation,
    onSelectConversation,
    onNewChat,
    onDeleteConversation,
    selectedModel,
    onSelectModel
}) {
    // Format date for display (UK London time)
    const formatDate = (dateString) => {
        if (!dateString) return ''
        try {
            const date = new Date(dateString)
            // Format time in 24h for London timezone
            const timeStr = date.toLocaleTimeString('en-GB', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
                timeZone: 'Europe/London'
            })
            // Format date with ordinal suffix
            const day = date.toLocaleDateString('en-GB', { day: 'numeric', timeZone: 'Europe/London' })
            const month = date.toLocaleDateString('en-GB', { month: 'short', timeZone: 'Europe/London' })
            const year = date.toLocaleDateString('en-GB', { year: 'numeric', timeZone: 'Europe/London' })

            // Add ordinal suffix (1st, 2nd, 3rd, etc.)
            const dayNum = parseInt(day)
            const suffix = ['th', 'st', 'nd', 'rd'][(dayNum % 100 > 10 && dayNum % 100 < 14) ? 0 : (dayNum % 10 < 4) ? dayNum % 10 : 0]

            return `${timeStr} · ${dayNum}${suffix} ${month}, ${year}`
        } catch {
            return ''
        }
    }

    return (
        <aside
            className={`
        fixed lg:relative inset-y-0 left-0 z-40
        w-96 bg-[#151616]
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-0 lg:opacity-0'}
        flex flex-col
        mt-[73px] lg:mt-0
      `}
        >
            {/* Logo Area (Desktop) */}
            <div className="p-4 pl-6 pt-8 hidden lg:block">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-pplx-accent flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity" title="Planck AI">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <span className="text-xl font-serif font-medium text-pplx-text tracking-wide flex items-center gap-1">Planck <span className="text-pplx-accent">AI</span></span>
                        <p className="text-xs text-pplx-muted font-medium tracking-wide mt-0.5">Autonomous Reasoning Engine</p>
                    </div>
                </div>
            </div>

            {/* New Chat Button */}
            <div className="p-4 border-b-0">
                <button
                    onClick={onNewChat}
                    className="w-full btn-secondary flex items-center justify-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    New Conversation
                </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {conversations.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center text-pplx-muted pb-8">
                        <MessageSquare className="w-14 h-14 mx-auto mb-4 opacity-40" />
                        <p className="text-lg font-medium">No conversations yet</p>
                        <p className="text-sm mt-1 opacity-70">Start chatting to create one</p>
                    </div>
                ) : (
                    conversations.map((conv) => (
                        <div
                            key={conv.id}
                            className={`
                group relative w-full rounded-lg transition-all duration-200
                hover:bg-pplx-hover
                ${activeConversation === conv.id
                                    ? 'bg-pplx-hover border border-pplx-border'
                                    : 'border border-transparent'
                                }
              `}
                        >
                            <button
                                onClick={() => onSelectConversation(conv.id)}
                                className="w-full text-left p-3 pr-10"
                            >
                                <div className="flex items-start gap-3">
                                    <div className={`
                    w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                    ${activeConversation === conv.id
                                            ? 'bg-pplx-card border border-pplx-border'
                                            : 'bg-pplx-card'
                                        }
                  `}>
                                        <MessageSquare className="w-4 h-4 text-pplx-text" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-base font-medium text-pplx-text truncate">
                                            {conv.title || 'New Conversation'}
                                        </p>
                                        <p className="text-xs text-pplx-muted mt-1">
                                            {formatDate(conv.created_at)}
                                        </p>
                                    </div>
                                </div>
                            </button>

                            {/* Delete Button */}
                            <button
                                onClick={(e) => {
                                    e.stopPropagation()
                                    onDeleteConversation(conv.id)
                                }}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md text-pplx-muted hover:text-red-400 hover:bg-red-500/10 transition-all"
                                title="Delete conversation"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </aside>
    )
}
