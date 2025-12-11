import { Menu, Sparkles } from 'lucide-react'

export default function Header({ onToggleSidebar, onNewChat }) {
    return (
        <header className="bg-pplx-dark px-4 py-3 flex items-center justify-between sticky top-0 z-50">
            {/* Left section */}
            <div className="flex items-center gap-4">
                <button
                    onClick={onToggleSidebar}
                    className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors lg:hidden"
                >
                    <Menu className="w-5 h-5 text-slate-300" />
                </button>

                <div className="flex items-center gap-3 lg:hidden">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-pplx-accent flex items-center justify-center">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-serif font-medium text-pplx-text tracking-wide">Planck <span className="text-pplx-accent">AI</span></h1>
                        <p className="text-xs text-pplx-muted">Autonomous Reasoning Engine</p>
                    </div>
                </div>
            </div>

        </header>
    )
}
