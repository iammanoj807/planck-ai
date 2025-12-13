import { useState, useRef, useEffect } from 'react'
import { Search, MessageSquareText, ArrowDown } from 'lucide-react'
import MessageBubble from './MessageBubble'
import ReasoningPanel from './ReasoningPanel'
import InputArea from './InputArea'
import HeroSection from './HeroSection'

const FOCUS_MODES = [
    { id: 'web', label: 'Web Search', icon: Search, description: 'Search the internet' },
    { id: 'chat', label: 'Chat Only', icon: MessageSquareText, description: 'Chat without searching' },
]

/**
 * Chat Interface Component
 * 
 * The core chat view. Handles:
 * 1. Rendering the message list (MessageBubble).
 * 2. Managing the input area and file uploads.
 * 3. Communicating with the Backend API via Streaming (Send/Receive).
 * 4. Parsing the complex SSE (Server-Sent Events) stream for thinking/tools/responses.
 */
export default function ChatInterface({
    conversationId,
    messages,
    onAddMessage,
    onConversationUpdate,
    selectedModel // New prop: 'gpt-4o' | 'gpt-4o-mini'
}) {
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [toolCalls, setToolCalls] = useState([])
    const [uploadedFiles, setUploadedFiles] = useState([])
    const [streamingMessage, setStreamingMessage] = useState('')

    const [focusMode, setFocusMode] = useState('web')
    const [showFocusMenu, setShowFocusMenu] = useState(false)
    const [showScrollButton, setShowScrollButton] = useState(false)

    const messagesEndRef = useRef(null)
    const scrollContainerRef = useRef(null)
    const fileInputRef = useRef(null)

    const scrollToBottom = () => {
        if (!scrollContainerRef.current) return
        scrollContainerRef.current.scrollTo({
            top: scrollContainerRef.current.scrollHeight,
            behavior: 'smooth'
        })
    }

    // Auto-scroll logic: Only scroll if user is near bottom
    const isUserNearBottom = useRef(true)

    const handleScroll = () => {
        if (!scrollContainerRef.current) return
        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current
        const distanceFromBottom = scrollHeight - scrollTop - clientHeight
        isUserNearBottom.current = distanceFromBottom < 30
        setShowScrollButton(distanceFromBottom >= 100)
    }

    useEffect(() => {
        if (isUserNearBottom.current) {
            scrollToBottom()
        }
    }, [messages, streamingMessage, toolCalls])



    // Handle file upload to backend/uploads
    const handleFileUpload = async (event) => {
        const file = event.target.files[0]
        if (!file) return

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            })
            const data = await response.json()

            setUploadedFiles(prev => [...prev, {
                ...data,
                preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
            }])
        } catch (error) {
            console.error('Upload failed:', error)
        }
    }

    const removeFile = (index) => {
        setUploadedFiles(prev => prev.filter((_, i) => i !== index))
    }

    /**
     * Handle Message Submission
     * 
     * 1. Constructs the user message object.
     * 2. Sends POST request to /chat.
     * 3. Opens a ReadableStream to process Server-Sent Events (SSE).
     * 4. Updates state based on event type:
     *    - 'thinking': semantic analysis step
     *    - 'tool_call': agent picking a tool (Search, Code)
     *    - 'tool_result': output of that tool
     *    - 'response': final answer text (streamed)
     *    - 'error': error handling (e.g. rate limits)
     */
    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!input.trim() && uploadedFiles.length === 0) return

        // Prepend focus mode context
        const trimmedInput = input.trim()
        let finalMessage = trimmedInput
        if (focusMode === 'chat') {
            finalMessage = `[Mode: Chat] ${trimmedInput}`
        } else if (focusMode === 'web') {
            finalMessage = `[Mode: Web] ${trimmedInput}`
        }

        const userMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: trimmedInput, // Show original trimmed input to user
            files: uploadedFiles
        }

        onAddMessage(userMessage)
        setInput('')
        setUploadedFiles([]) // Clear files immediately
        setIsLoading(true)
        setToolCalls([])
        setStreamingMessage('')

        let accumulatedToolCalls = [] // Local tracking for closure scope

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: finalMessage,
                    conversation_id: conversationId,
                    model: selectedModel,
                    files: uploadedFiles.map(f => ({
                        name: f.original_name,
                        path: f.path,
                        type: f.type
                    }))
                })
            })

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let currentConvId = conversationId

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const text = decoder.decode(value)
                const lines = text.split('\n').filter(line => line.startsWith('data: '))

                for (const line of lines) {
                    try {
                        const data = JSON.parse(line.slice(6))

                        if (data.type === 'thinking') {
                            // Helper to avoid duplicate thinking blocks
                            const updateThinking = calls => {
                                if (calls.some(t => t.tool === 'thinking')) return calls
                                return [...calls, {
                                    tool: 'thinking',
                                    status: 'running',
                                    input: { query: 'Analyzing request...' }
                                }]
                            }
                            setToolCalls(prev => updateThinking(prev))
                            accumulatedToolCalls = updateThinking(accumulatedToolCalls)

                        } else if (data.type === 'tool_call') {
                            const newCall = {
                                tool: data.metadata?.tool,
                                input: data.metadata?.input,
                                status: 'running'
                            }
                            setToolCalls(prev => [...prev, newCall])
                            accumulatedToolCalls.push(newCall)

                        } else if (data.type === 'tool_result') {
                            const updateResult = calls => calls.map((tc, i) =>
                                i === calls.length - 1
                                    ? { ...tc, status: 'complete', result: data.content, duration: data.metadata?.duration_ms }
                                    : tc
                            )
                            setToolCalls(prev => updateResult(prev))
                            accumulatedToolCalls = updateResult(accumulatedToolCalls)

                        } else if (data.type === 'response') {
                            // Complete any hanging thinking state
                            const completeThinking = calls => calls.map(tc =>
                                tc.tool === 'thinking' && tc.status === 'running'
                                    ? { ...tc, status: 'complete', result: 'Analysis complete' }
                                    : tc
                            )
                            setToolCalls(prev => completeThinking(prev))
                            accumulatedToolCalls = completeThinking(accumulatedToolCalls)

                            // Implement Typing Effect for aesthetic smoothness
                            setStreamingMessage('')
                            const fullContent = data.content
                            let currentText = ''
                            setStreamingMessage(' ') // Initialize bubble

                            const typeChar = (index) => {
                                // If user switches tabs (document hidden), finish immediately
                                if (document.hidden) {
                                    setStreamingMessage('')
                                    onAddMessage({
                                        id: Date.now().toString(),
                                        role: 'assistant',
                                        content: fullContent,
                                        toolCalls: accumulatedToolCalls,
                                        model: selectedModel
                                    })
                                    return
                                }

                                if (index < fullContent.length) {
                                    currentText += fullContent[index]
                                    setStreamingMessage(currentText)
                                    // Dynamic speed: Faster for longer blocks
                                    const delay = fullContent.length > 500 ? 1 : 5
                                    setTimeout(() => typeChar(index + 1), delay)
                                } else {
                                    // Done typing
                                    setStreamingMessage('')
                                    onAddMessage({
                                        id: Date.now().toString(),
                                        role: 'assistant',
                                        content: fullContent,
                                        toolCalls: accumulatedToolCalls,
                                        model: selectedModel // Pass model info
                                    })
                                }
                            }
                            typeChar(0)
                        } else if (data.type === 'error') {
                            const errorMsg = data.content || 'An unknown error occurred.'
                            const rateLimitMatch = errorMsg.match(/Please wait (\d+\.?\d*)s before trying again/)

                            if (rateLimitMatch) {
                                const waitTimeCurrent = Math.ceil(parseFloat(rateLimitMatch[1]))

                                onAddMessage({
                                    id: Date.now().toString(),
                                    role: 'assistant',
                                    content: `Rate Limit Hit. Please wait ${waitTimeCurrent}s.`,
                                    isRateLimit: true,
                                    retryAfter: waitTimeCurrent
                                })
                            } else {
                                onAddMessage({
                                    id: Date.now().toString(),
                                    role: 'assistant',
                                    content: `Error: ${errorMsg}`,
                                    isError: true
                                })
                            }
                        } else if (data.type === 'done') {
                            currentConvId = data.conversation_id
                            if (!conversationId && currentConvId) {
                                onConversationUpdate(currentConvId)
                            }
                        }
                    } catch (e) {
                        // Skip invalid JSON
                    }
                }
            }
        } catch (error) {
            console.error('Chat error:', error)
            onAddMessage({
                id: Date.now().toString(),
                role: 'assistant',
                content: 'Sorry, there was an error processing your request. Please try again.',
                isError: true
            })
        } finally {
            setIsLoading(false)
        }
    }

    const renderInputArea = (centered) => (
        <InputArea
            centered={centered}
            input={input}
            setInput={setInput}
            handleSubmit={handleSubmit}
            uploadedFiles={uploadedFiles}
            removeFile={removeFile}
            fileInputRef={fileInputRef}
            handleFileUpload={handleFileUpload}
            isLoading={isLoading}
            showFocusMenu={showFocusMenu}
            setShowFocusMenu={setShowFocusMenu}
            focusMode={focusMode}
            setFocusMode={setFocusMode}
            FOCUS_MODES={FOCUS_MODES}
        />
    )

    return (
        <div className="h-full flex flex-col relative bg-pplx-dark overflow-hidden">
            {/* Messages area */}
            <div
                ref={scrollContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto"
            >
                {messages.length === 0 && !isLoading ? (
                    <HeroSection
                        setInput={setInput}
                        setFocusMode={setFocusMode}
                        FOCUS_MODES={FOCUS_MODES}
                    >
                        {renderInputArea(true)}
                    </HeroSection>
                ) : (
                    <div className="p-4 lg:p-6 pb-24 space-y-6 max-w-4xl mx-auto w-full">
                        {messages.map((message) => (
                            <MessageBubble key={message.id} message={message} />
                        ))}

                        {/* Loading/Streaming State */}
                        {(isLoading || streamingMessage) && !messages.find(m => m.id === 'streaming') && (
                            <MessageBubble
                                key="streaming"
                                message={{
                                    role: 'assistant',
                                    content: streamingMessage || '',
                                    toolCalls: toolCalls.length > 0 ? toolCalls : (isLoading ? [{ tool: 'thinking', status: 'running' }] : [])
                                }}
                            />
                        )}

                        <div ref={messagesEndRef} className="h-64" />
                    </div>
                )}
            </div>

            {/* Scroll to Bottom Button */}
            {showScrollButton && (
                <button
                    onClick={scrollToBottom}
                    className="absolute bottom-48 left-1/2 -translate-x-1/2 bg-pplx-card border border-white/10 p-2 rounded-full shadow-lg hover:bg-white/10 transition-all animate-fade-in z-20"
                >
                    <ArrowDown className="w-5 h-5 text-slate-300" />
                </button>
            )}

            {/* Fixed input area (only shows when messages exist) */}
            {(messages.length > 0 || isLoading) && (
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-pplx-dark via-pplx-dark/95 to-transparent z-10">
                    <div className="max-w-4xl mx-auto">
                        {renderInputArea(false)}
                        <div className="text-center mt-3 space-y-1">
                            <p className="text-sm text-pplx-muted">
                                Planck AI can make mistakes. Verify important information.
                            </p>
                            <p className="text-xs text-pplx-muted/50">
                                © Planck AI 2025
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}