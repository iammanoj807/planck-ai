import { useRef } from 'react'
import { Sparkles } from 'lucide-react'

export default function HeroSection({
    setInput,
    setFocusMode,
    FOCUS_MODES,
    children
}) {
    return (
        <div className="h-full flex flex-col items-center justify-center px-4 relative pb-32">
            <div className="mb-12 flex flex-col items-center text-center">
                <div className="mb-4 hidden md:block">
                    <span className="text-xl font-medium text-pplx-text tracking-wider uppercase">Planck <span className="text-pplx-accent">AI</span></span>
                </div>
                <h1 className="text-4xl md:text-6xl font-serif font-light text-pplx-text tracking-tight animate-fade-in-up">
                    Where knowledge begins
                </h1>
            </div>

            {/* Input Area passed as child to avoid prop drilling */}
            {children}




            {/* Disclaimer */}
            <div className="absolute bottom-6 left-0 right-0 text-center space-y-2 animate-fade-in">
                <p className="text-sm text-pplx-muted">
                    Planck AI can make mistakes. Verify important information.
                </p>
                <p className="text-xs text-pplx-muted/50">
                    © Planck AI 2025
                </p>
            </div>
        </div>
    )
}
