import { Menu, Sparkles } from 'lucide-react'

const LANGUAGES = [
    { code: 'English', flag: '🇺🇸', label: 'English' },
    { code: 'Nepali', flag: '🇳🇵', label: 'Nepali' },
    { code: 'Hindi', flag: '🇮🇳', label: 'Hindi' },
    { code: 'Mandarin', flag: '🇨🇳', label: 'Mandarin' },
    { code: 'Spanish', flag: '🇪🇸', label: 'Spanish' },
    { code: 'French', flag: '🇫🇷', label: 'French' },
    { code: 'Arabic', flag: '🇸🇦', label: 'Arabic' },
    { code: 'Bengali', flag: '🇧🇩', label: 'Bengali' },
    { code: 'Russian', flag: '🇷🇺', label: 'Russian' },
    { code: 'Portuguese', flag: '🇵🇹', label: 'Portuguese' },
    { code: 'Indonesian', flag: '🇮🇩', label: 'Indonesian' },
    { code: 'Urdu', flag: '🇵🇰', label: 'Urdu' },
    { code: 'German', flag: '🇩🇪', label: 'German' },
    { code: 'Japanese', flag: '🇯🇵', label: 'Japanese' },
    { code: 'Swahili', flag: '🇰🇪', label: 'Swahili' },
    { code: 'Turkish', flag: '🇹🇷', label: 'Turkish' },
    { code: 'Korean', flag: '🇰🇷', label: 'Korean' },
    { code: 'Vietnamese', flag: '🇻🇳', label: 'Vietnamese' },
    { code: 'Italian', flag: '🇮🇹', label: 'Italian' },
    { code: 'Thai', flag: '🇹🇭', label: 'Thai' },
]

export default function Header({ onToggleSidebar, onNewChat, currentLanguage = 'English', onLanguageChange }) {
    const currentLangObj = LANGUAGES.find(l => l.code === currentLanguage) || LANGUAGES[0]

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

            {/* Right section - Language Selector */}
            <div className="flex items-center gap-2">
                <div className="relative group">
                    <button className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-pplx-card hover:bg-white/10 transition-colors border border-white/5">
                        <span className="text-xl">
                            {currentLangObj.flag}
                        </span>
                        <span className="text-sm font-medium text-pplx-text hidden sm:block">
                            {currentLangObj.label}
                        </span>
                    </button>

                    {/* Dropdown - Using pt-2 instead of mt-2 to maintain hover bridge */}
                    <div className="absolute right-0 top-full pt-2 w-64 hidden group-hover:block transition-all z-50">
                        <div className="bg-zinc-950 border border-white/10 rounded-xl shadow-xl overflow-hidden">
                            <div className="px-4 py-3 border-b border-white/10 bg-zinc-900/50">
                                <p className="text-[10px] text-gray-400 leading-tight">
                                    Language changes apply to new messages.
                                </p>
                            </div>
                            <div className="max-h-80 overflow-y-auto py-1 custom-scrollbar">
                                {LANGUAGES.map((lang) => (
                                    <button
                                        key={lang.code}
                                        onClick={() => onLanguageChange(lang.code)}
                                        className={`w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 flex items-center justify-between group/item ${currentLanguage === lang.code ? 'bg-white/5' : ''}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <span className="text-lg">{lang.flag}</span>
                                            <span className={`font-medium ${currentLanguage === lang.code ? 'text-pplx-accent' : 'text-pplx-text group-hover/item:text-gray-200'}`}>
                                                {lang.label}
                                            </span>
                                        </div>
                                        {currentLanguage === lang.code && <Sparkles className="w-3 h-3 text-pplx-accent" />}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </header>
    )
}
