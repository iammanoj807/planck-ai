import { useRef } from 'react'
import { Sparkles, ExternalLink } from 'lucide-react'

export default function HeroSection({
    setInput,
    setFocusMode,
    FOCUS_MODES,
    children
}) {
    return (
        <div className="h-full flex flex-col items-center justify-center px-4 relative pb-32">

            {/* Featured Project Floating Badge (Responsive) */}
            <a
                href="https://huggingface.co/spaces/manojthapaa/NeuroArc"
                target="_blank"
                rel="noopener noreferrer"
                className="absolute right-6 top-4 sm:right-12 sm:top-8 md:right-20 md:top-10 lg:right-32 lg:top-12 flex items-center gap-3 px-3 py-2 md:px-4 md:py-3 rounded-2xl bg-zinc-900/40 border border-violet-500/30 hover:border-violet-500/60 hover:bg-zinc-900/60 transition-all duration-300 group backdrop-blur-md animate-fade-in-left shadow-[0_0_15px_-3px_rgba(139,92,246,0.2)] origin-top-right max-w-[calc(100vw-3rem)] sm:max-w-none"
            >
                <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center group-hover:bg-violet-500/20 transition-colors shrink-0">
                    <img src="/neuroarc.svg" alt="" className="w-6 h-6 opacity-90" />
                </div>
                <div className="flex flex-col gap-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-white group-hover:text-violet-200 transition-colors">NeuroArc</span>
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500 text-white tracking-wide">NEW</span>
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-violet-500 text-white tracking-wide">FREE</span>
                        <span className="text-[10px] text-zinc-500 ml-1 hidden sm:inline">• By Planck AI Creator</span>
                        <ExternalLink className="w-3 h-3 text-zinc-500 group-hover:text-violet-400 transition-colors ml-auto sm:ml-2" />
                    </div>
                    <div className="text-[13px] text-zinc-400 group-hover:text-zinc-300 truncate">
                        ATS-Friendly Job & CV Assistant
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                        <span className="text-[11px] font-medium text-violet-400/90 group-hover:text-violet-300 whitespace-nowrap">Search Jobs</span>
                        <span className="text-[11px] text-zinc-600">→</span>
                        <span className="text-[11px] font-medium text-violet-400/90 group-hover:text-violet-300 whitespace-nowrap">Match CV</span>
                        <span className="text-[11px] text-zinc-600">→</span>
                        <span className="text-[11px] font-medium text-violet-400/90 group-hover:text-violet-300 whitespace-nowrap">Tailor</span>
                        <span className="text-[11px] text-zinc-600">→</span>
                        <span className="text-[11px] font-bold text-violet-400 group-hover:text-violet-200 whitespace-nowrap">Apply</span>
                    </div>
                </div>
            </a>

            <div className="mb-12 flex flex-col items-center text-center">
                <div className="mb-6 hidden md:block">
                    <span className="text-xl font-medium text-pplx-text tracking-wider uppercase">Planck <span className="text-pplx-accent">AI</span></span>
                </div>

                <h1 className="text-4xl md:text-6xl font-serif font-light text-pplx-text tracking-tight animate-fade-in-up">
                    Where knowledge begins
                </h1>
            </div>

            {/* Input Area passed as child to avoid prop drilling */}
            {children}

            {/* Disclaimer */}
            <div className="absolute bottom-6 left-0 right-0 text-center space-y-2 animate-fade-in px-6">
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
