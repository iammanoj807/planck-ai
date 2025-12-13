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
    // Format date for display
    const formatDate = (dateString) => {
        if (!dateString) return ''
        const date = new Date(dateString)
        const now = new Date()
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))

        if (diffDays === 0) return 'Today'
        if (diffDays === 1) return 'Yesterday'
        if (diffDays < 7) return `${diffDays} days ago`
        return date.toLocaleDateString()
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
            <div className="p-4 pl-6 hidden lg:block">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-pplx-accent flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity" title="Planck AI">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-xl font-serif font-medium text-pplx-text tracking-wide flex items-center gap-1">Planck <span className="text-pplx-accent">AI</span></span>
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
                    <div className="text-center py-8 text-pplx-muted">
                        <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-50" />
                        <p className="text-sm">No conversations yet</p>
                        <p className="text-xs mt-1">Start chatting to create one</p>
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
                                        <p className="text-sm font-medium text-pplx-text truncate">
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
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md text-pplx-muted hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                                title="Delete conversation"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/5">
                <div className="flex flex-col gap-2">
                    <p className="text-xs font-medium text-pplx-muted px-1">AI Model Strategy</p>
                    <div className="grid grid-cols-2 gap-1 bg-black/20 p-1 rounded-lg border border-white/5">
                        <button
                            onClick={() => onSelectModel('gpt-4o-mini')}
                            className={`
                                flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-medium transition-all
                                ${selectedModel === 'gpt-4o-mini'
                                    ? 'bg-pplx-accent/10 text-pplx-accent border border-pplx-accent/20'
                                    : 'text-pplx-muted hover:text-white hover:bg-white/5'}
                            `}
                        >
                            <Zap className={`w-3 h-3 ${selectedModel === 'gpt-4o-mini' ? 'fill-current' : ''}`} />
                            <span>GPT-4o Mini</span>
                        </button>
                        <button
                            onClick={() => onSelectModel('gpt-4o')}
                            className={`
                                flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-medium transition-all
                                ${selectedModel === 'gpt-4o'
                                    ? 'bg-pplx-accent/10 text-pplx-accent border border-pplx-accent/20'
                                    : 'text-pplx-muted hover:text-white hover:bg-white/5'}
                            `}
                        >
                            <Brain className={`w-3 h-3 ${selectedModel === 'gpt-4o' ? 'fill-current' : ''}`} />
                            <span>GPT-4o</span>
                        </button>
                    </div>
                    <p className="text-[10px] text-pplx-muted/60 text-center mt-1">
                        {selectedModel === 'gpt-4o' ? 'High Intelligence • 8k Token Limit' : 'High Speed • 8k Token Limit'}
                    </p>
                </div>
            </div>
        </aside>
    )
}
