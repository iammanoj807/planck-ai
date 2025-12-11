import { useState, useCallback, useEffect } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatInterface from './components/ChatInterface'

/**
 * Main Application Component
 * 
 * Manages the global state of the application:
 * - Conversations list and active conversation
 * - Sidebar visibility (responsive)
 * - Selected AI Model (GPT-4o vs GPT-4o Mini)
 * - Theme and layout structure
 */
function App() {
    const [conversations, setConversations] = useState([])
    const [activeConversation, setActiveConversation] = useState(null)
    const [messages, setMessages] = useState([])
    // Sidebar defaults to open on large screens, closed on mobile
    const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 1024)
    const [selectedModel, setSelectedModel] = useState('gpt-4o-mini')

    // Handle resize to auto-close/open
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth >= 1024) {
                setSidebarOpen(true)
            } else {
                setSidebarOpen(false)
            }
        }
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    /**
     * Start a new chat session.
     * Clears the current messages and active conversation ID.
     */
    const handleNewChat = useCallback(() => {
        setActiveConversation(null)
        setMessages([])
        if (window.innerWidth < 1024) setSidebarOpen(false)
    }, [])

    /**
     * Load an existing conversation by ID.
     * Fetches history from the backend.
     */
    const handleSelectConversation = useCallback(async (conversationId) => {
        setActiveConversation(conversationId)
        if (window.innerWidth < 1024) setSidebarOpen(false)

        try {
            const response = await fetch(`/conversations/${conversationId}`)
            const data = await response.json()
            setMessages(data.messages || [])
        } catch (error) {
            console.error('Failed to load conversation:', error)
        }
    }, [])

    // Add message to current conversation state locally
    const handleAddMessage = useCallback((message) => {
        setMessages(prev => [...prev, message])
    }, [])

    /**
     * Called when the backend assigns a Conversation ID to a new chat.
     * Updates the URL/State and refreshes the sidebar list.
     */
    const handleConversationUpdate = useCallback((conversationId) => {
        setActiveConversation(conversationId)

        // Refresh conversations list
        fetch('/conversations')
            .then(res => res.json())
            .then(data => setConversations(data.conversations || []))
            .catch(console.error)
    }, [])

    // Delete conversation permanently
    const handleDeleteConversation = useCallback(async (conversationId) => {
        try {
            await fetch(`/conversations/${conversationId}`, {
                method: 'DELETE'
            })

            setConversations(prev => prev.filter(c => c.id !== conversationId))

            if (activeConversation === conversationId) {
                setActiveConversation(null)
                setMessages([])
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error)
        }
    }, [activeConversation])

    // Load conversations list on initial mount
    useEffect(() => {
        fetch('/conversations')
            .then(res => res.json())
            .then(data => setConversations(data.conversations || []))
            .catch(console.error)
    }, [])

    return (
        <div className="h-screen overflow-hidden flex flex-col bg-pplx-dark">
            {/* Header */}
            <Header
                onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
                onNewChat={handleNewChat}
            />

            {/* Main content */}
            <div className="flex-1 flex overflow-hidden">
                <Sidebar
                    isOpen={sidebarOpen}
                    conversations={conversations}
                    activeConversation={activeConversation}
                    onSelectConversation={handleSelectConversation}
                    onNewChat={handleNewChat}
                    onDeleteConversation={handleDeleteConversation}
                    selectedModel={selectedModel}
                    onSelectModel={setSelectedModel}
                />

                {/* Sidebar Toggle Button (Desktop) */}
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className={`
                        hidden lg:flex items-center justify-center
                        absolute top-1/2 -translate-y-1/2 z-50
                        w-6 h-12
                        bg-pplx-card border border-l-0 border-pplx-border
                        rounded-r-lg
                        text-pplx-muted hover:text-pplx-accent
                        transition-all duration-300 ease-in-out
                        ${sidebarOpen ? 'left-96' : 'left-0 border-l'}
                    `}
                    aria-label="Toggle Sidebar"
                >
                    {sidebarOpen ? (
                        <ChevronLeft className="w-4 h-4" />
                    ) : (
                        <ChevronRight className="w-4 h-4" />
                    )}
                </button>

                {/* Chat area */}
                <main className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-0' : 'ml-0'}`}>
                    <ChatInterface
                        conversationId={activeConversation}
                        messages={messages}
                        onAddMessage={handleAddMessage}
                        onConversationUpdate={handleConversationUpdate}
                        selectedModel={selectedModel}
                    />
                </main>
            </div>
        </div>
    )
}

export default App
